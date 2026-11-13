"""C5-F4 hosted SAST trial driver (non-blocking, owner-dispatched only).

Subcommands:
  facts  Record read-only runner facts before any download (always safe to run).
  run    Execute the hardened F3 harness unchanged, measure wall time and peak
         child RSS, and write allowlisted evidence. Exits with the harness code:
         0 clean, 1 findings, 2 config, 3 tool, 4 control, 5 isolation unavailable.

Outputs (ignored artifacts/, allowlisted for upload; never raw engine reports):
  artifacts/sast/hosted-runner-facts.json, artifacts/sast/hosted-trial.json
Stdlib only; run with `python3 -I`. Never invokes sudo or changes system state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/sast"
FACTS = OUT / "hosted-runner-facts.json"
TRIAL = OUT / "hosted-trial.json"
SUMMARY = OUT / "c5-summary.json"
HARNESS = ROOT / "scripts/sast/feasibility.py"
EXIT_NAMES = {0: "clean", 1: "findings", 2: "configuration-error", 3: "tool-error",
              4: "control-failure", 5: "isolation-unavailable"}
# Non-secret GitHub/runner metadata only; tokens and arbitrary environment are never read.
CONTEXT_KEYS = ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_REF", "GITHUB_WORKFLOW_REF",
                "GITHUB_EVENT_NAME", "RUNNER_OS", "RUNNER_ARCH", "RUNNER_ENVIRONMENT", "ImageOS", "ImageVersion")
AUTH_PATTERN = re.compile(r"^[A-Za-z0-9._:/ -]{8,80}$")
INPUT_HASHES = ("scripts/sast/feasibility.py", "scripts/sast/hosted_trial.py", "security/sast/toolchain.json",
                "security/sast/controls.json", "security/sast/rules/typescript.yml", "security/sast/rules/python.yml",
                "requirements-sast-linux.txt", ".github/workflows/c5-sast-hosted-trial.yml")


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
        "github": {k: os.environ.get(k) for k in CONTEXT_KEYS},
        "authorization_reference": auth if AUTH_PATTERN.fullmatch(auth) else None,
    }


def sha(rel: str) -> str | None:
    path = ROOT / rel
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def run(semgrep: Path, repeat: int) -> int:
    started = time.monotonic()
    proc = subprocess.run([sys.executable, "-I", str(HARNESS), "--semgrep", str(semgrep), "--repeat", str(repeat)],
                          cwd=ROOT, capture_output=True, text=True, timeout=1500, check=False)
    wall = round(time.monotonic() - started, 2)
    rss_kib = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    code = proc.returncode if proc.returncode in EXIT_NAMES else 3
    # Harness stdout is fixed diagnostics plus rule/path/line findings; stderr is not published.
    lines = [line[:300] for line in proc.stdout.splitlines()][:40]
    summary = {}
    if code in (0, 1, 4) and SUMMARY.is_file():
        data = json.loads(SUMMARY.read_text())
        source = data.get("source") or {}
        controls = data.get("controls") or {}
        summary = {
            "result": data.get("result"), "isolation": data.get("isolation"), "toolchain": data.get("toolchain"),
            "inventory_total": (data.get("inventory") or {}).get("total_files"),
            "controls": {k: controls.get(k) for k in ("status", "fixtures", "failed_cases", "seconds",
                                                       "parser_gap_drift", "unexpected_findings")},
            "controls_outcomes": {o: sum(c.get("outcome") == o for c in controls.get("cases", []))
                                  for o in ("detected", "clean", "known-miss", "MISSED", "FALSE-POSITIVE",
                                            "UNEXPECTEDLY-DETECTED")},
            "source": {k: source.get(k) for k in ("status", "targets", "findings", "wall_seconds",
                                                   "max_memory_bytes", "total_bytes")},
        }
    record = {
        "schema": "c5-f4-hosted-trial/1", "non_blocking": True,
        "harness_exit": proc.returncode, "result": EXIT_NAMES[code], "harness_wall_seconds": wall,
        "peak_child_rss_kib": rss_kib, "repeat": repeat, "harness_stdout": lines,
        "input_sha256sum": [f"{sha(p)}  {p}" for p in INPUT_HASHES],
        "facts": facts(), "summary": summary,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    TRIAL.write_text(json.dumps(record, indent=2) + "\n")
    print("\n".join(lines))
    print(f"trial: harness exit {proc.returncode} ({EXIT_NAMES[code]}), wall {wall}s, peak child RSS {rss_kib} KiB")
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a") as handle:
            handle.write("## C5-F4 hosted SAST trial (non-blocking)\n\n"
                         f"* Harness exit: **{proc.returncode} ({EXIT_NAMES[code]})**\n"
                         f"* Wall: {wall}s; peak child RSS: {rss_kib} KiB\n"
                         f"* Isolation: {summary.get('isolation') or 'not established'}\n"
                         "* This run cannot authorize release, deployment or C5 acceptance.\n")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("facts")
    runner = sub.add_parser("run")
    runner.add_argument("--semgrep", required=True, type=Path)
    runner.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()
    if args.command == "facts":
        OUT.mkdir(parents=True, exist_ok=True)
        data = facts()
        FACTS.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({k: data[k] for k in ("system", "machine", "kernel", "libc", "python", "cpu_count",
                                               "seccomp_mode", "userns", "apparmor_enabled")}, indent=2))
        return 0
    return run(args.semgrep.absolute(), max(1, min(args.repeat, 10)))


if __name__ == "__main__":
    sys.exit(main())
