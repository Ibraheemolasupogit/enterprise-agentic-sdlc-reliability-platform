"""C5-G2 mitigation regression guard (local; not in CI discovery; no engine needed).

The owner's conditional G2 acceptance (docs/evidence/m4c-c5-g2-dependency-assessment.md)
relies on the scanner never enabling tracing, metrics, MCP or registry/Pro
features, and never inheriting operational credentials. This module pins those
properties at the point where the harness builds the engine process:

* the exact Semgrep flag list and the subcommand (``scan``);
* the exact engine and tool environment allowlist and its fixed values;
* the absence of any inherited variable even when the caller's environment is
  hostile (tokens, OTLP endpoint, trace parent, proxies, PYTHONPATH...);
* the only configs being the two catalogued local rule files;
* the hosted driver forwarding only named, non-secret variables into the container.

Negative tests mutate a disposable copy of the harness source and prove that each
drift is rejected. Subprocesses are intercepted; nothing is executed.
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
HARNESS = ROOT / "scripts/sast/feasibility.py"
sys.path.insert(0, str(ROOT / "scripts/sast"))
import hosted_trial as driver  # noqa: E402

# ------------------------------------------------------------------ G2 policy (pinned)
EXPECTED_FLAGS = (
    "scan", "--oss-only", "--metrics=off", "--disable-version-check", "--no-trace",
    "--disable-nosem", "--no-git-ignore", "--no-rewrite-rule-ids", "--strict", "--error",
    "--json", "--time", "--quiet", "--timeout", "30", "--timeout-threshold", "1",
    "--max-memory", "1024", "--jobs", "2", "--max-target-bytes")
G2_REQUIRED_FLAGS = ("--oss-only", "--metrics=off", "--disable-version-check", "--no-trace")
# Any of these anywhere in the engine argv enables tracing, metrics, MCP, login,
# registry rules, Pro/AppSec-platform features or network fetches.
FORBIDDEN_ARGS = re.compile(
    r"^(mcp|login|logout|ci|publish|install-semgrep-pro|lsp|show|--trace(-endpoint)?(=.*)?|--metrics(=(on|auto).*)?"
    r"|--enable-version-check|--pro.*|--secrets|--compute-secret-hash|--supply-chain|--allow-untrusted-validators|--dryrun"
    r"|--config=.*|auto|p/.*|r/.*|https?://.*|--use-git-ignore|--x-.*)$")
TOOL_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1", "PIP_NO_INPUT": "1", "PIP_CONFIG_FILE": os.devnull, "PYTHONNOUSERSITE": "1"}
ENGINE_FIXED = {"SEMGREP_SEND_METRICS": "off", "SEMGREP_ENABLE_VERSION_CHECK": "0", "NO_COLOR": "1"}
ENGINE_HOME_RELATIVE = {"SEMGREP_SETTINGS_FILE": "settings.yml", "XDG_CONFIG_HOME": "config", "XDG_CACHE_HOME": "cache"}
ENGINE_KEYS = frozenset({"HOME", *TOOL_ENV, *ENGINE_FIXED, *ENGINE_HOME_RELATIVE})
RULE_FILES = ("security/sast/rules/python.yml", "security/sast/rules/typescript.yml")
ALLOWED_WRAPPERS = ((), ("/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)"))
UNSHARE = re.compile(r"^/(usr/)?bin/unshare$")
CONTAINER_ENV_NAMES = frozenset({*driver.CONTEXT_KEYS, "TRIAL_AUTHORIZATION_REFERENCE", "C5_TRIAL_NONCE"})
SECRETISH = re.compile(r"TOKEN|SECRET|PASSW|CREDENTIAL|_KEY$|^AUTH|OTEL|SEMGREP_APP|SEMGREP_TRACE|SEMGREP_METRICS_URL|MCP|PROXY|"
                       r"^AWS_|^AZURE_|^ARM_|^ACTIONS_|PYTHON(PATH|STARTUP|HOME)", re.I)
# Hostile caller environment: none of this may reach the engine or the container.
HOSTILE = {
    "GITHUB_TOKEN": "C5G2CANARY", "GH_TOKEN": "C5G2CANARY", "SEMGREP_APP_TOKEN": "C5G2CANARY",
    "SEMGREP_APP_URL": "https://c5g2.invalid", "SEMGREP_METRICS_URL": "https://c5g2.invalid",  # read since 1.186.0
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://c5g2.invalid",
    "OTEL_TRACES_EXPORTER": "otlp", "OTEL_RESOURCE_ATTRIBUTES": "c5g2=1", "SEMGREP_TRACE_PARENT_TRACE_ID": "1" * 32,
    "SEMGREP_TRACE_PARENT_SPAN_ID": "2" * 16, "SEMGREP_SEND_METRICS": "on", "SEMGREP_ENABLE_VERSION_CHECK": "1",
    "SEMGREP_SETTINGS_FILE": "/c5g2/settings.yml", "SEMGREP_MCP_TOKEN": "C5G2CANARY", "HTTPS_PROXY": "http://c5g2.invalid",
    "PYTHONPATH": "/c5g2", "PYTHONSTARTUP": "/c5g2/x.py", "AZURE_CLIENT_SECRET": "C5G2CANARY",
    "AWS_SECRET_ACCESS_KEY": "C5G2CANARY", "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "C5G2CANARY",
    "ACTIONS_RUNTIME_TOKEN": "C5G2CANARY", "PATH": "/c5g2/bin:/usr/bin:/bin", "HOME": "/c5g2/home"}
# Caller environment for harness mutations: a canary value plus a caller PATH that always differs from the pinned tool
# PATH, so mutations that inherit the caller's environment are detectable whatever PATH the test itself runs with.
CALLER_PATH = HOSTILE["PATH"]
MUTATION_CALLER_ENV = {"X": "C5G2CANARY", "PATH": CALLER_PATH}


class Drift(AssertionError):
    pass


def check_engine(argv: list[str], env: dict, root: Path, home: Path, semgrep: Path) -> None:
    """Raise Drift unless the engine invocation satisfies the pinned G2 policy."""
    argv = list(argv)
    if "--" not in argv:
        raise Drift("no '--' separator before targets")
    sep = len(argv) - 1 - argv[::-1].index("--")  # the target separator (Linux unshare wrappers end with their own --)
    head, targets = argv[:sep], argv[sep + 1:]
    for arg in head:
        if FORBIDDEN_ARGS.match(arg):
            raise Drift(f"forbidden engine argument {arg!r}")
    try:
        start = head.index(str(semgrep.parent / "python"))
    except ValueError as exc:
        raise Drift("engine not run with the verified venv interpreter") from exc
    wrapper = tuple(head[:start])
    if wrapper not in ALLOWED_WRAPPERS and not (
            len(wrapper) >= 3 and UNSHARE.match(wrapper[0]) and wrapper[1] == "--net" and wrapper[-1] == "--"):
        raise Drift(f"unexpected isolation wrapper {wrapper!r}")
    if head[start + 1:start + 3] != ["-I", str(semgrep)]:
        raise Drift("interpreter not in isolated mode (-I) or wrong entry script")
    rest = head[start + 3:]
    flags = tuple(rest[:len(EXPECTED_FLAGS)])
    if flags != EXPECTED_FLAGS:
        raise Drift(f"Semgrep flags drifted: {flags!r}")
    if not rest[len(EXPECTED_FLAGS)].isdigit():
        raise Drift("--max-target-bytes value missing")
    configs = rest[len(EXPECTED_FLAGS) + 1:]
    expected_configs = [a for p in RULE_FILES for a in ("--config", str(root / p))]
    if configs != expected_configs:
        raise Drift(f"configs drifted: {configs!r}")
    missing = [f for f in G2_REQUIRED_FLAGS if f not in head]
    if missing:
        raise Drift(f"G2 flags missing: {missing}")
    if not targets or any(t.startswith("-") for t in targets):
        raise Drift("targets missing or contain options")
    if set(env) != ENGINE_KEYS:
        raise Drift(f"engine environment keys drifted: extra={sorted(set(env) - ENGINE_KEYS)} "
                    f"missing={sorted(ENGINE_KEYS - set(env))}")
    for key, value in {**TOOL_ENV, **ENGINE_FIXED}.items():
        if env[key] != value:
            raise Drift(f"{key} drifted")
    if Path(env["HOME"]) != home:
        raise Drift("HOME is not the per-run scratch home")
    for key, rel in ENGINE_HOME_RELATIVE.items():
        if Path(env[key]) != home / rel:
            raise Drift(f"{key} is outside the per-run scratch home")
    leaked = [k for k, v in env.items() if SECRETISH.search(k) or "C5G2" in v]
    if leaked:
        raise Drift(f"credential-like or hostile values reached the engine: {leaked}")


def check_tool_env(env: dict, home: Path) -> None:
    if set(env) != {"HOME", *TOOL_ENV} or Path(env["HOME"]) != home:
        raise Drift(f"tool environment drifted: {sorted(env)}")
    for key, value in TOOL_ENV.items():
        if env[key] != value:
            raise Drift(f"{key} drifted")


_COPIES: list[tempfile.TemporaryDirectory] = []  # disposable mutated harness copies


def tearDownModule():
    for tmp in _COPIES:
        tmp.cleanup()
    _COPIES.clear()


def load_harness(source: str | None = None, tag: str = "g2"):
    """Load the real harness, or a mutated copy placed at the same relative path in a temp tree."""
    if source is None:
        path = HARNESS
    else:
        tmp = tempfile.TemporaryDirectory(prefix="c5-g2-")
        _COPIES.append(tmp)
        path = Path(tmp.name) / "scripts/sast/feasibility.py"
        path.parent.mkdir(parents=True)
        path.write_text(source)
    spec = importlib.util.spec_from_file_location(f"c5_g2_{tag}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_engine(module, isolation: str = "container", environ: dict | None = None):
    """Run the harness's real run_engine with subprocess intercepted; return (argv, env, home, semgrep)."""
    seen = {}
    with tempfile.TemporaryDirectory(prefix="semgrep-home-") as tmp:
        home = Path(tmp)
        semgrep = home / "venv/bin/semgrep"

        def fake_run(argv, **kwargs):
            seen["argv"], seen["env"] = list(argv), dict(kwargs["env"])
            return subprocess.CompletedProcess(argv, 0, json.dumps({"version": module.ENGINE_VERSION}).encode(), b"")
        with mock.patch.object(module, "ISOLATION_MODE", isolation), \
                mock.patch.object(module, "PRIVATE", home / "private"), \
                mock.patch.object(module.subprocess, "run", side_effect=fake_run), \
                mock.patch.dict(os.environ, environ or {}, clear=False):
            (home / "private").mkdir()
            module.run_engine(semgrep, ["apps/a.ts"], "g2", home, {p: "x" for p in reversed(RULE_FILES)})
            tool = module.tool_env(home)
        return seen["argv"], seen["env"], home, semgrep, tool


