#!/usr/bin/env python3
"""Verify the pinned repository's hosted SAST governance using read-only GitHub GETs."""

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
from http.client import HTTPException
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[2]
OWNER = "Ibraheemolasupogit"
OWNER_ID = 181765037
REPOSITORY = f"{OWNER}/enterprise-agentic-sdlc-reliability-platform"
REPOSITORY_ID = 1439889276
MAIN_REF = "refs/heads/main"
EVENT = "workflow_dispatch"
WORKFLOW = ".github/workflows/c5-sast-hosted-trial.yml"
DRIVER = "scripts/sast/hosted_trial.py"
TRUST_CONFIG = "security/sast/trusted-inputs.json"
MANIFEST = "security/sast/approved-trial-inputs.json"
API = "https://api.github.com"
REPO_PATH = f"/repos/{REPOSITORY}"
API_VERSION = "2026-03-10"
TOKEN_ENV = "P4_GITHUB_TOKEN"
LIST_QUERY = "per_page=100&page=1"
MAX_RESPONSE = 512 << 10
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_SHA = re.compile(r"[0-9a-f]{40}")
OWNER_IDENTITY = {"id": OWNER_ID, "login": OWNER, "type": "User"}


class Rejected(Exception):
    """The available evidence cannot establish a safe governance configuration."""


def require(condition, message):
    if not condition:
        raise Rejected(message)


def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def fields(record, expected, label):
    require(isinstance(record, dict), f"{label} must be a JSON object")
    for name, value in expected.items():
        actual = record.get(name)
        require(type(actual) is type(value) and actual == value, f"{label} has invalid {name}")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject_constant(_):
    raise Rejected("non-finite JSON number")


def finite_float(value):
    result = float(value)
    require(math.isfinite(result), "non-finite JSON number")
    return result


def decode_json(payload, label):
    require(0 < len(payload) <= MAX_RESPONSE, f"{label} has an empty or oversized response")
    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=unique_keys,
                          parse_constant=reject_constant, parse_float=finite_float)
    except (ValueError, Rejected, RecursionError) as exc:
        raise Rejected(f"{label} has malformed JSON") from exc


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHubReadClient:
    def __init__(self, token):
        require(isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,512}", token),
                f"missing or invalid {TOKEN_ENV}")
        self.token = token
        self.opener = build_opener(NoRedirects())

    def get(self, path, label, *, complete_list=False):
        request = Request(f"{API}{REPO_PATH}{path}", method="GET", headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "morrow-supply-p4-governance-check",
            "X-GitHub-Api-Version": API_VERSION,
        })
        try:
            with self.opener.open(request, timeout=15) as response:
                require(response.status == 200, f"{label} returned HTTP {response.status}")
                require(response.headers.get_content_type() in ("application/json", "application/vnd.github+json"),
                        f"{label} did not return JSON")
                if complete_list:
                    # Safe results fit on page one. A Link header means completeness is unverified.
                    require("Link" not in response.headers, f"{label} returned pagination")
                payload = response.read(MAX_RESPONSE + 1)
        except HTTPError as exc:
            code = exc.code
            exc.close()
            detail = "authentication, access or service limit unverified" if code in (401, 403, 404, 429) else "request failed"
            raise Rejected(f"{label} returned HTTP {code} ({detail})") from None
        except (URLError, OSError, HTTPException):
            raise Rejected(f"{label} could not be read from GitHub") from None
        return decode_json(payload, label)


def local_file(root, relative):
    path = root / relative
    require(not path.is_symlink() and path.is_file(), f"missing or irregular local {relative}")
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_RESPONSE + 1)
    except OSError:
        raise Rejected(f"local {relative} could not be read") from None
    require(0 < len(data) <= MAX_RESPONSE, f"local {relative} is empty or oversized")
    return data


def approved_bindings(root):
    manifest = decode_json(local_file(root, MANIFEST), "local P3 manifest")
    fields(manifest, {"schema": "c5-approved-trial-inputs/1"}, "local P3 manifest")
    require(matches(GIT_SHA, manifest.get("baseline_commit")), "local P3 manifest has an invalid baseline")
    inputs = manifest.get("inputs")
    require(isinstance(inputs, dict) and len(inputs) == 11 and all(matches(SHA256, v) for v in inputs.values()),
            "local P3 manifest has an invalid input set or digest")
    pins = {
        WORKFLOW: inputs.get(WORKFLOW),
        DRIVER: inputs.get(DRIVER),
        TRUST_CONFIG: manifest.get("trusted_inputs_sha256"),
    }
    for path, digest in pins.items():
        require(matches(SHA256, digest) and hashlib.sha256(local_file(root, path)).hexdigest() == digest,
                f"local {path} differs from the P3 approval")
    fields(decode_json(local_file(root, TRUST_CONFIG), "local P1 trust configuration"), {
        "schema": "c5-trusted-inputs/1", "repository_id": REPOSITORY_ID, "repository_owner_id": OWNER_ID,
        "require_private": True, "events": [EVENT], "ref": MAIN_REF,
    }, "local P1 trust configuration")
    return pins


def main_tip(client):
    ref = client.get("/git/ref/heads/main", "main reference")
    fields(ref, {"ref": MAIN_REF}, "main reference")
    target = ref.get("object")
    fields(target, {"type": "commit"}, "main reference target")
    require(matches(GIT_SHA, target.get("sha")), "main reference has an invalid commit SHA")
    return target["sha"]


