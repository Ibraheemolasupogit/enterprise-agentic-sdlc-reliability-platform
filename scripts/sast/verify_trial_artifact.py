#!/usr/bin/env python3
"""Verify a retained C5 trial archive using independent GitHub and Git evidence."""

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import zipfile
import zlib


OWNER = "Ibraheemolasupogit"
OWNER_ID = 181765037
REPOSITORY = f"{OWNER}/enterprise-agentic-sdlc-reliability-platform"
REPOSITORY_ID = 1439889276
REF = "refs/heads/main"
EVENT = "workflow_dispatch"
WORKFLOW = ".github/workflows/c5-sast-hosted-trial.yml"
TRUST_CONFIG = "security/sast/trusted-inputs.json"
DOCKERFILE = "security/sast/container/Dockerfile"
TOOLCHAIN = "security/sast/toolchain.json"
BASE_IMAGE = "ubuntu@sha256:77eb101c607d6e3d4f5ad0c8a02c2136c689b98aba1f359e6502ba517e5c57ec"
HARDENING = [
    "--rm", "--platform", "linux/amd64", "--pull", "never", "--network", "none", "--user", "1001:1001",
    "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true", "--ipc", "none",
    "--pids-limit", "512", "--memory", "3g", "--memory-swap", "3g", "--cpus", "2",
    "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=512m", "--workdir", "/repo",
]
INPUTS = frozenset({
    "scripts/sast/feasibility.py", "scripts/sast/hosted_trial.py", TOOLCHAIN,
    "security/sast/controls.json", "security/sast/rules/typescript.yml", "security/sast/rules/python.yml",
    "requirements-sast-linux.txt", DOCKERFILE, WORKFLOW, "scripts/sast/ts_syntax_gate.mjs",
    "security/sast/typescript-gate.json",
})
SCHEMAS = {
    "hosted-runner-facts.json": "c5-f4-runner-facts/1",
    "container-image.json": "c5-f4r-container-image/1",
    "container-install.json": "c5-f4r-container-install/1",
    "container-run.json": "c5-f4r-container-run/1",
    "hosted-trial.json": "c5-f4-hosted-trial/2",
    "c5-summary.json": "c5-summary/2",
}
HISTORICAL_COMMIT = "2e0bd258a6b217572e86355a460d86dc5b479ce2"
HISTORICAL_RUN_ID = 44393309563
HISTORICAL_DIGEST = "388dc3baca1ba774e1a708514791aed36b45fca9d10ce0928af60c4cdf4e0cf8"
SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
MAX_ARCHIVE = 4 << 20
MAX_JSON = 1 << 20


class Rejected(Exception):
    """Evidence could not establish the requested verification result."""


def require(condition, message):
    if not condition:
        raise Rejected(message)


def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def expected_fields(record, expected, label):
    """Check shared fields without allowing JSON booleans to stand in for numbers."""
    require(isinstance(record, dict), f"{label} must be a JSON object")
    for key, value in expected.items():
        actual = record.get(key)
        require(type(actual) is type(value) and actual == value, f"{label} has invalid {key}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject_constant(_):
    raise Rejected("non-finite JSON number")


def finite_float(value):
    number = float(value)
    require(math.isfinite(number), "non-finite JSON number")
    return number


def json_object(data, label):
    try:
        record = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                            parse_constant=reject_constant, parse_float=finite_float)
    except (ValueError, RecursionError, Rejected) as exc:
        raise Rejected(f"{label} is malformed JSON") from exc
    require(isinstance(record, dict), f"{label} must be a JSON object")
    return record


def bounded_read(path, maximum, label):
    require(path.is_file(), f"{label} is missing or irregular")
    with path.open("rb") as handle:
        data = handle.read(maximum + 1)
    require(len(data) <= maximum, f"{label} is too large")
    return data