class PositivePolicy(unittest.TestCase):
    """The current harness and driver satisfy the pinned G2 policy."""

    def test_flags_constant_is_exactly_pinned(self):
        harness = load_harness(tag="flags")
        self.assertEqual(tuple(harness.FLAGS[:-1]), EXPECTED_FLAGS)
        self.assertEqual(harness.FLAGS[-1], str(harness.MAX_TARGET_BYTES))
        self.assertEqual(harness.FLAGS[0], "scan")
        for flag in G2_REQUIRED_FLAGS:
            self.assertEqual(harness.FLAGS.count(flag), 1, flag)

    def test_engine_invocation_container_mode(self):
        # Deterministic caller environment (C5-U1C): with an inherited caller PATH equal to the pin, a harness that
        # forwards the caller's PATH would be indistinguishable from one that pins it.
        harness = load_harness(tag="container")
        argv, env, home, semgrep, tool = capture_engine(harness, environ=MUTATION_CALLER_ENV)
        self.assertNotEqual(CALLER_PATH, TOOL_ENV["PATH"])
        self.assertEqual(tool["PATH"], TOOL_ENV["PATH"])
        self.assertEqual(env["PATH"], TOOL_ENV["PATH"])
        check_engine(argv, env, harness.ROOT, home, semgrep)
        check_tool_env(tool, home)

    def test_pinned_path_ignores_distinct_caller_path(self):
        """Control for the PATH mutation: the unmutated harness keeps the pinned PATH under a distinct caller PATH."""
        harness = load_harness(tag="caller_path")
        argv, env, home, semgrep, tool = capture_engine(harness, environ=MUTATION_CALLER_ENV)
        self.assertEqual(tool["PATH"], TOOL_ENV["PATH"])
        self.assertEqual(env["PATH"], TOOL_ENV["PATH"])
        check_tool_env(tool, home)
        check_engine(argv, env, harness.ROOT, home, semgrep)

    def test_engine_invocation_platform_wrapper(self):
        harness = load_harness(tag="auto")
        try:
            argv, env, home, semgrep, _ = capture_engine(harness, isolation="auto")
        except harness.Stop as exc:  # unsupported OS: harness refuses to scan (fail closed)
            self.assertEqual(exc.code, harness.EXIT_ISOLATION)
            return
        check_engine(argv, env, harness.ROOT, home, semgrep)
        self.assertNotEqual(tuple(argv[:argv.index(str(semgrep.parent / "python"))]), ())

    def test_hostile_caller_environment_never_reaches_engine(self):
        harness = load_harness(tag="hostile")
        argv, env, home, semgrep, tool = capture_engine(harness, environ=HOSTILE)
        check_engine(argv, env, harness.ROOT, home, semgrep)
        check_tool_env(tool, home)
        joined = json.dumps([argv, env, tool])
        self.assertNotIn("C5G2", joined)
        self.assertNotIn("c5g2", joined)
        self.assertEqual(env["SEMGREP_SEND_METRICS"], "off")
        self.assertEqual(env["PATH"], "/usr/bin:/bin")

    def test_cli_has_no_engine_flag_or_environment_passthrough(self):
        harness = load_harness(tag="cli")
        for extra in (["--trace"], ["--metrics=on"], ["mcp"], ["--", "--trace"], ["--config", "auto"],
                      ["--flags", "--trace"], ["--env", "SEMGREP_APP_TOKEN=x"]):
            with self.subTest(extra=extra), mock.patch.object(sys, "argv", ["feasibility.py", *extra]), \
                    mock.patch("sys.stderr"), self.assertRaises(SystemExit) as ctx:
                harness._main()
            self.assertEqual(ctx.exception.code, 2)
        self.assertNotIn("os.environ", HARNESS.read_text().split("def tool_env", 1)[1].split("\ndef ", 1)[0])

    def test_driver_forwards_only_named_non_secret_variables(self):
        self.assertFalse([k for k in driver.CONTEXT_KEYS if SECRETISH.search(k)])
        captured = {}

        def fake(argv, **kwargs):
            captured["argv"] = argv
            return subprocess.CompletedProcess(argv, 0, "", "")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "iid").write_text("sha256:" + "a" * 64)
            (base / "venv").mkdir()
            with mock.patch.object(driver.subprocess, "run", side_effect=fake), \
                    mock.patch.object(driver, "ROOT", base), \
                    mock.patch.object(driver, "OUT", base / "artifacts/sast"), \
                    mock.patch.object(driver, "TRIAL", base / "artifacts/sast/hosted-trial.json"), \
                    mock.patch.object(driver, "RUN_EVIDENCE", base / "artifacts/sast/container-run.json"), \
                    mock.patch.object(driver.shutil, "which", return_value="/usr/bin/docker"), \
                    mock.patch.dict(os.environ, HOSTILE), mock.patch("builtins.print"):
                driver.container_run(str(base / "iid"), str(base / "venv"), 1)
        argv = captured["argv"]
        names = {argv[i + 1] for i, a in enumerate(argv) if a == "--env"}
        self.assertEqual(names, CONTAINER_ENV_NAMES)
        self.assertNotIn("C5G2", " ".join(argv))
        command = argv[argv.index("-I") + 1:]
        self.assertEqual(command[:7], ["/repo/scripts/sast/hosted_trial.py", "run", "--isolation", "container",
                                       "--semgrep", "/opt/sast/bin/semgrep", "--repeat"])


