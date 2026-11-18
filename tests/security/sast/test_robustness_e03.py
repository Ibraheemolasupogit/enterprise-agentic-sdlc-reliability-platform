"""C5 E03 robustness tests: M11 failure handling, M12 forged reports, M14 canary capture.

Local only (not in CI discovery). Requires the verified Semgrep venv:
  C5_SEMGREP=/path/to/venv/bin/semgrep [C5_ISOLATION=container] \
    python3 -m unittest tests.security.sast.test_robustness_e03   (or discover -s tests/security/sast)

Each test class works on a disposable copy of the repository. The REAL harness runs
end to end (real preflight, toolchain/RECORD checks, inventory, catalogue, isolation
and real Semgrep). Only the engine's process result is intercepted and broken or forged
after the real engine produced it, so the harness's own validators must reject it.
Without C5_SEMGREP the tests are skipped explicitly (never silently passed).
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest import mock
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEMGREP = os.environ.get("C5_SEMGREP")
ISOLATION = os.environ.get("C5_ISOLATION", "auto")
SKIP = unittest.skipUnless(SEMGREP and Path(SEMGREP).is_file(), "C5_SEMGREP not set: real-engine E03 tests skipped")
IGNORE = shutil.ignore_patterns(".git", "node_modules", "dist", "coverage", "artifacts", "__pycache__", ".venv",
                                "test-results", "playwright-report", ".DS_Store")


def disposable_copy(test_case):
    tmp = tempfile.TemporaryDirectory(prefix="c5-e03-")
    test_case.addClassCleanup(tmp.cleanup)
    root = Path(tmp.name) / "repo"
    shutil.copytree(REPO, root, ignore=IGNORE, symlinks=True)
    data = root / "apps/octocat-supply/data"
    if data.exists():
        shutil.rmtree(data)
    return root


def load(root, name):
    spec = importlib.util.spec_from_file_location(f"{name}_{uuid.uuid4().hex}", root / "scripts/sast" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def label_of(argv):
    text = " ".join(map(str, argv))
    if "fixtures/malformed/" in text:
        return "malformed"
    if "fixtures/parser-gaps/" in text:
        return "parser-gaps"
    if "tests/security/sast/fixtures/" in text:
        return "controls"
    return "source"


def typescript_gate_args(module):
    """C5-G4: disposable copies have no node_modules. Auto mode points the harness at the real, hash-verified
    compiler; container mode (no Node) installs a host attestation given by C5_TS_ATTESTATION into the copy."""
    if ISOLATION == "container":
        source = os.environ.get("C5_TS_ATTESTATION")
        if not source:
            raise unittest.SkipTest("C5_ISOLATION=container needs C5_TS_ATTESTATION (host TypeScript gate)")
        data = json.loads(Path(source).read_text())
        module.TS_ATTESTATION.parent.mkdir(parents=True, exist_ok=True)
        module.TS_ATTESTATION.write_text(json.dumps(data))
        return ["--ts-nonce", data["nonce"]]
    ts_dir = Path(os.environ.get("C5_TYPESCRIPT_DIR", REPO / "apps/octocat-supply/node_modules/typescript"))
    node = os.environ.get("C5_NODE") or next((p for p in ("/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node")
                                              if Path(p).is_file()), None)
    if node is None or not (ts_dir / "lib/typescript.js").is_file():
        raise unittest.SkipTest("node or pinned typescript unavailable for the C5-G4 gate")
    return ["--typescript-dir", str(ts_dir), "--node", node]


def run_harness(module, forge=None, repeat=1, env_overrides=None, seen_envs=None):
    """Run the real harness main() with an optional forging layer over engine results."""
    real_run = subprocess.run
    counters = {}

    def intercepted(argv, *args, **kwargs):
        is_engine = "scan" in argv and "--oss-only" in argv
        if is_engine and seen_envs is not None:
            seen_envs.append(dict(kwargs.get("env") or {}))
        if not is_engine or forge is None:
            return real_run(argv, *args, **kwargs)
        label = label_of(argv)
        counters[label] = counters.get(label, 0) + 1
        return forge(label, counters[label], lambda: real_run(argv, *args, **kwargs), argv)

    argv = ["feasibility.py", "--semgrep", SEMGREP, "--repeat", str(repeat), "--isolation", ISOLATION]
    argv += typescript_gate_args(module)
    out = io.StringIO()
    old_argv, old_run = os.sys.argv, module.subprocess.run
    saved_env = {k: os.environ.get(k) for k in (env_overrides or {})}
    try:
        os.sys.argv = argv
        module.subprocess.run = intercepted
        os.environ.update(env_overrides or {})
        with contextlib.redirect_stdout(out):
            code = module.main()
    finally:
        os.sys.argv = old_argv
        module.subprocess.run = old_run
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return code, out.getvalue()


def edited(proc, change):
    report = json.loads(proc.stdout)
    returncode = change(report)
    return subprocess.CompletedProcess(proc.args, proc.returncode if returncode is None else returncode,
                                       json.dumps(report).encode(), proc.stderr)


def on(label, transform, call=1):
    """Apply `transform(real_process)` to the n-th engine call with the given label."""
    def forge(seen_label, count, real, argv):
        proc = real()
        return transform(proc) if (seen_label == label and count == call) else proc
    return forge


@SKIP
class ReportRobustness(unittest.TestCase):
    """M11 (failure handling) and M12 (forged reports) against the real engine."""

    @classmethod
    def setUpClass(cls):
        cls.root = disposable_copy(cls)
        cls.harness = load(cls.root, "feasibility")

    def expect(self, code, forge, fragment, repeat=1):
        got, out = run_harness(self.harness, forge, repeat)
        self.assertEqual(got, code, out)
        self.assertIn(fragment, out)
        return out

    def test_baseline_real_engine_is_clean(self):
        self.expect(0, None, "result: 0 clean")

    # ---- M11: failures, crashes, partial/empty/truncated/malformed output, skipped targets
    def test_m11_empty_output(self):
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, 0, b"", b"")),
                    "malformed or empty engine JSON")

    def test_m11_truncated_json(self):
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, 0, p.stdout[: len(p.stdout) // 2], b"")),
                    "malformed or empty engine JSON")

    def test_m11_malformed_and_wrong_shape(self):
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, 0, b"Traceback: boom\n", b"")),
                    "malformed or empty engine JSON")
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, 0, b"[]", b"")),
                    "unexpected report shape or engine version")

    def test_m11_killed_process_with_partial_output(self):
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, -9, p.stdout[:4096], b"Killed")),
                    "malformed or empty engine JSON")

    def test_m11_timeout(self):
        def forge(label, count, real, argv):
            if label == "source":
                raise subprocess.TimeoutExpired(argv, 120)
            return real()
        self.expect(3, forge, "engine exceeded 120s deadline")

    def test_m11_crash_exit_with_valid_report(self):
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, 2, p.stdout, b"")),
                    "contradicts report findings")

    def test_m11_skipped_and_unparsed_targets(self):
        self.expect(3, on("source", lambda p: edited(p, lambda r: r["paths"]["scanned"].pop())),
                    "scanned paths differ from expected targets (missing 1")
        self.expect(3, on("source", lambda p: edited(p, lambda r: r["time"]["targets"][0].update(parse_times=[0.0]))),
                    "were not parsed")

    def test_m11_engine_errors_skipped_rules_and_version(self):
        self.expect(3, on("source", lambda p: edited(p, lambda r: r["errors"].append({"type": "Timeout", "path": "x"}))),
                    "engine reported 1 error(s)")
        self.expect(3, on("source", lambda p: edited(p, lambda r: r["skipped_rules"].append({"rule_id": "x"}))),
                    "engine skipped rules")
        self.expect(3, on("source", lambda p: edited(p, lambda r: r.update(version="1.999.0"))),
                    "unexpected report shape or engine version")

    # ---- M12: forged exit codes / findings / coverage / catalogue
    def test_m12_forged_exit_zero_with_findings(self):
        def add_finding(r):
            r["results"].append({"check_id": "morrow.py.process-shell", "path": r["paths"]["scanned"][0],
                                 "start": {"line": 1}, "end": {"line": 1}, "extra": {}})
            return 0
        self.expect(3, on("source", lambda p: edited(p, add_finding)), "contradicts report findings")

    def test_m12_forged_exit_one_without_findings(self):
        self.expect(3, on("source", lambda p: subprocess.CompletedProcess(p.args, 1, p.stdout, b"")),
                    "contradicts report findings")

    def test_m12_coverage_mismatch_extra_path(self):
        self.expect(3, on("source", lambda p: edited(p, lambda r: r["paths"]["scanned"].append("forged/extra.py"))),
                    "scanned paths differ from expected targets (missing 0, extra 1)")

    def test_m12_rule_catalogue_forgery(self):
        self.expect(3, on("source", lambda p: edited(p, lambda r: r["time"]["rules"].pop())),
                    "executed rule catalog differs from manifest")

    def test_m12_nondeterministic_repeat(self):
        def add_finding(r):
            r["results"].append({"check_id": "morrow.py.process-shell", "path": r["paths"]["scanned"][0],
                                 "start": {"line": 1}, "end": {"line": 1}, "extra": {}})
            return 1
        self.expect(3, on("source", lambda p: edited(p, add_finding), call=2), "findings differ between repeated runs",
                    repeat=2)

    def test_m12_forged_clean_controls_are_detected_as_control_failure(self):
        def wipe(r):
            r["results"] = []
            return 0
        self.expect(4, on("controls", lambda p: edited(p, wipe)), "result: 4 control-failure")

    def test_m12_forged_clean_malformed_controls(self):
        def clean(r):
            r["errors"] = []
            return 0
        self.expect(4, on("malformed", lambda p: edited(p, clean)), "malformed rejected=False")

    def test_m12_forged_result_outside_targets(self):
        def forge_path(r):
            r["results"].append({"check_id": "morrow.py.process-shell", "path": "../../etc/C5CANARYPATH",
                                 "start": {"line": 1}, "end": {"line": 1}, "extra": {}})
            return 1
        out = self.expect(3, on("source", lambda p: edited(p, forge_path)), "result references a path outside the targets")
        self.assertNotIn("C5CANARYPATH", out)

    def test_m12_forged_result_unknown_rule_or_line(self):
        def forge(rule, line):
            def change(r):
                r["results"].append({"check_id": rule, "path": r["paths"]["scanned"][0],
                                     "start": {"line": line}, "end": {"line": 1}, "extra": {}})
                return 1
            return change
        self.expect(3, on("source", lambda p: edited(p, forge("forged.C5CANARYRULE", 1))),
                    "result references a rule outside the catalogue")
        self.expect(3, on("source", lambda p: edited(p, forge("morrow.py.process-shell", 0))),
                    "result has an invalid line")

    def test_m11_unexpected_internal_error_is_a_tool_error(self):
        def forge(label, count, real, argv):
            if label == "source":
                raise RuntimeError("simulated internal failure C5CANARYCRASH")
            return real()
        out = self.expect(3, forge, "STOP [3 tool-error]: unexpected internal error (RuntimeError)")
        self.assertNotIn("C5CANARYCRASH", out)

    def test_m12_residual_consistent_source_forgery_is_not_detectable(self):
        """Documented limit: a forger who controls the engine output consistently (report + exit) for the
        source scan is not detectable from the report alone; engine integrity (hash/RECORD) and controls are
        the mitigations. This test pins the behaviour so any change is reviewed."""
        def forge(label, count, real, argv):
            proc = real()
            return proc  # the real source scan is already clean; a consistent forgery is indistinguishable
        self.expect(0, forge, "result: 0 clean")


@SKIP
class CanaryCapture(unittest.TestCase):
    """M14: canaries in source, identifiers (metavariables), parse-error snippets and environment never
    reach the console or any uploadable artifact; the raw private report must contain them (positive
    control), be 0600 inside a 0700 directory, and never be in an upload root."""

    @classmethod
    def setUpClass(cls):
        cls.root = disposable_copy(cls)
        cls.canary = f"C5CANARY{uuid.uuid4().hex[:16].upper()}"
        c = cls.canary
        (cls.root / "scripts/delivery/canary_probe.py").write_text(
            "import subprocess\n\n\n"
            "def leak():\n"
            f"    subprocess.run(\"echo {c}\", shell=True)\n")
        (cls.root / "apps/octocat-supply/api/src/canaryProbe.ts").write_text(
            "type User = { id_token_" + c + ": string };\n"
            "export function leak(user: User) {\n"
            "  console.log(\"signed in\", user.id_token_" + c + ");\n"
            "}\n")
        cls.env_canary = f"ghs_{c}"
        cls.harness = load(cls.root, "feasibility")
        cls.envs = []
        cls.engine_redaction = []

        def inject(proc):
            def change(report):
                for result in report["results"]:
                    extra = result.setdefault("extra", {})
                    cls.engine_redaction.append(extra.get("lines"))
                    extra["lines"] = f"subprocess.run('echo {c}', shell=True)"
                    extra["message"] = f"message {c}"
                    extra["metavars"] = {"$CMD": {"abstract_content": c}}
                    extra["dataflow_trace"] = {"taint_source": [c]}
                    extra["fix"] = c
            return edited(proc, change)
        cls.code, cls.out = run_harness(cls.harness, forge=on("source", inject), env_overrides={
            "GITHUB_TOKEN": cls.env_canary, "SEMGREP_APP_TOKEN": cls.env_canary,
            "OTEL_EXPORTER_OTLP_ENDPOINT": f"https://{c.lower()}.invalid"}, seen_envs=cls.envs)

    def published(self):
        files = sorted((self.root / "artifacts/sast").glob("*.json"))
        self.assertTrue(files, "no published summary written")
        return {f.name: f.read_text() for f in files}

    def test_scan_reports_the_canary_findings_by_rule_path_line_only(self):
        self.assertEqual(self.code, 1, self.out)
        self.assertIn("finding morrow.py.process-shell at scripts/delivery/canary_probe.py:5", self.out)
        self.assertIn("finding morrow.ts.sensitive-value-logged at apps/octocat-supply/api/src/canaryProbe.ts:3",
                      self.out)

    def test_engine_itself_redacts_snippets_without_login(self):
        """Observed CE 1.185.0 behaviour (extra layer, not relied upon): real results carry no source lines."""
        self.assertTrue(self.engine_redaction)
        self.assertTrue(all(value == "requires login" for value in self.engine_redaction), self.engine_redaction)

    def test_positive_control_raw_report_contains_canary_and_is_private(self):
        private = self.root / "artifacts/sast-private/c5"
        raws = sorted(private.glob("source-*.json"))
        self.assertTrue(raws)
        self.assertTrue(any(self.canary in r.read_text() for r in raws), "canary never reached engine output")
        self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o700)
        self.assertTrue(all(stat.S_IMODE(r.stat().st_mode) == 0o600 for r in private.glob("*.json")))

    def test_console_and_published_artifacts_contain_no_canary(self):
        for value in (self.canary, self.canary.lower(), self.env_canary):
            self.assertNotIn(value, self.out)
            for name, text in self.published().items():
                self.assertNotIn(value, text, f"canary leaked into {name}")

    def test_environment_canaries_never_reach_the_engine(self):
        self.assertTrue(self.envs, "engine environment not observed")
        for env in self.envs:
            self.assertFalse(any(self.env_canary in v or self.canary.lower() in v for v in env.values()), env.keys())
            for key in ("GITHUB_TOKEN", "SEMGREP_APP_TOKEN", "OTEL_EXPORTER_OTLP_ENDPOINT"):
                self.assertNotIn(key, env)

    def test_upload_roots_exclude_raw_reports(self):
        trial = (self.root / ".github/workflows/c5-sast-hosted-trial.yml").read_text()
        paths = [line.strip() for line in trial.splitlines() if line.strip().startswith("artifacts/")]
        self.assertEqual(len(paths), 6)
        self.assertTrue(all(p.startswith("artifacts/sast/") and p.endswith(".json") for p in paths))
        self.assertNotIn("sast-private", trial)
        ci = (self.root / ".github/workflows/ci.yml").read_text()
        self.assertNotIn("sast-private", ci)
        self.assertNotIn("artifacts/sast", ci)  # mandatory CI uploads only artifacts/m3 and artifacts/m4b

    def test_trial_driver_record_contains_no_canary(self):
        driver = load(self.root, "hosted_trial")
        harness = load(self.root, "feasibility")
        gate = typescript_gate_args(harness)
        out = io.StringIO()
        nonce = {"C5_TRIAL_NONCE": gate[1]} if ISOLATION == "container" else {}
        with contextlib.redirect_stdout(out), mock.patch.dict(os.environ, nonce):
            code = driver.run(Path(SEMGREP), 1, ISOLATION, () if ISOLATION == "container" else tuple(gate))
        self.assertEqual(code, 1)
        trial = (self.root / "artifacts/sast/hosted-trial.json").read_text()
        for value in (self.canary, self.env_canary):
            self.assertNotIn(value, out.getvalue())
            self.assertNotIn(value, trial)


@SKIP
class CanaryInParseErrors(unittest.TestCase):
    """M14 + M07: engine parse-error messages embed source snippets; they must not be printed or published.
    C5-G4: the TypeScript gate now stops malformed .ts/.tsx before Semgrep, so the engine parse-error path is
    exercised with a malformed .jsx file (not TypeScript, therefore not gated); see CanaryInTypeScriptGate."""

    @classmethod
    def setUpClass(cls):
        cls.root = disposable_copy(cls)
        cls.canary = f"C5CANARY{uuid.uuid4().hex[:16].upper()}"
        (cls.root / "apps/octocat-supply/frontend/src/CanaryBroken.jsx").write_text(
            f"export function {cls.canary}( {{\n  return <div>{{x</span>;\n")
        cls.harness = load(cls.root, "feasibility")
        cls.code, cls.out = run_harness(cls.harness)

    def test_parse_error_is_a_tool_error_without_snippet_leak(self):
        self.assertEqual(self.code, 3, self.out)
        self.assertIn("engine reported 1 error(s)", self.out)
        self.assertNotIn(self.canary, self.out)
        raw = (self.root / "artifacts/sast-private/c5/source-1.json").read_text()
        self.assertIn(self.canary, raw, "positive control: snippet expected only in the private raw report")
        for f in (self.root / "artifacts/sast").glob("*.json"):
            self.assertNotIn(self.canary, f.read_text())


@SKIP
class CanaryInTypeScriptGate(unittest.TestCase):
    """M14 + C5-G4: malformed TypeScript stops before Semgrep; the gate prints only path, TS code and position."""

    @classmethod
    def setUpClass(cls):
        cls.root = disposable_copy(cls)
        cls.canary = f"C5CANARY{uuid.uuid4().hex[:16].upper()}"
        (cls.root / "apps/octocat-supply/frontend/src/CanaryBroken.tsx").write_text(
            f"export function {cls.canary}( {{\n  return <div>{{x</span>;\n")
        cls.harness = load(cls.root, "feasibility")
        engine_calls = []

        def forge(label, count, real, argv):
            engine_calls.append(label)
            return real()
        cls.engine_calls = engine_calls
        # Container mode: the host attestation covers the pristine repository, so the added file must make the
        # in-container harness reject it (target-set mismatch, exit 2) before Semgrep runs.
        cls.code, cls.out = run_harness(cls.harness, forge=forge)

    def test_typescript_gate_stops_before_semgrep_without_leak(self):
        self.assertEqual(self.code, 3 if ISOLATION != "container" else 2, self.out)
        if ISOLATION != "container":
            self.assertIn("typescript syntax error: apps/octocat-supply/frontend/src/CanaryBroken.tsx (TS1", self.out)
        self.assertNotIn(self.canary, self.out)
        self.assertEqual(self.engine_calls, [], "no Semgrep process may start after a TypeScript gate failure")
        for f in (self.root / "artifacts").rglob("*.json"):
            self.assertNotIn(self.canary, f.read_text())


if __name__ == "__main__":
    unittest.main()
