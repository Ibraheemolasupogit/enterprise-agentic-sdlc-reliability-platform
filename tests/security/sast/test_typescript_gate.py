"""C5-G4 TypeScript syntax gate regression tests (local; not in CI discovery).

Run:  python3 -m unittest tests/security/sast/test_typescript_gate.py
Needs Node (>= the manifest minimum) and the lock-pinned typescript package installed under
apps/octocat-supply/node_modules (override with C5_NODE / C5_TYPESCRIPT_DIR). Without them every test is
skipped explicitly. Optional C5_SEMGREP adds an end-to-end check that a malformed TypeScript source file
stops the real harness before any Semgrep process starts.

All repository mutations happen in disposable copies; the working tree is never modified.
"""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TS_DIR = Path(os.environ.get("C5_TYPESCRIPT_DIR", REPO / "apps/octocat-supply/node_modules/typescript"))
NODE = next((Path(p) for p in ([os.environ["C5_NODE"]] if os.environ.get("C5_NODE") else
                               ["/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"])
             if Path(p).is_file()), None)
SEMGREP = os.environ.get("C5_SEMGREP")
AVAILABLE = NODE is not None and (TS_DIR / "lib/typescript.js").is_file()
SKIP = unittest.skipUnless(AVAILABLE, "node or pinned typescript unavailable: C5-G4 gate tests skipped")
IGNORE = shutil.ignore_patterns(".git", "node_modules", "dist", "coverage", "artifacts", "__pycache__", ".venv",
                                "test-results", "playwright-report", ".DS_Store")
NONCE = "0123456789abcdef" * 2
G4_CASES = {  # the known Semgrep parser-recovery gaps (F1/F3) plus F3 matrix case T03
    "double-comma": "export const a = { b: 1,, c: 2 };\n",
    "unclosed-condition": "export function g(a: boolean) {\n  if (a {\n    return 1;\n  }\n  return 0;\n}\n",
    "unclosed-parameters": "export function f(v: string {\n  return v;\n}\n",
    "t03-broken": "export const a = { b: 1,, c: 2 };\n",
}
# Appended tails that are invalid TypeScript wherever they are placed after a complete, valid module.
MUTATION_TAILS = ("\nexport const = ;\n", "\nfunction (\n", "\nlet x: = 1;\n", "\nif (\n", "\nclass {\n")


def disposable_copy():
    tmp = tempfile.TemporaryDirectory(prefix="c5-g4-")
    root = Path(tmp.name) / "repo"
    shutil.copytree(REPO, root, ignore=IGNORE, symlinks=True)
    data = root / "apps/octocat-supply/data"
    if data.exists():
        shutil.rmtree(data)
    return tmp, root


