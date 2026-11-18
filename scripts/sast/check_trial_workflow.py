"""Static policy for the C5-F4/F4R hosted SAST trial workflow (local check; not a CI gate).

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
DOCKERFILE = ROOT / "security/sast/container/Dockerfile"
BASE_IMAGE = "ubuntu@sha256:77eb101c607d6e3d4f5ad0c8a02c2136c689b98aba1f359e6502ba517e5c57ec"
REQUIRED_HARDENING = (("--network", "none"), ("--user", "1001:1001"), ("--cap-drop", "ALL"),
                      ("--security-opt", "no-new-privileges=true"), ("--pull", "never"),
                      ("--platform", "linux/amd64"), ("--ipc", "none"))
REQUIRED_FLAGS = ("--rm", "--read-only")
# C5-G4H: host-side TypeScript gate prerequisites (pinned Node + lock-verified compiler) before any container.
NODE_VERSION_FILE = ROOT / "apps/octocat-supply/.node-version"
APP_DIR = "apps/octocat-supply"
NPM_INSTALL = "npm ci --ignore-scripts"
PINNED_NODE_ARG = '--node "$(command -v node)"'
NPM_ENV = {"NPM_CONFIG_AUDIT", "NPM_CONFIG_FUND", "NPM_CONFIG_UPDATE_NOTIFIER"}
# The upload allowlist is exactly these six evidence files (never raw reports, attestations or node_modules).
UPLOADS = ["artifacts/sast/hosted-runner-facts.json", "artifacts/sast/container-image.json",
           "artifacts/sast/container-install.json", "artifacts/sast/container-run.json",
           "artifacts/sast/hosted-trial.json", "artifacts/sast/c5-summary.json"]
FORBIDDEN_DOCKER = ("--privileged", "--cap-add", "--network=host", "host", "--pid", "--userns", "unconfined",
                    "--device", "docker.sock", "--volume", "-v", "--security-opt=seccomp", "apparmor")


class Violation(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Violation(message)


def ci_action_pins(ci: dict) -> set[str]:
    return {step["uses"] for job in ci["jobs"].values() for step in job.get("steps", []) if "uses" in step}


def trial_policy(trial: dict, trial_text: str, ci: dict, ci_text: str, node_version: str | None = None) -> None:
    require(set(trial) <= {"name", "on", "permissions", "concurrency", "jobs"}, "Unexpected top-level key")
    require(set(trial["on"]) == {"workflow_dispatch"}, "Trial must be workflow_dispatch only")
    inputs = trial["on"]["workflow_dispatch"].get("inputs", {})
    require(set(inputs) == {"confirm", "authorization_reference"}, "Unexpected dispatch inputs")
    require(all(i.get("required") == "true" and i.get("type") == "string" for i in inputs.values()),
            "Dispatch inputs must be required strings")
    require(trial["permissions"] == {"contents": "read"}, "Trial permissions must be contents: read only")
    require("concurrency" in trial, "Trial must serialize runs")
    for forbidden in ("secrets.", "id-token", "pull_request_target", "security-events", "GITHUB_TOKEN",
                      "continue-on-error", "environment:", "sudo ", "curl ", "wget ", "--privileged",
                      "unshare", "sysctl", "apparmor_parser", "setpriv", "nsenter", "GITHUB_PATH", "GITHUB_ENV",
                      "npx ", "yarn", "pnpm", "npm install", "npm exec", "npm run", "npm i "):
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
    for run in runs:
        for word in ("sudo", "unshare", "sysctl", "apparmor_parser", "setpriv", "nsenter", "--privileged",
                     "curl", "wget", "chmod", "chown"):
            require(not re.search(rf"(^|[\s;&|(]){re.escape(word)}\b", run), f"Forbidden command in step: {word}")
    require(not any(re.search(r"(^|[\s;&|(])docker\b", r) for r in runs),
            "Docker must only be driven by scripts/sast/hosted_trial.py (no raw docker commands)")
    pip_cmds = [line for r in runs for line in r.splitlines() if " -m pip " in line]
    require(len(pip_cmds) == 1 and " -m pip download" in pip_cmds[0], "Workflow may only pip download (install is containerized)")
    for flag in ("--require-hashes", "--no-deps", "--only-binary=:all:", f"-r {LOCK}"):
        require(flag in pip_cmds[0], f"pip download missing {flag}")

    def index(fragment):
        hits = [i for i, r in enumerate(runs) if fragment in r]
        require(len(hits) == 1, f"Expected exactly one step running: {fragment}")
        return hits[0]
    sequence = [index(" -m pip download"), index("hosted_trial.py container-build"),
                index("hosted_trial.py container-install"), index("hosted_trial.py container-run")]
    require(sequence == sorted(sequence), "Steps must run download -> build -> install -> scan")
    # C5-G4H: pinned Node, integrity-verified lockfile install and the TypeScript preflight precede any container.
    want_node = node_version if node_version is not None else NODE_VERSION_FILE.read_text().strip()
    require(re.fullmatch(r"\d+\.\d+\.\d+", want_node), "apps/octocat-supply/.node-version must be an exact version")
    setup = [i for i, s in enumerate(steps) if s.get("uses", "").startswith("actions/setup-node@")]
    require(len(setup) == 1, "Exactly one pinned actions/setup-node step expected")
    require(steps[setup[0]].get("with") == {"node-version": want_node},
            "setup-node must set only node-version equal to apps/octocat-supply/.node-version (no cache/registry/token)")
    npm_lines = [line.strip() for r in runs for line in r.splitlines() if re.search(r"(^|[\s;&|(])npm\b", line)]
    require(npm_lines == [NPM_INSTALL], "The only npm command allowed is a single `npm ci --ignore-scripts`")
    install = index(NPM_INSTALL)
    require(steps[install].get("working-directory") == APP_DIR, "npm ci must run from the application lockfile directory")
    require(set(steps[install].get("env", {})) <= NPM_ENV, "npm ci may only set reviewed NPM_CONFIG_* switches")
    preflight = index("hosted_trial.py typescript-preflight")
    require(PINNED_NODE_ARG in runs[preflight], "TypeScript preflight must use the provisioned node")
    require(PINNED_NODE_ARG in runs[sequence[3]], "container-run must pass the provisioned node to the host gate")
    order = [setup[0], install, preflight, *sequence]
    require(order == sorted(order), "Steps must run setup-node -> npm ci -> TypeScript preflight -> download -> build -> install -> scan")
    require(not any("hosted_trial.py run " in r for r in runs), "Harness must not run outside the container")
    require("--isolation" not in " ".join(runs), "Isolation mode is fixed by the container driver")
    summary = steps[index("hosted_trial.py summarize")]
    require(summary.get("if") == "always()", "Evidence summary must always run")
    upload = [s for s in steps if s.get("uses", "").startswith("actions/upload-artifact@")]
    require(len(upload) == 1 and upload[0].get("if") == "always()", "Evidence upload must always run once")
    paths = [p.strip() for p in upload[0]["with"]["path"].splitlines() if p.strip()]
    require(paths and all(p.startswith("artifacts/sast/") and p.endswith(".json") and "*" not in p for p in paths),
            "Upload must list explicit artifacts/sast/*.json files only")
    require(not any("private" in p for p in paths), "Raw/private reports must never be uploaded")
    require(paths == UPLOADS, "Upload allowlist must be exactly the six reviewed evidence files")
    require(int(upload[0]["with"].get("retention-days", 999)) <= 7, "Evidence retention must be <= 7 days")
    # Non-blocking: the existing release gate is untouched and never depends on the trial.
    require(ci["jobs"]["required"]["needs"] == REQUIRED_NEEDS, "ci.yml required gate changed")
    require(TRIAL_NAME not in ci_text and "hosted-sast-trial" not in ci_text, "ci.yml must not reference the trial")


def container_policy(dockerfile_text: str, hardening: tuple, base: str) -> None:
    lines = [l.strip() for l in dockerfile_text.splitlines() if l.strip() and not l.strip().startswith("#")]
    froms = [l.split()[1] for l in lines if l.startswith("FROM ")]
    require(froms == [BASE_IMAGE] and base == BASE_IMAGE, "Runtime image must use the reviewed amd64 base digest")
    require(not any(l.split()[0] in {"ADD", "COPY", "VOLUME", "EXPOSE", "ENTRYPOINT"} for l in lines),
            "Dockerfile must not ADD/COPY content, declare volumes/ports or entrypoints")
    require(lines[-2:] == ["USER 1001:1001", "WORKDIR /repo"], "Runtime image must end as non-root uid 1001")
    require(re.search(r"^ARG UBUNTU_SNAPSHOT=\d{8}T\d{6}Z$", dockerfile_text, re.M), "APT snapshot must be fixed")
    require('apt-get update --snapshot "$UBUNTU_SNAPSHOT"' in dockerfile_text, "Index must come from the fixed snapshot")
    require(not re.search(r"--allow-unauthenticated|AllowInsecure|trusted=yes|curl|wget|pip ", dockerfile_text),
            "Unauthenticated or non-APT downloads are forbidden in the image")
    installs = re.findall(r"apt-get install[^;]*", dockerfile_text)
    for install in installs:
        names = {w.split("=")[0] for w in install.replace("\\", " ").split() if "=" in w and not w.startswith("-")}
        require('--snapshot "$UBUNTU_SNAPSHOT"' in install or names == {"ca-certificates"},
                "Only pinned ca-certificates may be installed outside the fixed snapshot")
    words = [w for i in installs for w in i.replace("\\", " ").split()]
    packages = [w for w in words if not w.startswith(("-", '"$')) and w not in {"apt-get", "install"}]
    require(packages and all(re.fullmatch(r"[a-z0-9.+-]+=[A-Za-z0-9.+~:-]+", p) for p in packages),
            "Every APT package must be version-pinned")
    pairs = list(zip(hardening, hardening[1:]))
    for pair in REQUIRED_HARDENING:
        require(pair in pairs, f"Container hardening missing {' '.join(pair)}")
    for flag in REQUIRED_FLAGS:
        require(flag in hardening, f"Container hardening missing {flag}")
    require(any(f == "--tmpfs" and "noexec" in v and "nosuid" in v for f, v in pairs), "Writable /tmp must be noexec,nosuid")
    for flag in FORBIDDEN_DOCKER:
        require(not any(flag == h or h.startswith(flag + "=") or (flag in h and flag in {"docker.sock", "unconfined", "apparmor"})
                        for h in hardening), f"Forbidden container option {flag}")


def load_driver():
    sys.path.insert(0, str(ROOT / "scripts/sast"))
    import hosted_trial  # noqa: PLC0415
    return hosted_trial


def main() -> int:
    trial_text, ci_text = TRIAL.read_text(), CI.read_text()
    try:
        trial_policy(yaml.load(trial_text, Loader=yaml.BaseLoader), trial_text,
                     yaml.load(ci_text, Loader=yaml.BaseLoader), ci_text)
        driver = load_driver()
        container_policy(DOCKERFILE.read_text(), tuple(driver.HARDENING), driver.BASE_IMAGE)
    except (Violation, yaml.YAMLError, KeyError, TypeError, ValueError, StopIteration) as exc:
        print(f"FAIL: C5-F4 trial workflow policy: {exc}")
        return 1
    print("PASS: C5-F4R trial workflow is dispatch-only, read-only, pinned, injection-safe, hash-locked, "
          "container-isolated (network none, uid 1001, no caps, no-new-privileges, read-only root), "
          "fail-closed, allowlisted and non-blocking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