class NegativePolicy(unittest.TestCase):
    """Each drift or unsafe override, applied to a disposable copy, is rejected."""

    SOURCE = HARNESS.read_text()
    MUTATIONS = {
        "tracing enabled (--no-trace removed)": ('"--no-trace",', ""),
        "tracing endpoint added": ('"--no-trace",', '"--trace", "--trace-endpoint", "semgrep-prod",'),
        "metrics on": ('"--metrics=off"', '"--metrics=on"'),
        "version check on": ('"--disable-version-check", ', ""),
        "oss-only removed": ('"--oss-only", ', ""),
        "pro engine": ('"--oss-only",', '"--oss-only", "--pro",'),
        "mcp subcommand": ('FLAGS = ["scan",', 'FLAGS = ["mcp",'),
        "registry config": ('*FLAGS, *configs,', '*FLAGS, "--config", "auto", *configs,'),
        "interpreter not isolated": ('pre_python(semgrep), "-I", str(semgrep)', 'pre_python(semgrep), str(semgrep)'),
        "inherits caller environment": ('env = {**tool_env(home),', 'env = {**os.environ, **tool_env(home),'),
        "engine metrics env on": ('"SEMGREP_SEND_METRICS": "off"', '"SEMGREP_SEND_METRICS": "on"'),
        "real user settings (stored login token)": ('"SEMGREP_SETTINGS_FILE": str(home / "settings.yml")',
                                                    '"SEMGREP_SETTINGS_FILE": str(Path.home() / ".semgrep/settings.yml")'),
        "app token forwarded": ('"NO_COLOR": "1"}', '"NO_COLOR": "1", "SEMGREP_APP_TOKEN": os.environ.get("X", "")}'),
        "otel endpoint forwarded": ('"NO_COLOR": "1"}', '"NO_COLOR": "1", "OTEL_EXPORTER_OTLP_ENDPOINT": "http://x"}'),
        "tool PATH widened": ('{"PATH": "/usr/bin:/bin",', '{"PATH": os.environ.get("PATH", ""),'),
        "tool env inherits token": ('"PYTHONNOUSERSITE": "1"}', '"PYTHONNOUSERSITE": "1", "GITHUB_TOKEN": "x"}'),
        # Semgrep 1.186.0 surfaces (C5-U1): a configurable metrics endpoint and secret-hash computation.
        "metrics endpoint redirected": ('"NO_COLOR": "1"}', '"NO_COLOR": "1", "SEMGREP_METRICS_URL": "https://x"}'),
        "secret hash computation enabled": ('"--oss-only",', '"--oss-only", "--compute-secret-hash",'),
        "isolation wrapper weakened": ('SANDBOX_PROFILE = "(version 1)(allow default)(deny network*)"',
                                       'SANDBOX_PROFILE = "(version 1)(allow default)"'),
    }

    def test_every_mutation_is_rejected(self):
        # The caller environment is fixed here, never inherited: a PATH-inheriting mutation is only observable when the
        # caller's PATH differs from the pin (C5-U1C: under `env -i PATH=/usr/bin:/bin` the check was vacuous).
        self.assertNotEqual(CALLER_PATH, TOOL_ENV["PATH"])
        rejected = 0
        for name, (old, new) in self.MUTATIONS.items():
            isolation = "auto" if "wrapper" in name else "container"
            if isolation == "auto" and sys.platform != "darwin":
                continue  # the sandbox-exec profile applies on macOS only; Linux wrappers are pinned by shape
            with self.subTest(mutation=name):
                self.assertEqual(self.SOURCE.count(old), 1, f"mutation anchor not unique: {old!r}")
                mutated = self.SOURCE.replace(old, new)
                self.assertNotEqual(mutated, self.SOURCE)
                harness = load_harness(mutated, tag=re.sub(r"\W", "_", name))
                argv, env, home, semgrep, tool = capture_engine(harness, isolation, environ=MUTATION_CALLER_ENV)
                if name == "tool PATH widened":
                    # Non-vacuity: the mutation must really change PATH to the caller's value, away from the pin.
                    self.assertEqual(tool["PATH"], CALLER_PATH)
                    self.assertNotEqual(tool["PATH"], TOOL_ENV["PATH"])
                    self.assertNotEqual(env["PATH"], TOOL_ENV["PATH"])
                with self.assertRaises(Drift):
                    check_tool_env(tool, home)
                    check_engine(argv, env, harness.ROOT, home, semgrep)
                rejected += 1
        self.assertGreaterEqual(rejected, len(self.MUTATIONS) - 1)

    def test_policy_rejects_synthetic_overrides(self):
        harness = load_harness(tag="synthetic")
        argv, env, home, semgrep, _ = capture_engine(harness)
        sep = argv.index("--")
        cases = {
            "trace flag appended": (argv[:sep] + ["--trace"] + argv[sep:], env),
            "metrics auto": ([a if a != "--metrics=off" else "--metrics=auto" for a in argv], env),
            "mcp as target-less command": ([a if a != "scan" else "mcp" for a in argv], env),
            "login": (argv[:sep] + ["login"] + argv[sep:], env),
            "registry pack": (argv[:sep] + ["--config", "p/default"] + argv[sep:], env),
            "url config": (argv[:sep] + ["--config", "https://c5g2.invalid/r.yml"] + argv[sep:], env),
            "option smuggled as target": (argv + ["--trace"], env),
            "no separator": ([a for a in argv if a != "--"], env),
            "duplicate config": (argv[:sep] + ["--config", argv[sep - 1]] + argv[sep:], env),
            "github token": (argv, {**env, "GITHUB_TOKEN": "x"}),
            "app token": (argv, {**env, "SEMGREP_APP_TOKEN": "x"}),
            "otlp endpoint": (argv, {**env, "OTEL_EXPORTER_OTLP_ENDPOINT": "http://x"}),
            "trace parent": (argv, {**env, "SEMGREP_TRACE_PARENT_TRACE_ID": "1" * 32}),
            "proxy": (argv, {**env, "HTTPS_PROXY": "http://x"}),
            "metrics env on": (argv, {**env, "SEMGREP_SEND_METRICS": "on"}),
            "metrics endpoint override (1.186.0)": (argv, {**env, "SEMGREP_METRICS_URL": "http://x"}),
            "secret hash flag (1.186.0)": (argv[:sep] + ["--compute-secret-hash"] + argv[sep:], env),
            "version check env on": (argv, {**env, "SEMGREP_ENABLE_VERSION_CHECK": "1"}),
            "PATH widened": (argv, {**env, "PATH": "/opt/x:/usr/bin:/bin"}),
            "real HOME": (argv, {**env, "HOME": os.path.expanduser("~")}),
            "settings outside home": (argv, {**env, "SEMGREP_SETTINGS_FILE": "/tmp/settings.yml"}),
            "allowlisted key removed": (argv, {k: v for k, v in env.items() if k != "SEMGREP_SEND_METRICS"}),
        }
        for name, (bad_argv, bad_env) in cases.items():
            with self.subTest(case=name), self.assertRaises(Drift):
                check_engine(bad_argv, bad_env, harness.ROOT, home, semgrep)


if __name__ == "__main__":
    unittest.main()