def read_archive(path, expected_digest):
    data = bounded_read(path, MAX_ARCHIVE, "archive")
    require(hashlib.sha256(data).hexdigest() == expected_digest, "archive SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        require(len(members) == len(SCHEMAS), "archive must contain exactly six JSON files")
        records = {}
        for member in members:
            name = member.orig_filename
            file_type = stat.S_IFMT(member.external_attr >> 16)
            require(name in SCHEMAS and name == member.filename and name not in records,
                    "archive has an unexpected, unsafe or duplicate path")
            require(file_type in (0, stat.S_IFREG) and not member.external_attr & 0x10
                    and not member.flag_bits & 1 and 0 < member.file_size <= MAX_JSON,
                    "archive has an irregular, encrypted or oversized member")
            require(member.compress_type in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED),
                    "archive uses an unsupported compression method")
            with archive.open(member) as handle:
                payload = handle.read(MAX_JSON + 1)
            require(len(payload) == member.file_size, "archive member length mismatch")
            record = json_object(payload, name)
            expected_fields(record, {"schema": SCHEMAS[name]}, name)
            records[name] = record
    return records


def git(repo, *arguments):
    # Resolve evidence from the supplied object's repository, free of inherited Git overrides.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_GRAFT_FILE=os.devnull, GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(["git", "-C", str(repo), *arguments], env=env, capture_output=True, timeout=15)
    require(result.returncode == 0, f"independent Git evidence failed {arguments[0]}")
    return result.stdout


def require_commit(repo, revision):
    require(matches(COMMIT, revision), "Git evidence requires a full lowercase commit ID")
    require(git(repo, "cat-file", "-t", revision) == b"commit\n", "Git object is not a commit")


def git_blob(repo, revision, path):
    entry = git(repo, "ls-tree", "-l", revision, "--", path).decode("ascii").rstrip("\n")
    match = re.fullmatch(r"100(?:644|755) blob [0-9a-f]{40}\s+(\d+)\t" + re.escape(path), entry)
    require(match is not None and int(match[1]) <= MAX_JSON, f"missing or irregular Git input {path}")
    return git(repo, "cat-file", "blob", f"{revision}:{path}")


def approved_inputs(manifest, repo, revision, main_tip, historical):
    if historical:
        baseline = HISTORICAL_COMMIT
        require(revision == baseline, "historical Run 1 requires its exact checkout commit")
    else:
        require(set(manifest) == {"schema", "baseline_commit", "inputs", "trusted_inputs_sha256"}
                and manifest["schema"] == "c5-approved-trial-inputs/1", "invalid approval manifest schema")
        baseline = manifest["baseline_commit"]
    for commit in (baseline, revision, main_tip):
        require_commit(repo, commit)
    git(repo, "merge-base", "--is-ancestor", baseline, revision)
    git(repo, "merge-base", "--is-ancestor", revision, main_tip)
    approved = {path: hashlib.sha256(git_blob(repo, baseline, path)).hexdigest() for path in sorted(INPUTS)}
    if not historical:
        require(manifest["inputs"] == approved, "manifest input set or hashes differ from approved baseline")
        trust_data = git_blob(repo, baseline, TRUST_CONFIG)
        require(hashlib.sha256(trust_data).hexdigest() == manifest["trusted_inputs_sha256"],
                "manifest P1 trust-config digest differs from approved baseline")
        require(trust_data == git_blob(repo, revision, TRUST_CONFIG), "run commit changed P1 trust configuration")
        expected_fields(json_object(trust_data, "P1 trust configuration"), {
            "schema": "c5-trusted-inputs/1", "repository_id": REPOSITORY_ID, "repository_owner_id": OWNER_ID,
            "ref": REF, "events": [EVENT], "require_private": True,
        }, "P1 trust configuration")
    if revision != baseline:
        for path, digest in approved.items():
            require(hashlib.sha256(git_blob(repo, revision, path)).hexdigest() == digest,
                    f"run commit changed approved input {path}")
    return approved


def recorded_inputs(lines):
    require(isinstance(lines, list) and len(lines) == len(INPUTS), "invalid recorded input hash count")
    result = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line) if isinstance(line, str) else None
        require(match is not None and match[2] in INPUTS and match[2] not in result,
                "invalid, unexpected or duplicate recorded input")
        result[match[2]] = match[1]
    return result