def approved_tree_entries(client, tip, paths):
    commit = client.get(f"/git/commits/{tip}", "main commit")
    fields(commit, {"sha": tip}, "main commit")
    tree = commit.get("tree")
    require(isinstance(tree, dict) and matches(GIT_SHA, tree.get("sha")), "main commit has an invalid tree SHA")
    tree_sha = tree["sha"]
    snapshot = client.get(f"/git/trees/{tree_sha}?recursive=1", "main Git tree")
    fields(snapshot, {"sha": tree_sha, "truncated": False}, "main Git tree")
    entries = snapshot.get("tree")
    require(isinstance(entries, list) and all(isinstance(item, dict) for item in entries),
            "main Git tree has an invalid entry list")
    blobs = {}
    for path in paths:
        members = [item for item in entries if item.get("path") == path]
        require(len(members) == 1, f"main Git tree is missing or duplicates {path}")
        entry = members[0]
        fields(entry, {"type": "blob"}, f"main Git tree entry {path}")
        require(entry.get("mode") in ("100644", "100755") and matches(GIT_SHA, entry.get("sha")),
                f"main Git tree entry {path} is not a regular file")
        blobs[path] = entry["sha"]
    return blobs


def verify_file(client, path, tip, expected, tree_blob):
    content = client.get(f"/contents/{path}?ref={tip}", f"approved file {path}")
    fields(content, {"path": path, "name": Path(path).name, "type": "file", "encoding": "base64"},
           f"approved file {path}")
    require(isinstance(content.get("content"), str), f"approved file {path} is missing base64 content")
    try:
        raw = base64.b64decode(content["content"].replace("\n", "").replace("\r", ""), validate=True)
    except (ValueError, binascii.Error):
        raise Rejected(f"approved file {path} has invalid base64 content") from None
    blob_sha = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw, usedforsecurity=False).hexdigest()
    fields(content, {"size": len(raw), "sha": blob_sha}, f"approved file {path}")
    require(blob_sha == tree_blob, f"approved file {path} differs from its main Git tree entry")
    require(hashlib.sha256(raw).hexdigest() == expected, f"approved file {path} changed on main")


def check_governance(client, root=ROOT):
    pins = approved_bindings(root)
    repository = client.get("", "repository")
    fields(repository, {
        "id": REPOSITORY_ID, "full_name": REPOSITORY, "private": True, "visibility": "private",
        "fork": False, "default_branch": "main", "archived": False, "disabled": False,
    }, "repository")
    fields(repository.get("owner"), OWNER_IDENTITY, "repository owner")
    tip = main_tip(client)

    collaborators = client.get(f"/collaborators?affiliation=all&{LIST_QUERY}", "collaborators", complete_list=True)
    require(isinstance(collaborators, list) and len(collaborators) == 1, "collaborator list must contain only the owner")
    fields(collaborators[0], OWNER_IDENTITY, "sole collaborator")
    fields(collaborators[0].get("permissions"), {"admin": True}, "owner collaborator permissions")
    keys = client.get(f"/keys?{LIST_QUERY}", "deploy keys", complete_list=True)
    require(isinstance(keys, list) and not keys, "deploy key inventory must be empty")

    actions = client.get("/actions/permissions", "repository Actions policy")
    fields(actions, {"enabled": True}, "repository Actions policy")
    require(actions.get("allowed_actions") in ("all", "local_only", "selected"),
            "repository Actions policy has an invalid allowed_actions value")
    fork = client.get("/actions/permissions/fork-pr-workflows-private-repos", "fork PR workflow policy")
    fields(fork, {
        "run_workflows_from_fork_pull_requests": False, "send_write_tokens_to_workflows": False,
        "send_secrets_and_variables": False,
    }, "fork PR workflow policy")
    require(type(fork.get("require_approval_for_fork_pr_workflows")) is bool,
            "fork PR workflow policy is missing a Boolean approval setting")
    permissions = client.get("/actions/permissions/workflow", "default workflow token policy")
    fields(permissions, {
        "default_workflow_permissions": "read", "can_approve_pull_request_reviews": False,
    }, "default workflow token policy")

    workflow = client.get(f"/actions/workflows/{Path(WORKFLOW).name}", "trial workflow registration")
    fields(workflow, {"path": WORKFLOW, "state": "active"}, "trial workflow registration")
    workflow_id = workflow.get("id")
    require(type(workflow_id) is int and workflow_id > 0, "trial workflow registration has an invalid ID")
    fields(workflow, {"url": f"{API}{REPO_PATH}/actions/workflows/{workflow_id}"}, "trial workflow registration")
    blobs = approved_tree_entries(client, tip, pins)
    for path, digest in pins.items():
        verify_file(client, path, tip, digest, blobs[path])
    require(main_tip(client) == tip, "main changed during the governance check")
    return {"repository_id": REPOSITORY_ID, "workflow_id": workflow_id, "main_commit": tip}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="read GitHub using the owner-supplied P4_GITHUB_TOKEN")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("use --live to request GitHub governance reads")
    try:
        record = check_governance(GitHubReadClient(os.environ.get(TOKEN_ENV)))
    except Rejected as exc:
        print(f"P4 governance NO-GO: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"result": "pass", "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
