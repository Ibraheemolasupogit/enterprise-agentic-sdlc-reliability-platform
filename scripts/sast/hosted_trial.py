"""C5-F4/F4R hosted SAST trial driver (non-blocking, owner-dispatched only).

Subcommands (all stdlib; run with `python3 -I`; never invokes sudo):
  facts              Record read-only host runner facts before any download.
  container-build    Build the digest-pinned Ubuntu 24.04 runtime image (network for
                     signed APT only), record its package/licence inventory.
  container-install  In a hardened --network none container, create the venv and install
                     the hash-locked wheels offline; `pip check` is fatal.
  container-run      Run the C5-G4 TypeScript syntax gate on the host (pinned compiler; writes a
                     nonce-bound attestation), then in a hardened --network none container run
                     `run --isolation container`; verify the evidence written for this exact run.
  typescript-preflight  Before any image build or container: require the pinned Node (exact
                     .node-version) and run the C5-G4 TypeScript gate on the host (lock-verified
                     compiler); failure stops the job before container launch.
  trust-check        C5 R2(a): fail closed (exit 2) unless the hosted context is an owner-dispatched
                     workflow_dispatch on refs/heads/main of the pinned repository (numeric IDs);
                     typescript-preflight, container-build, container-install and container-run apply
                     the same check before any download, Docker call or Semgrep execution.
  run                Execute the F3 harness, measure it, write allowlisted evidence.
  summarize          Report all evidence to the job summary.

Exit codes: 0 clean, 1 findings, 2 configuration, 3 tool, 4 control,
5 isolation unavailable/insufficient, 6 container build/runtime error,
7 evidence missing or inconsistent. Docker's own codes (125-127, 128+n) never
pass through as harness codes.

Outputs (ignored artifacts/sast/, allowlisted for upload; never raw engine reports).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import resource
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/sast"
FACTS = OUT / "hosted-runner-facts.json"
TRIAL = OUT / "hosted-trial.json"
SUMMARY = OUT / "c5-summary.json"
IMAGE_EVIDENCE = OUT / "container-image.json"
INSTALL_EVIDENCE = OUT / "container-install.json"
RUN_EVIDENCE = OUT / "container-run.json"
HARNESS = ROOT / "scripts/sast/feasibility.py"
CONTAINER_DIR = ROOT / "security/sast/container"
DOCKERFILE = CONTAINER_DIR / "Dockerfile"
LOCK = "requirements-sast-linux.txt"
BASE_IMAGE = "ubuntu@sha256:77eb101c607d6e3d4f5ad0c8a02c2136c689b98aba1f359e6502ba517e5c57ec"
IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
EXIT_NAMES = {0: "clean", 1: "findings", 2: "configuration-error", 3: "tool-error", 4: "control-failure",
              5: "isolation-unavailable", 6: "container-runtime-error", 7: "evidence-missing"}
# Non-secret GitHub/runner metadata only; tokens and arbitrary environment are never read.
CONTEXT_KEYS = ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_REF", "GITHUB_WORKFLOW_REF",
                "GITHUB_EVENT_NAME", "RUNNER_OS", "RUNNER_ARCH", "RUNNER_ENVIRONMENT", "ImageOS", "ImageVersion")
AUTH_PATTERN = re.compile(r"^[A-Za-z0-9._:/ -]{8,80}$")
INPUT_HASHES = ("scripts/sast/feasibility.py", "scripts/sast/hosted_trial.py", "security/sast/toolchain.json",
                "security/sast/controls.json", "security/sast/rules/typescript.yml", "security/sast/rules/python.yml",
                LOCK, "security/sast/container/Dockerfile", ".github/workflows/c5-sast-hosted-trial.yml",
                "scripts/sast/ts_syntax_gate.mjs", "security/sast/typescript-gate.json")
# C5-G4: the scan image has no Node, so the TypeScript syntax gate runs on the host before any container
# starts and writes a nonce-bound attestation that the in-container harness verifies (exact targets, hashes).
TS_GATE_EXITS = (2, 3, 4)
# C5-G4H: on hosted runners the pinned Node comes from actions/setup-node (tool cache), not the image's own node.
NODE_VERSION_FILE = ROOT / "apps/octocat-supply/.node-version"
# Every container this driver starts gets exactly these restrictions.
HARDENING = ("--rm", "--platform", "linux/amd64", "--pull", "never", "--network", "none", "--user", "1001:1001",
             "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges=true", "--ipc", "none",
             "--pids-limit", "512", "--memory", "3g", "--memory-swap", "3g", "--cpus", "2",
             "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=512m", "--workdir", "/repo")
PIP_ENV = ("HOME=/tmp", "PIP_NO_CACHE_DIR=1", "PIP_DISABLE_PIP_VERSION_CHECK=1", "PIP_NO_INPUT=1",
           "PIP_CONFIG_FILE=/dev/null")
# C5 R2(a) P1: trusted-input pins. Hosted driver steps run only for an owner-dispatched workflow_dispatch on
# refs/heads/main of the pinned repository (numeric IDs: names can be reused and a forker owns their fork).
TRUSTED_INPUTS = ROOT / "security/sast/trusted-inputs.json"
TRUSTED_KEYS = {"schema", "purpose", "repository_id", "repository_owner_id", "ref", "events", "require_private"}
# Any of these means a GitHub Actions job context (GitHub does not let workflows overwrite GITHUB_*/RUNNER_*).
# ACTIONS_* tokens are deliberately not markers: they never establish trust and are absent from local shells.
HOSTED_MARKERS = ("GITHUB_ACTIONS", "GITHUB_RUN_ID", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH",
                  "GITHUB_WORKFLOW_REF", "RUNNER_ENVIRONMENT")
HOSTED_REQUIRED = ("GITHUB_RUN_ID", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "GITHUB_REF", "GITHUB_REPOSITORY_ID",
                   "GITHUB_REPOSITORY_OWNER", "GITHUB_REPOSITORY_OWNER_ID", "GITHUB_ACTOR", "GITHUB_ACTOR_ID",
                   "GITHUB_TRIGGERING_ACTOR")
NUMERIC_ID = re.compile(r"^[1-9][0-9]{0,19}$")
LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
MAX_EVENT_BYTES = 1 << 20


class Fail(Exception):
    def __init__(self, code: int, reason: str):
        super().__init__(reason)
        self.code = code


def _is_id(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def load_trusted_inputs(path: Path | None = None) -> dict:
    """The pinned trust configuration; anything unexpected is a configuration error (exit 2)."""
    path = TRUSTED_INPUTS if path is None else path
    try:
        if path.is_symlink() or not path.is_file():
            raise Fail(2, "trusted-input configuration missing or a symlink")
        pins = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Fail(2, "trusted-input configuration unreadable or malformed") from exc
    if not isinstance(pins, dict) or set(pins) != TRUSTED_KEYS or pins.get("schema") != "c5-trusted-inputs/1":
        raise Fail(2, "trusted-input configuration has an unexpected schema")
    if not (_is_id(pins["repository_id"]) and _is_id(pins["repository_owner_id"])
            and pins["ref"] == "refs/heads/main" and pins["events"] == ["workflow_dispatch"]
            and pins["require_private"] is True):
        raise Fail(2, "trusted-input configuration values are not the reviewed pins")
    return pins


def _read_event(raw: str) -> dict:
    path = Path(raw)
    try:
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise Fail(2, "hosted event payload missing, relative or a symlink")
        if path.stat().st_size > MAX_EVENT_BYTES:
            raise Fail(2, "hosted event payload too large")
        payload = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Fail(2, "hosted event payload unreadable or malformed") from exc
    if not isinstance(payload, dict):
        raise Fail(2, "hosted event payload malformed")
    return payload


def trusted_context(env=None, pins_path: Path | None = None) -> dict:
    """C5 R2(a) P1 fail-closed trusted-input check (exit 2 on any doubt). Without any GitHub Actions marker the
    caller is a local developer workstation (owner-controlled) and nothing is required; with any marker, the full
    owner-dispatched workflow_dispatch-on-main context must be present, well formed, pinned and self-consistent."""
    env = os.environ if env is None else env
    present = [k for k in HOSTED_MARKERS if k in env]
    if not present:
        return {"mode": "local", "trusted": True}
    pins = load_trusted_inputs(pins_path)
    if env.get("GITHUB_ACTIONS") != "true":
        raise Fail(2, f"hosted context markers {present[:3]} present but GITHUB_ACTIONS is not 'true' (contradictory)")
    missing = [k for k in HOSTED_REQUIRED if not env.get(k)]
    if missing:
        raise Fail(2, f"hosted context incomplete (missing {missing[:4]})")
    event, ref = env["GITHUB_EVENT_NAME"], env["GITHUB_REF"]
    if event not in pins["events"]:
        raise Fail(2, f"untrusted event {event[:40]!r}: only {pins['events']} is allowed")
    if ref != pins["ref"]:
        raise Fail(2, f"untrusted ref {ref[:60]!r}: only {pins['ref']} is allowed")
    ids = {k: env[k] for k in ("GITHUB_REPOSITORY_ID", "GITHUB_REPOSITORY_OWNER_ID", "GITHUB_ACTOR_ID")}
    if not all(NUMERIC_ID.fullmatch(v) for v in ids.values()):
        raise Fail(2, "hosted context has a malformed numeric ID")
    if int(ids["GITHUB_REPOSITORY_ID"]) != pins["repository_id"]:
        raise Fail(2, "untrusted repository (GITHUB_REPOSITORY_ID differs from the pin)")
    if int(ids["GITHUB_REPOSITORY_OWNER_ID"]) != pins["repository_owner_id"]:
        raise Fail(2, "untrusted repository owner (GITHUB_REPOSITORY_OWNER_ID differs from the pin)")
    if int(ids["GITHUB_ACTOR_ID"]) != pins["repository_owner_id"]:
        raise Fail(2, "untrusted actor (GITHUB_ACTOR_ID is not the repository owner)")
    owner, actor, triggering = env["GITHUB_REPOSITORY_OWNER"], env["GITHUB_ACTOR"], env["GITHUB_TRIGGERING_ACTOR"]
    if not all(LOGIN.fullmatch(v) for v in (owner, actor, triggering)):
        raise Fail(2, "hosted context has a malformed login")
    if actor != owner:
        raise Fail(2, "untrusted actor (GITHUB_ACTOR is not the repository owner)")
    if triggering != owner:
        raise Fail(2, "untrusted triggering actor (re-run or dispatch by someone other than the owner)")
    payload = _read_event(env["GITHUB_EVENT_PATH"])
    repo, sender = payload.get("repository"), payload.get("sender")
    owner_obj = repo.get("owner") if isinstance(repo, dict) else None
    if not (isinstance(repo, dict) and isinstance(sender, dict) and isinstance(owner_obj, dict)
            and "inputs" in payload and isinstance(payload.get("workflow"), str) and isinstance(payload.get("ref"), str)):
        raise Fail(2, "hosted event payload is not a workflow_dispatch payload")
    if payload["ref"] != ref:
        raise Fail(2, "event payload ref contradicts GITHUB_REF")
    if not _is_id(repo.get("id")) or repo["id"] != pins["repository_id"]:
        raise Fail(2, "event payload repository differs from the pinned repository")
    if repo.get("fork") is not False:
        raise Fail(2, "event payload repository is a fork (or fork flag missing)")
    if pins["require_private"] and repo.get("private") is not True:
        raise Fail(2, "event payload repository is not private (or private flag missing)")
    if not _is_id(owner_obj.get("id")) or owner_obj["id"] != pins["repository_owner_id"] or owner_obj.get("login") != owner:
        raise Fail(2, "event payload repository owner contradicts the pin or GITHUB_REPOSITORY_OWNER")
    if not _is_id(sender.get("id")) or sender["id"] != pins["repository_owner_id"] or sender.get("login") != triggering:
        raise Fail(2, "event payload sender is not the repository owner")
    return {"mode": "hosted", "trusted": True, "event": event, "ref": ref, "repository_id": pins["repository_id"],
            "actor_id": pins["repository_owner_id"]}


def trust_check() -> int:
    try:
        ctx = trusted_context()
    except Fail as fail:
        print(f"trust-check: exit {fail.code} ({EXIT_NAMES[fail.code]}) - {fail}")
        return fail.code
    detail = "no hosted CI context" if ctx["mode"] == "local" else f"{ctx['event']} on {ctx['ref']} by the repository owner"
    print(f"trust-check: ok ({ctx['mode']}: {detail})")
    return 0


def read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def facts() -> dict:
    os_release = {}
    for line in (read("/etc/os-release") or "").splitlines():
        key, _, value = line.partition("=")
        if key in {"PRETTY_NAME", "VERSION_ID", "ID"}:
            os_release[key] = value.strip('"')
    cpu = next((l.split(":", 1)[1].strip() for l in (read("/proc/cpuinfo") or "").splitlines()
                if l.startswith("model name")), None)
    mem = next((l.split(":", 1)[1].strip() for l in (read("/proc/meminfo") or "").splitlines()
                if l.startswith("MemTotal")), None)
    seccomp = next((l.split(":", 1)[1].strip() for l in (read("/proc/self/status") or "").splitlines()
                    if l.startswith("Seccomp:")), None)
    try:
        libc = os.confstr("CS_GNU_LIBC_VERSION")
    except (ValueError, OSError):
        libc = None
    auth = os.environ.get("TRIAL_AUTHORIZATION_REFERENCE", "")
    return {
        "schema": "c5-f4-runner-facts/1",
        "system": platform.system(), "machine": platform.machine(), "kernel": platform.release(),
        "os_release": os_release, "libc": libc, "python": platform.python_version(),
        "cpu_model": cpu, "cpu_count": os.cpu_count(), "mem_total": mem, "euid": os.geteuid(),
        "seccomp_mode": seccomp,
        "userns": {"max_user_namespaces": read("/proc/sys/user/max_user_namespaces"),
                   "unprivileged_userns_clone": read("/proc/sys/kernel/unprivileged_userns_clone"),
                   "apparmor_restrict_unprivileged_userns":
                       read("/proc/sys/kernel/apparmor_restrict_unprivileged_userns")},
        "apparmor_enabled": read("/sys/module/apparmor/parameters/enabled"),
        "unshare_present": Path("/usr/bin/unshare").exists(),
        "docker_present": shutil.which("docker") is not None,
        "github": {k: os.environ.get(k) for k in CONTEXT_KEYS},
        "authorization_reference": auth if AUTH_PATTERN.fullmatch(auth) else None,
    }


def sha(rel: str) -> str | None:
    path = ROOT / rel
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def write_json(path: Path, data: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------- harness (inside or outside a container)
def run(semgrep: Path, repeat: int, isolation: str, gate_args: tuple[str, ...] = ()) -> int:
    started = time.monotonic()
    argv = [sys.executable, "-I", str(HARNESS), "--semgrep", str(semgrep), "--repeat", str(repeat),
            "--isolation", isolation]
    if isolation == "container":  # the harness verifies the host TypeScript attestation for this run's nonce
        argv += ["--ts-nonce", os.environ.get("C5_TRIAL_NONCE", "")]
    else:  # auto: the harness runs the TypeScript gate itself (optional explicit node / compiler location)
        argv += list(gate_args)
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1500, check=False)
    wall = round(time.monotonic() - started, 2)
    rss_kib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    code = proc.returncode if proc.returncode in range(6) else 3
    # Harness stdout is fixed diagnostics plus rule/path/line findings; stderr is not published.
    lines = [line[:300] for line in proc.stdout.splitlines()][:40]
    summary = {}
    if code in (0, 1, 4) and SUMMARY.is_file():
        data = json.loads(SUMMARY.read_text())
        source = data.get("source") or {}
        controls = data.get("controls") or {}
        summary = {
            "result": data.get("result"), "isolation": data.get("isolation"),
            "isolation_mode": data.get("isolation_mode"), "toolchain": data.get("toolchain"),
            "inventory_total": (data.get("inventory") or {}).get("total_files"),
            "controls": {k: controls.get(k) for k in ("status", "fixtures", "failed_cases", "seconds",
                                                       "parser_gap_drift", "unexpected_findings")},
            "controls_outcomes": {o: sum(c.get("outcome") == o for c in controls.get("cases", []))
                                  for o in ("detected", "clean", "known-miss", "MISSED", "FALSE-POSITIVE",
                                            "UNEXPECTEDLY-DETECTED")},
            "source": {k: source.get(k) for k in ("status", "targets", "findings", "wall_seconds",
                                                   "max_memory_bytes", "total_bytes")},
            "typescript_syntax_gate": data.get("typescript_syntax_gate"),
        }
    nonce = os.environ.get("C5_TRIAL_NONCE", "")
    record = {
        "schema": "c5-f4-hosted-trial/2", "non_blocking": True, "isolation_requested": isolation,
        "nonce": nonce if re.fullmatch(r"[0-9a-f]{32}", nonce) else None,
        "harness_exit": proc.returncode, "result": EXIT_NAMES[code], "harness_wall_seconds": wall,
        "peak_child_rss_kib": rss_kib, "repeat": repeat, "harness_stdout": lines,
        "input_sha256sum": [f"{sha(p)}  {p}" for p in INPUT_HASHES],
        "facts": facts(), "summary": summary,
    }
    write_json(TRIAL, record)
    print("\n".join(lines))
    print(f"trial: harness exit {proc.returncode} ({EXIT_NAMES[code]}), wall {wall}s, peak child RSS {rss_kib} KiB")
    return code


# ---------------------------------------------------------------- docker orchestration (host side)
def docker() -> str:
    path = shutil.which("docker")
    if not path:
        raise Fail(6, "docker CLI not found")
    return path


def checked_dir(raw: str, what: str, must_exist: bool = True) -> Path:
    path = Path(raw).absolute()
    if any(c in str(path) for c in ",=\n"):
        raise Fail(2, f"{what} path contains characters unsafe for --mount")
    if path.is_symlink():
        raise Fail(2, f"{what} is a symlink")
    if must_exist and not path.is_dir():
        raise Fail(2, f"{what} missing: {path}")
    return path


def image_id(path: str) -> str:
    try:
        value = Path(path).read_text().strip()
    except OSError as exc:
        raise Fail(6, "runtime image id file missing (image not built)") from exc
    if not IMAGE_ID.fullmatch(value):
        raise Fail(2, "runtime image id file is malformed")
    return value


def hardened(image: str, mounts: list[tuple[Path, str, bool]], command: list[str], name: str,
             env_values: tuple[str, ...] = (), env_names: tuple[str, ...] = ()) -> list[str]:
    argv = [docker(), "run", "--name", name, *HARDENING]
    for source, target, readonly in mounts:
        argv += ["--mount", f"type=bind,source={source},target={target}" + (",readonly" if readonly else "")]
    for value in env_values:
        argv += ["--env", value]
    for key in env_names:  # value is taken from the docker CLI environment, never placed in argv
        argv += ["--env", key]
    return [*argv, image, *command]


def docker_call(argv: list[str], timeout: int, name: str, env: dict | None = None):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False, env=env)
    except subprocess.TimeoutExpired as exc:
        subprocess.run([docker(), "kill", name], capture_output=True, check=False)
        raise Fail(6, f"container {name} exceeded {timeout}s and was killed") from exc


def last_line(text: str) -> str:
    lines = [l for l in (text or "").strip().splitlines() if l.strip()]
    return lines[-1][:240] if lines else "no output"


def container_build(iidfile: str) -> int:
    started = time.monotonic()
    record = {"schema": "c5-f4r-container-image/1", "base_image": BASE_IMAGE,
              "dockerfile_sha256": sha("security/sast/container/Dockerfile")}
    try:
        record["trusted_input"] = trusted_context()  # C5 R2(a): before any build or download
        text = DOCKERFILE.read_text()
        froms = [l.split()[1] for l in text.splitlines() if l.startswith("FROM ")]
        if froms != [BASE_IMAGE] or re.search(r"^\s*(ADD|COPY)\b", text, re.M):
            raise Fail(2, "Dockerfile must use only the pinned base and must not ADD/COPY repository content")
        iid = Path(iidfile).absolute()
        build = subprocess.run([docker(), "build", "--platform", "linux/amd64", "--no-cache", "--iidfile", str(iid),
                                "-f", str(DOCKERFILE), str(CONTAINER_DIR)], capture_output=True, text=True,
                               timeout=900, check=False)
        if build.returncode != 0:
            raise Fail(6, f"image build failed: {last_line(build.stderr)}")
        image = image_id(str(iid))
        meta = subprocess.run([docker(), "image", "inspect", image, "--format",
                               "{{.Architecture}} {{.Os}} {{.Config.User}}"], capture_output=True, text=True,
                              check=False)
        if meta.stdout.split() != ["amd64", "linux", "1001:1001"]:
            raise Fail(2, f"runtime image metadata unexpected: {meta.stdout.strip()}")
        name = f"c5f4r-inventory-{secrets.token_hex(4)}"
        listing = docker_call(hardened(image, [], [
            "sh", "-c", "dpkg-query -W -f='${Package}=${Version}\\n'; echo ---; "
                        "for p in $(dpkg-query -W -f='${Package} '); do "
                        "[ -f /usr/share/doc/$p/copyright ] || echo $p; done; echo ---; python3 -V"], name),
            120, name)
        if listing.returncode != 0:
            raise Fail(6, f"image inventory container failed ({listing.returncode})")
        packages, missing, python = (listing.stdout.split("---\n") + ["", "", ""])[:3]
        record.update({"image_id": image, "architecture": "amd64", "user": "1001:1001",
                       "packages": packages.split(), "package_count": len(packages.split()),
                       "copyright_missing": missing.split(), "python": python.strip(), "status": "built"})
        code = 0
    except Fail as fail:
        record.update({"status": "failed", "reason": str(fail)})
        code = fail.code
    record.update({"exit": code, "result": EXIT_NAMES[code], "seconds": round(time.monotonic() - started, 2)})
    write_json(IMAGE_EVIDENCE, record)
    print(f"container-build: {'ok' if code == 0 else EXIT_NAMES[code]} ({record.get('reason') or record.get('image_id')})")
    return code


def container_install(iidfile: str, wheels: str, venv: str) -> int:
    started = time.monotonic()
    record = {"schema": "c5-f4r-container-install/1", "hardening": list(HARDENING)}
    try:
        record["trusted_input"] = trusted_context()  # C5 R2(a): before any container
        image = image_id(iidfile)
        wheel_dir = checked_dir(wheels, "wheelhouse")
        venv_dir = checked_dir(venv, "venv directory", must_exist=False)
        venv_dir.mkdir(parents=True, exist_ok=True)
        if any(venv_dir.iterdir()):
            raise Fail(2, "venv directory must be empty before install")
        mounts = [(ROOT, "/repo", True), (wheel_dir, "/wheels", True), (venv_dir, "/opt/sast", False)]
        stages = (
            ("venv", ["python3", "-m", "venv", "/opt/sast"], 6),
            ("pip-install", ["/opt/sast/bin/python", "-m", "pip", "install", "--no-index", "--no-deps",
                             "--only-binary=:all:", "--require-hashes", "--find-links", "/wheels",
                             "-r", f"/repo/{LOCK}"], 2),
            ("pip-check", ["/opt/sast/bin/python", "-m", "pip", "check"], 2),
        )
        record["stages"] = {}
        for stage, command, failure_code in stages:
            name = f"c5f4r-{stage}-{secrets.token_hex(4)}"
            proc = docker_call(hardened(image, mounts, command, name, PIP_ENV), 600, name)
            record["stages"][stage] = {"exit": proc.returncode, "last": last_line(proc.stdout or proc.stderr)}
            if proc.returncode >= 125:
                raise Fail(6, f"{stage}: container runtime error {proc.returncode}: {last_line(proc.stderr)}")
            if proc.returncode != 0:
                raise Fail(failure_code, f"{stage} failed (fatal): {last_line(proc.stdout + proc.stderr)}")
        code = 0
    except Fail as fail:
        record.update({"reason": str(fail)})
        code = fail.code
    record.update({"exit": code, "result": EXIT_NAMES[code], "seconds": round(time.monotonic() - started, 2)})
    write_json(INSTALL_EVIDENCE, record)
    print(f"container-install: {'ok' if code == 0 else EXIT_NAMES[code]} ({record.get('reason') or 'venv installed offline; pip check pass'})")
    return code


def pinned_node(raw: str | None) -> Path | None:
    """C5-G4H: an explicit node must be an absolute executable reporting exactly apps/octocat-supply/.node-version."""
    if raw is None:
        return None
    node = Path(raw)
    if not node.is_absolute() or not node.is_file() or not os.access(node, os.X_OK):
        raise Fail(2, "pinned node runtime missing or not an absolute executable path")
    try:
        want = "v" + NODE_VERSION_FILE.read_text().strip()
        got = subprocess.run([str(node), "--version"], capture_output=True, text=True, timeout=30, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Fail(2, "pinned node runtime did not start") from exc
    if not re.fullmatch(r"v\d+\.\d+\.\d+", want) or got != want:
        raise Fail(2, f"node runtime {got[:20] or 'unknown'} differs from pinned {want[:20]}")
    return node


def typescript_gate(nonce: str, node: Path | None = None) -> dict:
    """Host-side C5-G4 gate before any container starts; failures keep their harness code (2/3/4)."""
    argv = [sys.executable, "-I", str(HARNESS), "--typescript-gate-only", "--ts-nonce", nonce]
    if node is not None:
        argv += ["--node", str(node)]
    try:
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
    except subprocess.TimeoutExpired as exc:
        raise Fail(3, "host TypeScript syntax gate timed out") from exc
    result = {"exit": proc.returncode, "last": last_line(proc.stdout)}
    print(result["last"])
    if proc.returncode != 0:
        code = proc.returncode if proc.returncode in TS_GATE_EXITS else 3
        raise Fail(code, f"host TypeScript syntax gate failed before the container started: {result['last']}")
    return result


def typescript_preflight(node_raw: str) -> int:
    """C5-G4H: fail before any image build or container if Node or the lock-pinned compiler is wrong."""
    try:
        trusted_context()  # C5 R2(a): before Node or the compiler is executed
        node = pinned_node(node_raw)
        result = typescript_gate(secrets.token_hex(16), node)
        print(f"typescript-preflight: ok (node {NODE_VERSION_FILE.read_text().strip()}; {result['last']})")
        return 0
    except Fail as fail:
        print(f"typescript-preflight: exit {fail.code} ({EXIT_NAMES[fail.code]}) - {fail}")
        return fail.code


def container_run(iidfile: str, venv: str, repeat: int, node_raw: str | None = None) -> int:
    started = time.monotonic()
    nonce = secrets.token_hex(16)
    record = {"schema": "c5-f4r-container-run/1", "hardening": list(HARDENING), "nonce": nonce}
    try:
        record["trusted_input"] = trusted_context()  # C5 R2(a): before the host gate, Docker or Semgrep
        node = pinned_node(node_raw)
        image = image_id(iidfile)
        venv_dir = checked_dir(venv, "venv directory")
        artifacts = ROOT / "artifacts"
        artifacts.mkdir(exist_ok=True)
        (artifacts / "sast").mkdir(exist_ok=True)
        mounts = [(ROOT, "/repo", True), (artifacts, "/repo/artifacts", False), (venv_dir, "/opt/sast", True)]
        record["typescript_gate"] = typescript_gate(nonce, node)
        name = f"c5f4r-scan-{secrets.token_hex(4)}"
        env = {**os.environ, "C5_TRIAL_NONCE": nonce}
        argv = hardened(image, mounts, ["python3", "-I", "/repo/scripts/sast/hosted_trial.py", "run",
                                        "--isolation", "container", "--semgrep", "/opt/sast/bin/semgrep",
                                        "--repeat", str(repeat)], name,
                        env_names=(*CONTEXT_KEYS, "TRIAL_AUTHORIZATION_REFERENCE", "C5_TRIAL_NONCE"))
        proc = docker_call(argv, 1800, name, env)
        print(proc.stdout.rstrip())
        record["docker_exit"] = proc.returncode
        if proc.returncode == 7:
            raise Fail(7, "in-container driver could not produce evidence")
        if proc.returncode not in range(6):
            raise Fail(6, f"container runtime error {proc.returncode}: {last_line(proc.stderr)}")
        try:
            evidence = json.loads(TRIAL.read_text())
        except (OSError, ValueError) as exc:
            raise Fail(7, "hosted-trial.json missing or unreadable after container run") from exc
        if evidence.get("nonce") != nonce:
            raise Fail(7, "hosted-trial.json is stale or was not written by this run (nonce mismatch)")
        if evidence.get("harness_exit") != proc.returncode:
            raise Fail(7, "hosted-trial.json harness exit disagrees with the container exit code")
        code = proc.returncode
    except Fail as fail:
        record["reason"] = str(fail)
        code = fail.code
    record.update({"exit": code, "result": EXIT_NAMES[code], "seconds": round(time.monotonic() - started, 2)})
    write_json(RUN_EVIDENCE, record)
    print(f"container-run: exit {code} ({EXIT_NAMES[code]}){' - ' + record['reason'] if 'reason' in record else ''}")
    return code


def summarize() -> int:
    rows = []
    for label, path in (("image", IMAGE_EVIDENCE), ("install", INSTALL_EVIDENCE), ("scan", RUN_EVIDENCE),
                        ("harness", TRIAL)):
        try:
            data = json.loads(path.read_text())
            rows.append(f"* {label}: exit {data.get('exit', data.get('harness_exit'))} ({data.get('result')})"
                        + (f" - {data['reason']}" if data.get("reason") else ""))
        except (OSError, ValueError):
            rows.append(f"* {label}: **evidence missing**")
    complete = not any("evidence missing" in r for r in rows)
    text = ("## C5-F4R hosted SAST trial (non-blocking)\n\n" + "\n".join(rows) +
            "\n* This run cannot authorize release, deployment or C5 acceptance.\n")
    print(text)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a") as handle:
            handle.write(text)
    return 0 if complete else 7


def main() -> int:
    """Any unexpected driver failure means evidence could not be produced: exit 7, never Python's
    default exit 1 (= findings). Only the exception type is printed."""
    try:
        return _main()
    except Exception as exc:  # noqa: BLE001 - deliberate fail-closed classification
        print(f"driver: exit 7 (evidence-missing) - unexpected internal error ({type(exc).__name__})")
        return 7


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("facts")
    sub.add_parser("summarize")
    runner = sub.add_parser("run")
    runner.add_argument("--semgrep", required=True, type=Path)
    runner.add_argument("--repeat", type=int, default=5)
    runner.add_argument("--isolation", choices=("auto", "container"), default="auto")
    runner.add_argument("--node", help="auto mode only: node runtime for the TypeScript gate")
    runner.add_argument("--typescript-dir", help="auto mode only: installed typescript (hash-verified)")
    build = sub.add_parser("container-build")
    build.add_argument("--iidfile", required=True)
    install = sub.add_parser("container-install")
    install.add_argument("--image-id-file", required=True)
    install.add_argument("--wheels", required=True)
    install.add_argument("--venv", required=True)
    scan = sub.add_parser("container-run")
    scan.add_argument("--image-id-file", required=True)
    scan.add_argument("--venv", required=True)
    scan.add_argument("--repeat", type=int, default=5)
    scan.add_argument("--node", help="absolute path of the pinned node (exact .node-version) for the host TypeScript gate")
    pre = sub.add_parser("typescript-preflight")
    pre.add_argument("--node", required=True, help="absolute path of the pinned node (exact .node-version)")
    sub.add_parser("trust-check")
    args = parser.parse_args()
    if args.command == "trust-check":
        return trust_check()
    if args.command == "facts":
        data = facts()
        write_json(FACTS, data)
        print(json.dumps({k: data[k] for k in ("system", "machine", "kernel", "libc", "python", "cpu_count",
                                               "seccomp_mode", "userns", "apparmor_enabled", "docker_present")},
                         indent=2))
        return 0
    if args.command == "summarize":
        return summarize()
    if args.command == "run":
        gate_args = tuple(a for flag, value in (("--node", args.node), ("--typescript-dir", args.typescript_dir))
                          if value for a in (flag, value))
        if gate_args and args.isolation == "container":
            print("driver: --node/--typescript-dir apply to auto mode only")
            return 2
        return run(args.semgrep.absolute(), max(1, min(args.repeat, 10)), args.isolation, gate_args)
    if args.command == "container-build":
        return container_build(args.iidfile)
    if args.command == "container-install":
        return container_install(args.image_id_file, args.wheels, args.venv)
    if args.command == "typescript-preflight":
        return typescript_preflight(args.node)
    return container_run(args.image_id_file, args.venv, max(1, min(args.repeat, 10)), args.node)


if __name__ == "__main__":
    sys.exit(main())