def trusted_execution(facts, run_metadata, historical):
    github = facts.get("github")
    expected_fields(github, {
        "GITHUB_REF": REF, "GITHUB_EVENT_NAME": EVENT, "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW}@{REF}",
        "RUNNER_ENVIRONMENT": "github-hosted", "RUNNER_OS": "Linux", "RUNNER_ARCH": "X64",
    }, "runner GitHub context")
    revision = github.get("GITHUB_SHA")
    require(matches(COMMIT, revision), "runner context has an invalid commit")
    if historical:
        run_id, attempt = HISTORICAL_RUN_ID, 1
    else:
        run_id, attempt = run_metadata.get("id"), run_metadata.get("run_attempt")
        require(all(type(value) is int and value > 0 for value in (run_id, attempt)),
                "GitHub run metadata has an invalid ID or attempt")
        expected_fields(run_metadata, {
            "head_sha": revision, "head_branch": "main", "event": EVENT, "status": "completed",
            "conclusion": "success",
        }, "GitHub run metadata")
        require(run_metadata.get("path") in (WORKFLOW, f"{WORKFLOW}@main", f"{WORKFLOW}@{REF}"),
                "GitHub run used an unexpected workflow")
        for key in ("actor", "triggering_actor"):
            expected_fields(run_metadata.get(key), {"id": OWNER_ID, "login": OWNER}, f"GitHub {key}")
        for key in ("repository", "head_repository"):
            repository = run_metadata.get(key)
            expected_fields(repository, {
                "id": REPOSITORY_ID, "full_name": REPOSITORY, "private": True, "fork": False,
            }, f"GitHub {key}")
            expected_fields(repository.get("owner"), {"id": OWNER_ID, "login": OWNER}, f"GitHub {key} owner")
    expected_fields(github, {"GITHUB_RUN_ID": str(run_id), "GITHUB_RUN_ATTEMPT": str(attempt)}, "runner GitHub context")
    require(matches(re.compile(r"[A-Za-z0-9._:/ -]{8,80}"), facts.get("authorization_reference")),
            "runner facts lack a valid authorization reference")
    return revision, run_id, attempt


def verify_records(records, inputs, engine, historical):
    trial = records["hosted-trial.json"]
    summary = records["c5-summary.json"]
    image = records["container-image.json"]
    install = records["container-install.json"]
    run = records["container-run.json"]
    for name, record in (("image", image), ("install", install), ("run", run)):
        expected_fields(record, {"exit": 0, "result": "clean"}, f"container {name}")
        require("reason" not in record, f"container {name} contains a contradictory failure reason")
        if historical:
            require("trusted_input" not in record, "historical evidence unexpectedly contains a P1 decision")
        else:
            decision = {
                "mode": "hosted", "trusted": True, "event": EVENT, "ref": REF,
                "repository_id": REPOSITORY_ID, "actor_id": OWNER_ID,
            }
            expected_fields(record.get("trusted_input"), decision, f"container {name} P1 decision")
            require(set(record["trusted_input"]) == set(decision), f"container {name} P1 decision has unexpected fields")
    expected_fields(image, {
        "status": "built", "architecture": "amd64", "user": "1001:1001",
        "dockerfile_sha256": inputs[DOCKERFILE], "base_image": BASE_IMAGE,
    }, "container image")
    require(matches(re.compile(r"sha256:[0-9a-f]{64}"), image.get("image_id")), "invalid container image ID")
    expected_fields(install, {"hardening": HARDENING}, "container install")
    expected_fields(run, {"hardening": HARDENING}, "container run")
    stages = install.get("stages")
    require(isinstance(stages, dict) and set(stages) == {"venv", "pip-install", "pip-check"},
            "container install stages missing or unexpected")
    for stage, result in stages.items():
        expected_fields(result, {"exit": 0}, f"install stage {stage}")
    nonce = trial.get("nonce")
    require(matches(re.compile(r"[0-9a-f]{32}"), nonce), "missing or malformed run nonce")
    expected_fields(run, {"nonce": nonce, "docker_exit": 0}, "container run")
    expected_fields(run.get("typescript_gate"), {"exit": 0}, "host TypeScript gate")
    expected_fields(trial, {"harness_exit": 0, "result": "clean", "non_blocking": True,
                            "isolation_requested": "container"}, "hosted trial")
    require(recorded_inputs(trial.get("input_sha256sum")) == inputs, "recorded input hashes differ from approval")
    expected_fields(summary, {"exit": 0, "result": "clean", "engine": "semgrep-ce",
                              "isolation_mode": "container", "version": engine["version"],
                              "semgrep_core_sha256": engine["platforms"]["Linux-x86_64"]["semgrep_core_sha256"]},
                    "harness summary")
    expected_fields(summary.get("source"), {"exit": 0, "status": "clean", "findings": []}, "source scan")
    expected_fields(summary.get("typescript_syntax_gate"), {
        "status": "pass", "mode": "host-attestation", "gate_sha256": inputs["scripts/sast/ts_syntax_gate.mjs"],
    }, "harness TypeScript gate")
    expected_fields(summary.get("rules_sha256"), {path: inputs[path] for path in INPUTS if path.startswith("security/sast/rules/")},
                    "harness rules")
    expected_fields(summary.get("controls"), {"status": "pass", "failed_cases": 0,
                    "catalogue_sha256": inputs["security/sast/controls.json"]}, "harness controls")
    expected_fields(summary.get("toolchain"), {"pip_check": "pass", "lock": "requirements-sast-linux.txt"},
                    "harness toolchain")
    expected_fields(trial.get("summary"), {key: summary[key] for key in
                    ("result", "isolation_mode", "isolation", "toolchain", "typescript_syntax_gate")},
                    "embedded harness summary")
    source_keys = ("status", "targets", "findings", "wall_seconds", "max_memory_bytes", "total_bytes")
    expected_fields(trial["summary"].get("source"), {key: summary["source"][key] for key in source_keys},
                    "embedded source scan")
    controls_keys = ("status", "fixtures", "failed_cases", "seconds", "parser_gap_drift", "unexpected_findings")
    expected_fields(trial["summary"].get("controls"), {key: summary["controls"][key] for key in controls_keys},
                    "embedded controls")