def load(root):
    spec = importlib.util.spec_from_file_location(f"feasibility_g4_{uuid.uuid4().hex}", root / "scripts/sast/feasibility.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@SKIP
class GateBehaviour(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = disposable_copy()
        self.addCleanup(self.tmp.cleanup)
        self.h = load(self.root)
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    DEFAULT = object()  # use the manifest's default compiler location inside the disposable copy

    def gate(self, node=None, ts_dir=None, wrapper=()):
        directory = None if ts_dir is self.DEFAULT else (ts_dir or TS_DIR)
        return self.h.run_typescript_gate(self.h.inventory(), self.home, node or NODE, directory, list(wrapper))

    def stops(self, code, fn, *args, contains=None):
        with self.assertRaises(self.h.Stop) as ctx:
            fn(*args)
        self.assertEqual(ctx.exception.code, code, str(ctx.exception))
        if contains:
            self.assertIn(contains, str(ctx.exception))
        return str(ctx.exception)

    # ------------------------------------------------------------ positive
    def test_current_repository_passes_and_binds_hashes(self):
        gate = self.gate()
        accept, reject = self.h.typescript_sets(self.h.inventory())
        self.assertEqual(gate["status"], "pass")
        self.assertEqual((gate["accepted"], gate["rejected_controls"]), (len(accept), len(reject)))
        self.assertEqual(gate["rejected_controls"], 5)  # 2 malformed + 3 parser-gap TypeScript fixtures
        self.assertTrue(all(p.endswith((".ts", ".tsx")) for p in gate["hashes"]))
        self.assertEqual(set(gate["hashes"]), set(accept + reject))
        self.assertEqual(gate["compiler_sha256"], json.loads((self.root / "security/sast/typescript-gate.json")
                                                              .read_text())["files_sha256"]["lib/typescript.js"])
        self.h.recheck_typescript(gate)

    def test_targets_are_exactly_the_semgrep_typescript_inputs(self):
        inv = self.h.inventory()
        accept, reject = self.h.typescript_sets(inv)
        source = {p for p, (_, m) in inv.items() if m == "source" and p.endswith((".ts", ".tsx"))}
        annotated = {p for p, (_, m) in inv.items() if m == "controls" and p.endswith((".ts", ".tsx"))
                     and self.h.fixture_kind(p) == "annotated"}
        self.assertEqual(set(accept), source | annotated)
        self.assertFalse(any(p.endswith((".mts", ".cts", ".d.mts")) for p in accept + reject))

    def test_gate_runs_inside_the_auto_isolation_wrapper(self):
        if sys.platform != "darwin":
            self.skipTest("macOS sandbox-exec wrapper only")
        self.assertEqual(self.gate(wrapper=self.h.isolation_wrapper()[0])["status"], "pass")

    # ------------------------------------------------------------ negative: syntax
    def test_g4_cases_fail_closed_as_source(self):
        for name, text in G4_CASES.items():
            with self.subTest(case=name):
                target = self.root / f"apps/octocat-supply/api/src/g4-{name}.ts"
                target.write_text(text)
                try:
                    message = self.stops(self.h.EXIT_TOOL, self.gate, contains="typescript syntax error")
                    self.assertIn(f"api/src/g4-{name}.ts", message)
                    self.assertRegex(message, r"\(TS1\d{3} at \d+:\d+\)")
                finally:
                    target.unlink()

    def test_tsx_and_test_files_are_gated(self):
        for rel in ("apps/octocat-supply/frontend/src/G4Broken.tsx", "apps/octocat-supply/api/test/g4.test.ts"):
            with self.subTest(rel=rel):
                (self.root / rel).write_text("export const V = () => <div>{</div>;\n" if rel.endswith("x")
                                             else "describe('x', () => {\n")
                try:
                    self.stops(self.h.EXIT_TOOL, self.gate, contains=rel)
                finally:
                    (self.root / rel).unlink()

    def test_mutation_regression_every_real_file(self):
        """Every source TypeScript file x 5 invalid tails: the gate script must flag all, and none of the originals."""
        accept, _ = self.h.typescript_sets(self.h.inventory())
        source = [p for p in accept if not p.startswith("tests/")]
        mut = Path(self.tmp.name) / "mut"
        files = []
        for i, rel in enumerate(source):
            text = (self.root / rel).read_text()
            orig = f"orig/{i}{Path(rel).suffix}"
            (mut / orig).parent.mkdir(parents=True, exist_ok=True)
            (mut / orig).write_text(text)
            files.append(orig)
            for j, tail in enumerate(MUTATION_TAILS):
                name = f"m{j}/{i}{Path(rel).suffix}"
                (mut / name).parent.mkdir(parents=True, exist_ok=True)
                (mut / name).write_text(text + tail)
                files.append(name)
        manifest = json.loads((self.root / "security/sast/typescript-gate.json").read_text())
        request = self.home / "req.json"
        request.write_text(json.dumps({"root": str(mut), "compiler": str(TS_DIR / "lib/typescript.js"),
                                       "compiler_sha256": manifest["files_sha256"]["lib/typescript.js"],
                                       "version": manifest["version"], "files": files}))
        proc = subprocess.run([str(NODE), "--no-addons", "--disallow-code-generation-from-strings",
                               str(self.root / "scripts/sast/ts_syntax_gate.mjs"), str(request)],
                              capture_output=True, text=True, timeout=300, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout[-300:])
        result = json.loads(proc.stdout)["files"]
        originals = [f for f in files if f.startswith("orig/")]
        mutants = [f for f in files if not f.startswith("orig/")]
        self.assertEqual(len(mutants), len(source) * len(MUTATION_TAILS))
        self.assertEqual([f for f in originals if result[f]["diagnostic_count"]], [])
        self.assertEqual([f for f in mutants if not result[f]["diagnostic_count"]], [])

    # ------------------------------------------------------------ negative: compiler, lock, manifest, node
    def isolated_compiler(self):
        tdir = Path(self.tmp.name) / "ts"
        (tdir / "lib").mkdir(parents=True)
        shutil.copy2(TS_DIR / "package.json", tdir / "package.json")
        shutil.copy2(TS_DIR / "lib/typescript.js", tdir / "lib/typescript.js")
        return tdir

    def test_compiler_tampering_and_absence_fail_closed(self):
        tdir = self.isolated_compiler()
        self.assertEqual(self.gate(ts_dir=tdir)["status"], "pass")
        lib = tdir / "lib/typescript.js"
        original = lib.read_bytes()
        lib.write_bytes(original + b"\n// tampered\n")
        self.stops(self.h.EXIT_CONFIG, self.gate, None, tdir, contains="hash mismatch")
        lib.write_bytes(original)
        pkg = json.loads((tdir / "package.json").read_text())
        (tdir / "package.json").write_text(json.dumps({**pkg, "version": "6.0.4"}))
        self.stops(self.h.EXIT_CONFIG, self.gate, None, tdir, contains="version differs")
        shutil.copy2(TS_DIR / "package.json", tdir / "package.json")
        lib.unlink()
        lib.symlink_to(TS_DIR / "lib/typescript.js")
        self.stops(self.h.EXIT_CONFIG, self.gate, None, tdir, contains="unavailable")
        self.stops(self.h.EXIT_CONFIG, self.gate, None, Path(self.tmp.name) / "missing", contains="unavailable")
        self.stops(self.h.EXIT_CONFIG, self.gate, None, self.DEFAULT, contains="unavailable")  # copy has no node_modules

    def test_lockfile_or_manifest_drift_fails_closed(self):
        lock = self.root / "apps/octocat-supply/package-lock.json"
        original = lock.read_text()
        data = json.loads(original)
        for field, value in (("version", "6.0.4"), ("integrity", "sha512-AAAA"), ("resolved", "https://example.invalid/t.tgz")):
            with self.subTest(lock_field=field):
                changed = json.loads(original)
                changed["packages"]["node_modules/typescript"][field] = value
                lock.write_text(json.dumps(changed))
                self.stops(self.h.EXIT_CONFIG, self.gate, contains="does not match the application lockfile")
        del data["packages"]["node_modules/typescript"]
        lock.write_text(json.dumps(data))
        self.stops(self.h.EXIT_CONFIG, self.gate)
        lock.write_text(original)
        manifest = self.root / "security/sast/typescript-gate.json"
        good = manifest.read_text()
        for change in ({"lock": "../outside.json"}, {"default_dir": "/etc"}, {"files_sha256": {"../x": "0"}},
                       {"files_sha256": {}}):
            with self.subTest(manifest=change):
                manifest.write_text(json.dumps({**json.loads(good), **change}))
                self.stops(self.h.EXIT_CONFIG, self.gate)
        manifest.unlink()
        self.stops(self.h.EXIT_CONFIG, self.gate, contains="manifest missing")

    def fake_node(self, body):
        script = Path(self.tmp.name) / f"node-{uuid.uuid4().hex[:6]}"
        script.write_text("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo ${FAKE_VERSION:-v24.0.0}; exit 0; fi\n" + body)
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return script

    def test_node_runtime_problems_fail_closed(self):
        self.stops(self.h.EXIT_CONFIG, self.gate, Path(self.tmp.name) / "no-node", contains="node runtime unavailable")
        old = Path(self.tmp.name) / "old-node"
        old.write_text("#!/bin/sh\necho v18.20.0\n")
        old.chmod(0o755)
        self.stops(self.h.EXIT_CONFIG, self.gate, old, contains="older than")
        self.stops(self.h.EXIT_TOOL, self.gate, self.fake_node("echo not-json\n"), contains="malformed output")
        self.stops(self.h.EXIT_TOOL, self.gate, self.fake_node("echo '{\"error\": \"compiler hash mismatch\"}'; exit 2\n"),
                   contains="compiler hash mismatch")
        self.stops(self.h.EXIT_TOOL, self.gate, self.fake_node("sleep 0; exit 0\n"), contains="malformed output")

    def forged(self, transform):
        """A fake node that replays the real gate result after `transform` (simulates a compromised gate)."""
        real = self.gate()
        accept, reject = self.h.typescript_sets(self.h.inventory())
        files = {rel: {"sha256": real["hashes"][rel], "diagnostics": [[1005, 1, 1]] if rel in reject else [],
                       "diagnostic_count": 1 if rel in reject else 0} for rel in accept + reject}
        result = {"schema": "c5-ts-syntax-gate-result/1", "typescript_version": real["typescript"],
                  "compiler_sha256": real["compiler_sha256"], "files": files}
        transform(result)
        payload = Path(self.tmp.name) / f"result-{uuid.uuid4().hex[:6]}.json"
        payload.write_text(json.dumps(result))
        return self.fake_node(f"cat '{payload}'\n")

    def test_forged_or_inconsistent_gate_results_fail_closed(self):
        self.assertEqual(self.gate(self.forged(lambda r: None))["status"], "pass")  # replay control
        cases = [
            (self.h.EXIT_CONTROL, "self-test failed", lambda r: [f.update(diagnostic_count=0, diagnostics=[]) for f in r["files"].values()]),
            (self.h.EXIT_TOOL, "different file set", lambda r: r["files"].pop(sorted(r["files"])[0])),
            (self.h.EXIT_TOOL, "different file set", lambda r: r["files"].update({"apps/extra.ts": {"sha256": "0", "diagnostic_count": 0}})),
            (self.h.EXIT_TOOL, "changed during validation", lambda r: r["files"][sorted(r["files"])[0]].update(sha256="0" * 64)),
            (self.h.EXIT_TOOL, "pinned compiler", lambda r: r.update(compiler_sha256="0" * 64)),
            (self.h.EXIT_TOOL, "pinned compiler", lambda r: r.update(typescript_version="5.9.3")),
            (self.h.EXIT_TOOL, "bad result", lambda r: r["files"][sorted(r["files"])[0]].update(diagnostic_count="0")),
        ]
        for code, text, transform in cases:
            with self.subTest(expect=text):
                self.stops(code, self.gate, self.forged(transform), contains=text)

    # ------------------------------------------------------------ race window and attestation
    def test_post_scan_recheck_detects_changes(self):
        gate = self.gate()
        rel = sorted(gate["hashes"])[0]
        path = self.root / rel
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        self.stops(self.h.EXIT_TOOL, self.h.recheck_typescript, gate, contains="between validation and scan")
        path.unlink()
        self.stops(self.h.EXIT_TOOL, self.h.recheck_typescript, gate, contains=rel)
        path.write_bytes(original)
        self.h.recheck_typescript(gate)

    def test_attestation_round_trip_and_tampering(self):
        inv = self.h.inventory()
        gate = self.gate()
        self.h.write_typescript_attestation(gate, NONCE)
        self.assertEqual(self.h.verify_typescript_attestation(inv, NONCE)["mode"], "host-attestation")
        self.stops(self.h.EXIT_CONFIG, self.h.verify_typescript_attestation, inv, "f" * 32, contains="nonce mismatch")
        self.stops(self.h.EXIT_CONFIG, self.h.verify_typescript_attestation, inv, "not-a-nonce", contains="malformed")
        self.stops(self.h.EXIT_CONFIG, self.h.write_typescript_attestation, gate, None, contains="malformed")
        path = self.h.TS_ATTESTATION
        good = json.loads(path.read_text())
        for change, code, text in (({"status": "fail"}, self.h.EXIT_CONFIG, "status"),
                                   ({"gate_sha256": "0" * 64}, self.h.EXIT_CONFIG, "differs"),
                                   ({"manifest_sha256": "0" * 64}, self.h.EXIT_CONFIG, "differs"),
                                   ({"compiler_sha256": "0" * 64}, self.h.EXIT_CONFIG, "differs"),
                                   ({"accepted": 1}, self.h.EXIT_CONFIG, "different TypeScript target set"),
                                   ({"hashes": {k: v for k, v in list(good["hashes"].items())[1:]}}, self.h.EXIT_CONFIG,
                                    "different TypeScript target set")):
            with self.subTest(change=sorted(change)):
                path.write_text(json.dumps({**good, **change}))
                self.stops(code, self.h.verify_typescript_attestation, inv, NONCE, contains=text)
        path.write_text(json.dumps(good))
        rel = sorted(good["hashes"])[0]
        original = (self.root / rel).read_bytes()
        (self.root / rel).write_bytes(original + b"\n")
        self.stops(self.h.EXIT_TOOL, self.h.verify_typescript_attestation, inv, NONCE, contains="after host validation")
        (self.root / rel).write_bytes(original)
        extra = self.root / "apps/octocat-supply/api/src/added-after-attestation.ts"
        extra.write_text("export const x = 1;\n")
        self.stops(self.h.EXIT_CONFIG, self.h.verify_typescript_attestation, self.h.inventory(), NONCE,
                   contains="different TypeScript target set")
        extra.unlink()
        path.unlink()
        self.stops(self.h.EXIT_CONFIG, self.h.verify_typescript_attestation, inv, NONCE, contains="attestation missing")

    # ------------------------------------------------------------ CLI contract
    def run_main(self, *argv):
        out = io.StringIO()
        old = sys.argv
        try:
            sys.argv = ["feasibility.py", *argv]
            with contextlib.redirect_stdout(out):
                return self.h.main(), out.getvalue()
        finally:
            sys.argv = old

    def test_cli_mode_rules(self):
        cfg = self.h.EXIT_CONFIG
        for argv, text in ((["--semgrep", "/x", "--ts-nonce", NONCE], "--ts-nonce is not accepted"),
                           (["--semgrep", "/x", "--isolation", "container"], "requires --ts-nonce"),
                           (["--semgrep", "/x", "--isolation", "container", "--ts-nonce", NONCE, "--node", str(NODE)], "no node is used"),
                           (["--semgrep", "/x", "--isolation", "container", "--ts-nonce", NONCE, "--typescript-dir", "/x"], "no node is used"),
                           (["--typescript-gate-only", "--semgrep", "/x", "--ts-nonce", NONCE], "without Semgrep"),
                           (["--typescript-gate-only", "--isolation", "container", "--ts-nonce", NONCE], "without Semgrep")):
            with self.subTest(argv=argv):
                code, out = self.run_main(*argv)
                self.assertEqual(code, cfg, out)
                self.assertIn(text, out)
        code, out = self.run_main("--typescript-gate-only", "--typescript-dir", str(TS_DIR), "--node", str(NODE))
        self.assertEqual(code, cfg)
        self.assertIn("nonce missing", out)
        code, out = self.run_main("--typescript-gate-only", "--typescript-dir", str(TS_DIR), "--node", str(NODE),
                                  "--ts-nonce", NONCE)
        self.assertEqual(code, self.h.EXIT_CLEAN, out)
        self.assertEqual(json.loads(self.h.TS_ATTESTATION.read_text())["nonce"], NONCE)


@SKIP
@unittest.skipUnless(SEMGREP and Path(SEMGREP).is_file(), "C5_SEMGREP not set: end-to-end G4 test skipped")
class HarnessEndToEnd(unittest.TestCase):
    def test_malformed_typescript_stops_before_any_semgrep_process(self):
        tmp, root = disposable_copy()
        self.addCleanup(tmp.cleanup)
        h = load(root)
        (root / "apps/octocat-supply/api/src/broken.ts").write_text(G4_CASES["t03-broken"])
        engine_calls, real = [], subprocess.run

        def spy(argv, *args, **kwargs):
            if "scan" in argv and "--oss-only" in argv:
                engine_calls.append(argv)
            return real(argv, *args, **kwargs)
        h.subprocess.run = spy
        out, old = io.StringIO(), sys.argv
        try:
            sys.argv = ["feasibility.py", "--semgrep", SEMGREP, "--repeat", "1", "--typescript-dir", str(TS_DIR),
                        "--node", str(NODE)]
            with contextlib.redirect_stdout(out):
                code = h.main()
        finally:
            sys.argv = old
        self.assertEqual(code, h.EXIT_TOOL, out.getvalue())
        self.assertIn("typescript syntax error: apps/octocat-supply/api/src/broken.ts (TS1136", out.getvalue())
        self.assertEqual(engine_calls, [], "Semgrep must not run after a TypeScript syntax failure")


if __name__ == "__main__":
    unittest.main()
