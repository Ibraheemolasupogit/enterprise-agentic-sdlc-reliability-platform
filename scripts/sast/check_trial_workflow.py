"""Static policy for the C5-F4 hosted SAST trial workflow (local check; not a CI gate).

Requires PyYAML (already pinned in requirements-delivery.txt). Exits 0 on PASS,
1 on any violation. The trial must stay dispatch-only, read-only, pinned,
injection-safe, hash-locked, fail-closed, allowlisted for upload and
non-blocking (never part of ci.yml's required gate).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / ".github/workflows/c5-sast-hosted-trial.yml"
CI = ROOT / ".github/workflows/ci.yml"
TRIAL_NAME = "c5-sast-hosted-trial"
CONFIRM_PHRASE = "run-c5-f4-hosted-trial"
REQUIRED_NEEDS = ["application", "policy", "containers", "codeql"]
LOCK = "requirements-sast-linux.txt"


class Violation(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Violation(message)


def ci_action_pins(ci: dict) -> set[str]:
    return {step["uses"] for job in ci["jobs"].values() for step in job.get("steps", []) if "uses" in step}


def trial_policy(trial: dict, trial_text: str, ci: dict, ci_text: str) -> None:
    require(set(trial) <= {"name", "on", "permissions", "concurrency", "jobs"}, "Unexpected top-level key")
    require(set(trial["on"]) == {"workflow_dispatch"}, "Trial must be workflow_dispatch only")
    inputs = trial["on"]["workflow_dispatch"].get("inputs", {})
    require(set(inputs) == {"confirm", "authorization_reference"}, "Unexpected dispatch inputs")
    require(all(i.get("required") == "true" and i.get("type") == "string" for i in inputs.values()),
            "Dispatch inputs must be required strings")
    require(trial["permissions"] == {"contents": "read"}, "Trial permissions must be contents: read only")
    require("concurrency" in trial, "Trial must serialize runs")
    for forbidden in ("secrets.", "id-token", "pull_request_target", "security-events", "GITHUB_TOKEN",
                      "continue-on-error", "environment:", "sudo ", "curl ", "wget "):
        require(forbidden not in trial_text, f"Forbidden construct in trial: {forbidden.strip()}")
    require(list(trial["jobs"]) == ["hosted-sast-trial"], "Exactly one trial job expected")
    job = trial["jobs"]["hosted-sast-trial"]
    require(set(job) <= {"runs-on", "timeout-minutes", "steps"}, "Unexpected job key (permissions/if/needs/container/...)")
    require(job["runs-on"] == "ubuntu-24.04", "Trial must use the ubuntu-24.04 hosted runner")
    require(1 <= int(job["timeout-minutes"]) <= 30, "Trial needs a bounded timeout")
    steps = job["steps"]
    pins = ci_action_pins(ci)
    for step in steps:
        if "uses" in step:
            require(re.fullmatch(r"[\w./-]+@[a-f0-9]{40}", step["uses"]), "Unpinned action")
            require(step["uses"] in pins, "Action/SHA not already reviewed in ci.yml")
            if step["uses"].startswith("actions/checkout@"):
                require(step.get("with", {}).get("persist-credentials") == "false", "Checkout must not persist credentials")
        if "run" in step:
            require("${{" not in step["run"], "Expressions must reach scripts via env only (injection)")
    guard = steps[0]
    require("run" in guard and CONFIRM_PHRASE in guard["run"] and "exit 2" in guard["run"],
            "First step must enforce the owner confirmation phrase")
    require(guard.get("env", {}).get("CONFIRM") == "${{ inputs.confirm }}", "Confirmation must arrive via env")
    runs = [s.get("run", "") for s in steps]
    pip_cmds = [line for r in runs for line in r.splitlines() if " -m pip download" in line or " -m pip install" in line]
    require(len(pip_cmds) == 2, "Expected exactly one download and one install")
    for cmd in pip_cmds:
        for flag in ("--require-hashes", "--no-deps", "--only-binary=:all:", f"-r {LOCK}"):
            require(flag in cmd, f"pip command missing {flag}")
    install = next(c for c in pip_cmds if " -m pip install" in c)
    require("--no-index" in install, "Install must be offline (--no-index)")
    order = [i for i, r in enumerate(runs) if "-m pip install" in r]
    require(order and "-m pip check" in runs[order[0]].split("-m pip install", 1)[1], "pip check must follow install")
    harness = [i for i, r in enumerate(runs) if "scripts/sast/hosted_trial.py run" in r]
    require(len(harness) == 1 and harness[0] > order[0], "Harness run must follow the verified install")
    upload = [s for s in steps if s.get("uses", "").startswith("actions/upload-artifact@")]
    require(len(upload) == 1 and upload[0].get("if") == "always()", "Evidence upload must always run once")
    paths = [p.strip() for p in upload[0]["with"]["path"].splitlines() if p.strip()]
    require(paths and all(p.startswith("artifacts/sast/") and p.endswith(".json") and "*" not in p for p in paths),
            "Upload must list explicit artifacts/sast/*.json files only")
    require(not any("private" in p for p in paths), "Raw/private reports must never be uploaded")
    require(int(upload[0]["with"].get("retention-days", 999)) <= 7, "Evidence retention must be <= 7 days")
    # Non-blocking: the existing release gate is untouched and never depends on the trial.
    require(ci["jobs"]["required"]["needs"] == REQUIRED_NEEDS, "ci.yml required gate changed")
    require(TRIAL_NAME not in ci_text and "hosted-sast-trial" not in ci_text, "ci.yml must not reference the trial")


def main() -> int:
    trial_text, ci_text = TRIAL.read_text(), CI.read_text()
    try:
        trial_policy(yaml.load(trial_text, Loader=yaml.BaseLoader), trial_text,
                     yaml.load(ci_text, Loader=yaml.BaseLoader), ci_text)
    except (Violation, yaml.YAMLError, KeyError, TypeError, ValueError, StopIteration) as exc:
        print(f"FAIL: C5-F4 trial workflow policy: {exc}")
        return 1
    print("PASS: C5-F4 trial workflow is dispatch-only, read-only, pinned, injection-safe, hash-locked, "
          "fail-closed, allowlisted and non-blocking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