def verify(archive, expected_digest, repo, main_tip, manifest_path=None, run_metadata_path=None, historical=False):
    require(isinstance(expected_digest, str), "an independent archive SHA-256 is required")
    digest = expected_digest.removeprefix("sha256:")
    require(matches(SHA256, digest), "invalid expected archive SHA-256")
    if historical:
        require(digest == HISTORICAL_DIGEST and manifest_path is None and run_metadata_path is None,
                "historical mode is limited to the original Run 1 archive")
        manifest = run_metadata = None
    else:
        require(manifest_path is not None and run_metadata_path is not None,
                "P3 requires an approved manifest and independent GitHub run-attempt metadata")
        manifest = json_object(bounded_read(manifest_path, MAX_JSON, "approval manifest"), "approval manifest")
        run_metadata = json_object(bounded_read(run_metadata_path, MAX_JSON, "GitHub run metadata"), "GitHub run metadata")
    records = read_archive(archive, digest)
    facts = records["hosted-runner-facts.json"]
    revision, run_id, attempt = trusted_execution(facts, run_metadata, historical)
    expected_fields(records["hosted-trial.json"].get("facts"), {
        "schema": facts["schema"], "github": facts["github"], "authorization_reference": facts["authorization_reference"],
    }, "container runner facts")
    inputs = approved_inputs(manifest, repo, revision, main_tip, historical)
    toolchain = json_object(git_blob(repo, revision, TOOLCHAIN), "approved toolchain")
    verify_records(records, inputs, toolchain["engine"], historical)
    return run_id, attempt, revision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="original GitHub artifact ZIP")
    parser.add_argument("--expected-digest", required=True, help="SHA-256 obtained separately from GitHub")
    parser.add_argument("--git-repo", required=True, type=Path, help="independently obtained Git checkout")
    parser.add_argument("--main-tip", required=True, help="independently obtained GitHub main commit ID")
    parser.add_argument("--manifest", type=Path, help="owner-reviewed approval manifest from outside the artifact")
    parser.add_argument("--run-metadata", type=Path, help="independent GitHub REST run-attempt JSON")
    parser.add_argument("--historical-run-1", action="store_true", help="verify Run 1 evidence integrity only")
    args = parser.parse_args()
    try:
        run_id, attempt, revision = verify(args.archive, args.expected_digest, args.git_repo, args.main_tip,
                                           args.manifest, args.run_metadata, args.historical_run_1)
    except Rejected as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile, zlib.error,
            subprocess.SubprocessError, RuntimeError) as exc:
        print(f"Verification failed: unreadable or malformed evidence ({type(exc).__name__})", file=sys.stderr)
        return 1
    if args.historical_run_1:
        print(f"Historical integrity verified for run {run_id}/{attempt} at {revision}. "
              "Run 1 predates P1. Current trust policy was not evaluated.")
    else:
        print(f"P3 trust policy passed for run {run_id}/{attempt} at {revision}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
