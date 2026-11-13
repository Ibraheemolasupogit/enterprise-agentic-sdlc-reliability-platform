"""C5 local Semgrep CE harness (F1 feasibility, F3 hardening; not a CI gate).

Runs the pinned, locally installed Semgrep CE engine with only the owned rules in
security/sast/rules, inside an environment allowlist and a verified OS network
denial, then validates every report independently of the engine exit code:

* toolchain: manifest, lock, installed distribution set, `pip check`, engine hash;
* controls:  exact catalogue (security/sast/controls.json) of fixture files,
             hashes and expected cases, plus malformed and parser-gap controls;
* source:    every repository file classified; unknown or unsupported
             executable extensions are rejected before scanning.

Exit codes (stable contract):
  0 clean      controls verified, no source findings
  1 findings   controls verified, source findings reported
  2 config     manifest/catalogue/rule/lock/install/inventory/classification error
  3 tool       engine timeout/crash/malformed or incomplete report, parse error
  4 control    a control expectation failed (missed, false positive, drift)
  5 isolation  OS network isolation unavailable or ineffective (no sudo is used)

Raw engine JSON stays in artifacts/sast-private/ (0600). Only an allowlisted
summary is written to artifacts/sast/c5-summary.json. Stdlib only; run with
`python3 -I`. `--emit-catalogue` prints a candidate catalogue for human review.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN = ROOT / "security/sast/toolchain.json"
CATALOGUE = ROOT / "security/sast/controls.json"
FIXTURES = "tests/security/sast/fixtures/"
PRIVATE = ROOT / "artifacts/sast-private/c5"
SUMMARY = ROOT / "artifacts/sast/c5-summary.json"
ENGINE_VERSION = "1.185.0"

EXIT_CLEAN, EXIT_FINDINGS, EXIT_CONFIG, EXIT_TOOL, EXIT_CONTROL, EXIT_ISOLATION = 0, 1, 2, 3, 4, 5
EXIT_NAMES = {0: "clean", 1: "findings", 2: "configuration-error", 3: "tool-error",
              4: "control-failure", 5: "isolation-unavailable"}

SCANNED_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}
# Executable languages the pinned engine/rules do not cover, or cannot target.
UNSUPPORTED_EXECUTABLE = {".mts", ".cts", ".pyw", ".go", ".rb", ".php", ".java", ".kt", ".rs", ".c",
                          ".cc", ".cpp", ".h", ".cs", ".swift", ".pl", ".lua", ".ps1", ".bat", ".cmd",
                          ".vue", ".svelte", ".scala", ".groovy", ".r", ".jl", ".dart", ".ex", ".exs"}
# Reviewed non-code classes: covered by other checks or not executable.
NON_CODE_SUFFIXES = {
    ".md": "documentation", ".txt": "documentation", ".png": "image-asset",
    ".json": "data-config", ".toml": "data-config", ".yaml": "data-config", ".yml": "data-config",
    ".conf": "proxy-config", ".example": "env-template", ".template": "config-template",
    ".css": "web-asset", ".html": "web-markup-outside-ce-claim",
    ".bicep": "iac-outside-ce-claim (C4 validation)", ".kql": "query-outside-ce-claim (C4 validation)",
}
NON_CODE_NAMES = {".dockerignore": "data-config", ".editorconfig": "data-config", ".gitignore": "data-config",
                  ".node-version": "data-config", ".npmrc": "data-config", ".prettierignore": "data-config",
                  "Dockerfile": "container-outside-ce-claim (Trivy config)", "LICENSE": "documentation"}
REVIEWED_SHELL = {"apps/octocat-supply/frontend/start.sh"}
# Generated/installed directories are excluded by explicit name only.
GENERATED_DIRS = {".git", "node_modules", "dist", "coverage", "artifacts", "__pycache__", ".venv",
                  "test-results", "playwright-report"}
GENERATED_PATHS = ("apps/octocat-supply/data/",)
MAX_TARGET_BYTES = 1048576
PROCESS_DEADLINE = 120
ANNOTATION = re.compile(r"^\s*(?://|#)\s*(ruleid|ok|todoruleid):\s*([\w.-]+)\s*$")
CLASSES = [  # Ordered: first matching prefix wins.
    ("runtime-api", "apps/octocat-supply/api/src/"),
    ("runtime-frontend", "apps/octocat-supply/frontend/src/"),
    ("app-test", "apps/octocat-supply/api/test/"),
    ("app-test", "apps/octocat-supply/frontend/test/"),
    ("app-test", "apps/octocat-supply/e2e/"),
    ("app-test", "apps/octocat-supply/test/"),
    ("app-tooling", "apps/octocat-supply/scripts/"),
    ("delivery-python", "scripts/"),
    ("delivery-python", "tests/delivery/"),
    ("sast-tooling-test", "tests/security/sast/"),  # fixtures/ is classified first as controls
]
APP_CONFIG = re.compile(r"^apps/octocat-supply/(frontend/)?[\w.-]+\.config\.(ts|mjs)$")
SANDBOX_PROFILE = "(version 1)(allow default)(deny network*)"
FLAGS = ["scan", "--oss-only", "--metrics=off", "--disable-version-check", "--no-trace",
         "--disable-nosem", "--no-git-ignore", "--no-rewrite-rule-ids", "--strict", "--error",
         "--json", "--time", "--quiet", "--timeout", "30", "--timeout-threshold", "1",
         "--max-memory", "1024", "--jobs", "2", "--max-target-bytes", str(MAX_TARGET_BYTES)]
# Loopback connect inside the isolation wrapper: never leaves the host.
PROBE = ("import errno,socket\ns=socket.socket();s.settimeout(2)\n"
         "try:\n s.connect(('127.0.0.1',9));print('connected')\n"
         "except OSError as e:print(errno.errorcode.get(e.errno,str(e.errno)))\n")
ISOLATED_ERRNOS = {"EPERM", "EACCES", "ENETUNREACH"}
# Verify every installed file that its distribution RECORD hashes (engine, Python
# package code and generated entry scripts). Runs inside the tool venv.
RECORD_CHECK = (
    "import base64,hashlib,json,importlib.metadata as m\n"
    "checked=0;bad=[]\n"
    "for d in m.distributions():\n"
    " for f in d.files or []:\n"
    "  if f.hash is None: continue\n"
    "  try: data=open(f.locate(),'rb').read()\n"
    "  except OSError: bad.append(str(f)); continue\n"
    "  checked+=1\n"
    "  h=base64.urlsafe_b64encode(hashlib.new(f.hash.mode,data).digest()).rstrip(b'=').decode()\n"
    "  if h!=f.hash.value: bad.append(str(f))\n"
    "print(json.dumps({'checked':checked,'bad':bad[:5],'bad_count':len(bad)}))\n")


class Stop(Exception):
    """Fail-closed condition with a fixed, safe reason and an exit class."""

    def __init__(self, code: int, reason: str):
        super().__init__(reason)
        self.code = code


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path, what: str) -> dict:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise Stop(EXIT_CONFIG, f"{what} missing: {path.relative_to(ROOT)}") from exc
    except (ValueError, UnicodeError) as exc:
        raise Stop(EXIT_CONFIG, f"{what} is not valid JSON: {path.relative_to(ROOT)}") from exc
    if not isinstance(data, dict):
        raise Stop(EXIT_CONFIG, f"{what} has an unexpected shape")
    return data


# ---------------------------------------------------------------- inventory
def classify(rel: str, path: Path) -> tuple[str, str]:
    name, suffix = path.name, path.suffix.lower()
    if rel.startswith(FIXTURES):
        return "sast-control-fixture", "controls"
    if suffix == ".sh":
        if rel in REVIEWED_SHELL:
            return "shell-outside-ce-claim", "excluded"
        raise Stop(EXIT_CONFIG, f"unreviewed shell script: {rel}")
    if rel.endswith((".d.mts", ".d.cts")):
        return "type-declaration-outside-ce-claim", "excluded"
    if suffix in UNSUPPORTED_EXECUTABLE:
        raise Stop(EXIT_CONFIG, f"unsupported executable extension {suffix}: {rel}")
    if suffix in SCANNED_SUFFIXES:
        if APP_CONFIG.match(rel):
            return "app-config", "source"
        for cls, prefix in CLASSES:
            if rel.startswith(prefix):
                return cls, "source"
        raise Stop(EXIT_CONFIG, f"unclassified code file: {rel}")
    kind = NON_CODE_NAMES.get(name) if not suffix or name in NON_CODE_NAMES else NON_CODE_SUFFIXES.get(suffix)
    if kind is None:
        raise Stop(EXIT_CONFIG, f"unknown file type (not reviewed): {rel}")
    if path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        raise Stop(EXIT_CONFIG, f"executable bit on non-code file: {rel}")
    with path.open("rb") as handle:
        if handle.read(2) == b"#!":
            raise Stop(EXIT_CONFIG, f"shebang in non-code file: {rel}")
    return f"non-code:{kind}", "non-code"


def inventory() -> dict[str, tuple[str, str]]:
    found = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        for d in dirnames:
            if Path(dirpath, d).is_symlink():
                raise Stop(EXIT_CONFIG, f"symlinked directory: {Path(dirpath, d).relative_to(ROOT)}")
        dirnames[:] = sorted(d for d in dirnames if d not in GENERATED_DIRS)
        for name in sorted(filenames):
            path = Path(dirpath, name)
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(GENERATED_PATHS) or name == ".DS_Store":
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise Stop(EXIT_CONFIG, f"symlink or path escape: {rel}")
            if path.stat().st_size > MAX_TARGET_BYTES and path.suffix.lower() in SCANNED_SUFFIXES:
                raise Stop(EXIT_CONFIG, f"oversize target: {rel}")
            found[rel] = classify(rel, path)
    if not any(mode == "source" for _, mode in found.values()):
        raise Stop(EXIT_CONFIG, "empty source inventory")
    return found


def python_syntax(inv: dict[str, tuple[str, str]]) -> int:
    """Independent stdlib syntax gate: Semgrep error recovery can accept invalid Python."""
    checked = 0
    for rel, (_, mode) in sorted(inv.items()):
        if mode == "source" and rel.endswith(".py"):
            try:
                ast.parse((ROOT / rel).read_bytes(), filename=rel)
            except (SyntaxError, ValueError) as exc:
                raise Stop(EXIT_TOOL, f"python syntax error (ast.parse): {rel}") from exc
            checked += 1
    return checked


# ---------------------------------------------------------------- toolchain
def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def lock_entries(path: Path) -> set[tuple[str, str]]:
    entries = set()
    for line in path.read_text().splitlines():
        match = re.match(r"^([A-Za-z0-9][\w.-]*)==([^\s\\]+)", line)
        if match:
            entries.add((normalise(match.group(1)), match.group(2)))
    return entries


def tool_env(home: Path) -> dict:
    return {"PATH": "/usr/bin:/bin", "HOME": str(home), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_INDEX": "1", "PIP_NO_INPUT": "1",
            "PIP_CONFIG_FILE": os.devnull, "PYTHONNOUSERSITE": "1"}


def preflight(semgrep: Path, home: Path) -> dict:
    manifest = load_json(TOOLCHAIN, "toolchain manifest")
    key = f"{platform.system()}-{platform.machine()}"
    try:
        plat = manifest["engine"]["platforms"].get(key)
        rule_items, rule_ids = manifest["rules"], sorted(manifest["rule_ids"])
        catalogue_sha = manifest["controls_catalogue_sha256"]
    except (KeyError, TypeError, AttributeError) as exc:
        raise Stop(EXIT_CONFIG, "toolchain manifest is missing required fields") from exc
    if not plat:
        raise Stop(EXIT_CONFIG, f"unsupported platform {key}")
    lock = ROOT / plat["lock"]
    if not lock.is_file() or sha256(lock) != plat["lock_sha256"]:
        raise Stop(EXIT_CONFIG, f"lock file changed or missing: {plat['lock']}")
    venv_python = semgrep.parent / "python"
    if not semgrep.is_file() or not venv_python.exists():
        raise Stop(EXIT_CONFIG, "semgrep entry point or its venv python is missing")
    cores = list(semgrep.parent.parent.glob("lib/python3.*/site-packages/semgrep/bin/semgrep-core"))
    if len(cores) != 1 or sha256(cores[0]) != plat["semgrep_core_sha256"]:
        raise Stop(EXIT_CONFIG, "semgrep-core binary hash mismatch or missing")
    check = subprocess.run([str(venv_python), "-I", "-m", "pip", "check"], env=tool_env(home),
                           capture_output=True, text=True, timeout=120, check=False)
    if check.returncode != 0:
        first = (check.stdout or check.stderr).strip().splitlines()[:1]
        raise Stop(EXIT_CONFIG, f"pip check failed (fatal): {first[0] if first else 'no output'}")
    listing = subprocess.run(
        [str(venv_python), "-I", "-c",
         "import importlib.metadata as m,json;print(json.dumps(sorted({(d.metadata['Name'],d.version)"
         " for d in m.distributions()})))"],
        env=tool_env(home), capture_output=True, text=True, timeout=120, check=False)
    try:
        pairs = json.loads(listing.stdout)
        installed = {(normalise(n), v) for n, v in pairs if normalise(n) not in {"pip", "setuptools"}}
    except (ValueError, TypeError) as exc:
        raise Stop(EXIT_CONFIG, "could not list installed distributions") from exc
    expected = lock_entries(lock)
    if installed != expected:
        raise Stop(EXIT_CONFIG, f"installed distributions differ from {plat['lock']} "
                                f"(missing {len(expected - installed)}, unexpected {len(installed - expected)})")
    record = subprocess.run([str(venv_python), "-I", "-c", RECORD_CHECK], env=tool_env(home),
                            capture_output=True, text=True, timeout=300, check=False)
    try:
        verified = json.loads(record.stdout)
    except ValueError as exc:
        raise Stop(EXIT_CONFIG, "installed-file RECORD verification did not complete") from exc
    if verified["bad_count"] or verified["checked"] == 0:
        raise Stop(EXIT_CONFIG, f"installed files differ from their RECORD hashes "
                                f"({verified['bad_count']}): {verified['bad'][:3]}")
    rules = {}
    for item in rule_items:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or sha256(path) != item["sha256"]:
            raise Stop(EXIT_CONFIG, f"rule file changed or missing: {item['path']}")
        rules[item["path"]] = item["sha256"]
    if not CATALOGUE.is_file() or sha256(CATALOGUE) != catalogue_sha:
        raise Stop(EXIT_CONFIG, "controls catalogue changed or missing (hash differs from toolchain manifest)")
    return {"platform": key, "core_sha256": plat["semgrep_core_sha256"], "rules": rules,
            "expected_rule_ids": rule_ids, "distributions": len(installed), "lock": plat["lock"],
            "record_files_verified": verified["checked"]}


# ---------------------------------------------------------------- isolation
def isolation_wrapper() -> tuple[list[str], str]:
    system = platform.system()
    if system == "Darwin":
        if not Path("/usr/bin/sandbox-exec").exists():
            raise Stop(EXIT_ISOLATION, "macOS sandbox-exec not found; refusing to scan")
        return ["/usr/bin/sandbox-exec", "-p", SANDBOX_PROFILE], "macOS sandbox-exec deny network*"
    if system == "Linux":
        unshare = shutil.which("unshare", path="/usr/bin:/bin")
        if not unshare:
            raise Stop(EXIT_ISOLATION, "util-linux unshare not found; refusing to scan")
        if os.geteuid() == 0:
            # Operator chose to run as root; no user namespace is needed. Never escalates itself.
            return [unshare, "--net", "--"], "Linux unshare --net (operator-run as root)"
        return [unshare, "--net", "--map-root-user", "--"], "Linux unshare --net --map-root-user"
    raise Stop(EXIT_ISOLATION, f"no supported OS network isolation on {system}; refusing to scan")


def linux_diagnostics() -> str:
    facts = []
    for label, path in (("max_user_namespaces", "/proc/sys/user/max_user_namespaces"),
                        ("unprivileged_userns_clone", "/proc/sys/kernel/unprivileged_userns_clone"),
                        ("apparmor_restrict_unprivileged_userns",
                         "/proc/sys/kernel/apparmor_restrict_unprivileged_userns")):
        try:
            facts.append(f"{label}={Path(path).read_text().strip()}")
        except OSError:
            facts.append(f"{label}=absent")
    try:
        seccomp = next(line.split(":")[1].strip() for line in Path("/proc/self/status").read_text().splitlines()
                       if line.startswith("Seccomp:"))
        facts.append(f"seccomp_mode={seccomp}")
    except (OSError, StopIteration):
        facts.append("seccomp_mode=unknown")
    facts.append(f"euid={os.geteuid()}")
    facts.append(f"container={'yes' if Path('/.dockerenv').exists() else 'not detected'}")
    return ", ".join(facts)


def verify_isolation(home: Path) -> str:
    wrapper, label = isolation_wrapper()
    try:
        proc = subprocess.run([*wrapper, sys.executable, "-I", "-c", PROBE], env=tool_env(home),
                              capture_output=True, text=True, timeout=30, check=False)
    except subprocess.TimeoutExpired as exc:
        raise Stop(EXIT_ISOLATION, f"{label}: isolation probe timed out") from exc
    result = proc.stdout.strip()
    if proc.returncode != 0 or not result:
        reason = (proc.stderr.strip().splitlines() or ["no diagnostic"])[-1][:160]
        detail = f" [{linux_diagnostics()}]" if platform.system() == "Linux" else ""
        raise Stop(EXIT_ISOLATION, f"{label} could not start ({reason}){detail}. Fail closed: sudo is never "
                                   "invoked automatically; run where unprivileged user namespaces are "
                                   "permitted, or an operator may deliberately run the harness as root")
    if result not in ISOLATED_ERRNOS:
        raise Stop(EXIT_ISOLATION, f"{label} started but loopback probe returned {result}; network not isolated")
    return f"{label}; loopback probe {result}"


# ---------------------------------------------------------------- engine
def pre_python(semgrep: Path) -> str:
    return str(semgrep.parent / "python")


def run_engine(semgrep: Path, targets: list[str], label: str, home: Path, rules: dict) -> dict:
    configs = [arg for path in sorted(rules) for arg in ("--config", str(ROOT / path))]
    wrapper, denial = isolation_wrapper()
    # Run the entry script with the verified venv interpreter, never via its shebang.
    argv = [*wrapper, pre_python(semgrep), "-I", str(semgrep), *FLAGS, *configs, "--", *targets]
    env = {**tool_env(home), "SEMGREP_SETTINGS_FILE": str(home / "settings.yml"), "SEMGREP_SEND_METRICS": "off",
           "SEMGREP_ENABLE_VERSION_CHECK": "0", "XDG_CONFIG_HOME": str(home / "config"),
           "XDG_CACHE_HOME": str(home / "cache"), "NO_COLOR": "1"}
    started = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=PROCESS_DEADLINE, check=False)
    except subprocess.TimeoutExpired as exc:
        raise Stop(EXIT_TOOL, f"{label}: engine exceeded {PROCESS_DEADLINE}s deadline") from exc
    elapsed = time.monotonic() - started
    raw = PRIVATE / f"{label}.json"
    raw.write_bytes(proc.stdout)
    raw.chmod(0o600)
    try:
        report = json.loads(proc.stdout)
    except (ValueError, UnicodeError) as exc:
        raise Stop(EXIT_TOOL, f"{label}: malformed or empty engine JSON (engine exit {proc.returncode})") from exc
    if not isinstance(report, dict) or report.get("version") != ENGINE_VERSION:
        raise Stop(EXIT_TOOL, f"{label}: unexpected report shape or engine version")
    return {"report": report, "exit": proc.returncode, "seconds": round(elapsed, 3), "denial": denial}


def parsed_targets(report: dict) -> set[str]:
    return {t["path"] for t in report.get("time", {}).get("targets", [])
            if any(p > 0 for p in t.get("parse_times", []))}


def validate_complete(result: dict, targets: list[str], expected_ids: list[str], label: str) -> None:
    report = result["report"]
    if report.get("errors"):
        raise Stop(EXIT_TOOL, f"{label}: engine reported {len(report['errors'])} error(s)")
    if report.get("skipped_rules"):
        raise Stop(EXIT_TOOL, f"{label}: engine skipped rules")
    scanned = set(report.get("paths", {}).get("scanned", []))
    if scanned != set(targets):
        raise Stop(EXIT_TOOL, f"{label}: scanned paths differ from expected targets "
                              f"(missing {len(set(targets) - scanned)}, extra {len(scanned - set(targets))})")
    unparsed = set(targets) - parsed_targets(report)
    if unparsed:
        raise Stop(EXIT_TOOL, f"{label}: {len(unparsed)} target(s) were not parsed")
    ran = sorted({r if isinstance(r, str) else r.get("id") for r in report["time"].get("rules", [])})
    if ran != expected_ids:
        raise Stop(EXIT_TOOL, f"{label}: executed rule catalog differs from manifest")
    if result["exit"] not in (0, 1) or (result["exit"] == 1) != bool(report.get("results")):
        raise Stop(EXIT_TOOL, f"{label}: engine exit {result['exit']} contradicts report findings")


def findings(report: dict) -> set[tuple[str, int, str]]:
    return {(r["path"], r["start"]["line"], r["check_id"]) for r in report.get("results", [])}


# ---------------------------------------------------------------- controls
def annotations(path: Path) -> list[tuple[str, str, int]]:
    out = []
    lines = path.read_text().splitlines()
    for number, line in enumerate(lines, 1):
        match = ANNOTATION.match(line)
        if match:
            target = next((n for n in range(number + 1, len(lines) + 1)
                           if lines[n - 1].strip() and not ANNOTATION.match(lines[n - 1])), None)
            if target is None:
                raise Stop(EXIT_CONFIG, f"dangling annotation: {path.relative_to(ROOT)}:{number}")
            out.append((match.group(1), match.group(2), target))
    return out


def fixture_kind(rel: str) -> str:
    if rel.startswith(FIXTURES + "malformed/"):
        return "malformed"
    if rel.startswith(FIXTURES + "parser-gaps/"):
        return "parser-gap"
    suffix = Path(rel).suffix.lower()
    if suffix == ".md":
        return "documentation"
    return "annotated" if suffix in SCANNED_SUFFIXES else "unsupported"


def build_catalogue(inv: dict) -> dict:
    files = sorted(p for p, (cls, _) in inv.items() if cls == "sast-control-fixture")
    cases = [{"path": rel, "line": line, "rule": rule, "expectation": kind}
             for rel in files if fixture_kind(rel) == "annotated"
             for kind, rule, line in annotations(ROOT / rel)]
    gaps = []
    for rel in files:
        if fixture_kind(rel) == "parser-gap":
            native = None
            if rel.endswith(".py"):
                try:
                    ast.parse((ROOT / rel).read_bytes(), filename=rel)
                    native = False
                except SyntaxError:
                    native = True
            # engine_rejected records the reviewed engine behaviour; a harness run reports drift (exit 4).
            gaps.append({"path": rel, "engine_rejected": False, "ast_parse_rejected": native})
    return {"schema": "c5-controls/1",
            "fixtures": [{"path": p, "sha256": sha256(ROOT / p), "kind": fixture_kind(p)} for p in files],
            "cases": cases, "parser_gaps": gaps}


def verify_catalogue(inv: dict, rule_ids: list[str]) -> dict:
    catalogue = load_json(CATALOGUE, "controls catalogue")
    try:
        listed = {f["path"]: f for f in catalogue["fixtures"]}
        expected_cases = catalogue["cases"]
        gap_expectations = {g["path"]: g for g in catalogue["parser_gaps"]}
    except (KeyError, TypeError) as exc:
        raise Stop(EXIT_CONFIG, "controls catalogue is missing required fields") from exc
    on_disk = {p for p, (cls, _) in inv.items() if cls == "sast-control-fixture"}
    missing, extra = sorted(set(listed) - on_disk), sorted(on_disk - set(listed))
    if missing or extra:
        raise Stop(EXIT_CONFIG, f"control fixtures differ from catalogue (missing/renamed {len(missing)}: "
                                f"{missing[:3]}; uncatalogued {len(extra)}: {extra[:3]})")
    altered = sorted(p for p, f in listed.items() if sha256(ROOT / p) != f["sha256"])
    if altered:
        raise Stop(EXIT_CONFIG, f"control fixtures altered since catalogue review: {altered[:3]}")
    kinds = {p: f["kind"] for p, f in listed.items()}
    if any(fixture_kind(p) == "unsupported" for p in kinds):
        raise Stop(EXIT_CONFIG, "control fixture with an unsupported file type")
    if any(kinds[p] != fixture_kind(p) for p in kinds):
        raise Stop(EXIT_CONFIG, "catalogue fixture kinds do not match their locations")
    actual_cases = build_catalogue(inv)["cases"]
    if actual_cases != expected_cases:
        raise Stop(EXIT_CONFIG, "annotated control cases differ from the catalogue")
    unknown = sorted({c["rule"] for c in expected_cases} - set(rule_ids))
    if unknown:
        raise Stop(EXIT_CONFIG, f"catalogue names unknown rules: {unknown}")
    security_rules = [r for r in rule_ids if ".parse-probe." not in r]
    uncovered = [r for r in security_rules
                 if not any(c["rule"] == r and c["expectation"] == "ruleid" for c in expected_cases)]
    if uncovered:
        raise Stop(EXIT_CONFIG, f"security rules without a positive control: {uncovered}")
    if set(gap_expectations) != {p for p, k in kinds.items() if k == "parser-gap"}:
        raise Stop(EXIT_CONFIG, "parser-gap expectations do not match catalogued parser-gap fixtures")
    return {"catalogue": catalogue, "kinds": kinds, "gaps": gap_expectations}


def run_controls(semgrep: Path, home: Path, pre: dict, cat: dict) -> dict:
    kinds = cat["kinds"]
    annotated = sorted(p for p, k in kinds.items() if k == "annotated")
    malformed = sorted(p for p, k in kinds.items() if k == "malformed")
    gaps = sorted(p for p, k in kinds.items() if k == "parser-gap")
    result = run_engine(semgrep, annotated, "controls", home, pre["rules"])
    validate_complete(result, annotated, pre["expected_rule_ids"], "controls")
    actual = findings(result["report"])
    cases, expected_hits = [], set()
    for case in cat["catalogue"]["cases"]:
        key = (case["path"], case["line"], case["rule"])
        hit = key in actual
        if case["expectation"] == "ruleid":
            expected_hits.add(key)
            outcome = "detected" if hit else "MISSED"
        elif case["expectation"] == "ok":
            outcome = "FALSE-POSITIVE" if hit else "clean"
        else:
            if hit:
                expected_hits.add(key)
            outcome = "UNEXPECTEDLY-DETECTED" if hit else "known-miss"
        cases.append({**case, "outcome": outcome})
    unexpected = sorted(actual - expected_hits)
    bad = run_engine(semgrep, malformed, "malformed", home, pre["rules"])
    if bad["report"].get("results"):
        raise Stop(EXIT_CONTROL, "malformed controls produced findings instead of parse errors")
    parse_error_paths = {e.get("path") for e in bad["report"].get("errors", [])
                         if "PartialParsing" in json.dumps(e.get("type")) or "Syntax error" in str(e.get("message", ""))}
    malformed_ok = bad["exit"] not in (0, 1) and set(malformed) <= parse_error_paths
    gap = run_engine(semgrep, gaps, "parser-gaps", home, pre["rules"])
    engine_rejected = {e.get("path") for e in gap["report"].get("errors", [])}
    gap_rows, gap_drift = [], []
    for rel in gaps:
        native = None
        if rel.endswith(".py"):
            try:
                ast.parse((ROOT / rel).read_bytes(), filename=rel)
                native = False
            except SyntaxError:
                native = True
        row = {"path": rel, "engine_rejected": rel in engine_rejected, "ast_parse_rejected": native}
        gap_rows.append(row)
        want = cat["gaps"][rel]
        if row["engine_rejected"] != want["engine_rejected"] or row["ast_parse_rejected"] != want["ast_parse_rejected"]:
            gap_drift.append(rel)
    failed = [c for c in cases if c["outcome"] not in {"detected", "clean", "known-miss"}]
    status = "pass" if not failed and not unexpected and malformed_ok and not gap_drift else "FAIL"
    return {"status": status, "catalogue_sha256": sha256(CATALOGUE), "fixtures": len(kinds),
            "annotated_targets": len(annotated), "exit": result["exit"], "seconds": result["seconds"],
            "network_denial": result["denial"], "cases": cases, "failed_cases": len(failed),
            "unexpected_findings": [{"path": p, "line": n, "rule": r} for p, n, r in unexpected],
            "malformed": {"targets": malformed, "exit": bad["exit"], "rejected": sorted(parse_error_paths),
                          "all_rejected": malformed_ok, "seconds": bad["seconds"]},
            "parser_gaps": gap_rows, "parser_gap_drift": gap_drift}


# ---------------------------------------------------------------- source
def run_source(semgrep: Path, home: Path, pre: dict, inv: dict, repeat: int) -> dict:
    targets = sorted(p for p, (_, mode) in inv.items() if mode == "source")
    runs = []
    for index in range(repeat):
        result = run_engine(semgrep, targets, f"source-{index + 1}", home, pre["rules"])
        validate_complete(result, targets, pre["expected_rule_ids"], "source")
        runs.append(result)
    first = runs[0]
    hits = sorted(findings(first["report"]))
    if any(sorted(findings(r["report"])) != hits for r in runs[1:]):
        raise Stop(EXIT_TOOL, "source: findings differ between repeated runs")
    counts: dict[str, int] = {}
    for cls, mode in inv.values():
        if mode == "source":
            counts[cls] = counts.get(cls, 0) + 1
    return {"status": "clean" if not hits else "findings", "targets": len(targets),
            "classes": dict(sorted(counts.items())), "exit": first["exit"],
            "findings": [{"path": p, "line": n, "rule": r, "class": inv[p][0]} for p, n, r in hits],
            "wall_seconds": [r["seconds"] for r in runs],
            "max_memory_bytes": first["report"]["time"].get("max_memory_bytes"),
            "total_bytes": first["report"]["time"].get("total_bytes"), "network_denial": first["denial"],
            "source_sha256sum": [f"{sha256(ROOT / p)}  {p}" for p in targets]}


def summarise(inv: dict) -> dict:
    classes: dict[str, int] = {}
    for cls, _ in inv.values():
        classes[cls] = classes.get(cls, 0) + 1
    return {"total_files": len(inv), "classes": dict(sorted(classes.items())),
            "excluded_outside_claim": sorted(p for p, (_, mode) in inv.items() if mode == "excluded")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--semgrep", type=Path, help="semgrep entry point in the verified venv")
    parser.add_argument("--repeat", type=int, default=3, help="source scan repetitions for timing")
    parser.add_argument("--emit-catalogue", action="store_true",
                        help="print a candidate controls catalogue for human review and exit (writes nothing)")
    args = parser.parse_args()
    try:
        if args.emit_catalogue:
            print(json.dumps(build_catalogue(inventory()), indent=2))
            return EXIT_CLEAN
        if args.semgrep is None:
            raise Stop(EXIT_CONFIG, "--semgrep is required")
        semgrep = args.semgrep.absolute()
        PRIVATE.mkdir(parents=True, exist_ok=True)
        PRIVATE.chmod(0o700)
        with tempfile.TemporaryDirectory(prefix="semgrep-home-") as tmp:
            home = Path(tmp)
            pre = preflight(semgrep, home)
            inv = inventory()
            cat = verify_catalogue(inv, pre["expected_rule_ids"])
            py_checked = python_syntax(inv)
            isolation = verify_isolation(home)
            controls = run_controls(semgrep, home, pre, cat)
            if controls["status"] != "pass":
                code = EXIT_CONTROL
                source = None
            else:
                source = run_source(semgrep, home, pre, inv, max(1, args.repeat))
                code = EXIT_CLEAN if source["status"] == "clean" else EXIT_FINDINGS
    except Stop as stop:
        print(f"STOP [{stop.code} {EXIT_NAMES[stop.code]}]: {stop}")
        return stop.code
    summary = {
        "schema": "c5-summary/2", "engine": "semgrep-ce", "version": ENGINE_VERSION, "result": EXIT_NAMES[code],
        "exit": code, "platform": pre["platform"], "python": platform.python_version(),
        "semgrep_core_sha256": pre["core_sha256"], "rules_sha256": pre["rules"], "rule_ids": pre["expected_rule_ids"],
        "toolchain": {"lock": pre["lock"], "distributions_match_lock": pre["distributions"], "pip_check": "pass",
                      "record_files_verified": pre["record_files_verified"]},
        "isolation": isolation, "flags": FLAGS, "inventory": summarise(inv),
        "python_ast_syntax_gate": {"checked": py_checked, "status": "pass"}, "controls": controls, "source": source,
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    passed = sum(c["outcome"] in {"detected", "clean"} for c in controls["cases"])
    misses = sum(c["outcome"] == "known-miss" for c in controls["cases"])
    print(f"isolation: {isolation}")
    print(f"toolchain: {pre['distributions']} distributions match {pre['lock']}; pip check pass; "
          f"{pre['record_files_verified']} installed files match RECORD hashes")
    print(f"inventory: {summary['inventory']['total_files']} files classified; ast gate {py_checked} python files")
    print(f"controls: {controls['status']} ({passed}/{len(controls['cases'])} as expected, {misses} known misses, "
          f"{controls['fixtures']} catalogued fixtures, malformed rejected={controls['malformed']['all_rejected']}, "
          f"parser-gap drift={len(controls['parser_gap_drift'])})")
    if source:
        print(f"source: {source['status']} ({source['targets']} targets, {len(source['findings'])} findings, "
              f"wall seconds {source['wall_seconds']})")
        for item in source["findings"]:
            print(f"  finding {item['rule']} at {item['path']}:{item['line']} [{item['class']}]")
    print(f"result: {code} {EXIT_NAMES[code]}; summary {SUMMARY.relative_to(ROOT)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
