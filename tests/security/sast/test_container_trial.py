"""C5-F4R container policy and driver exit-code tests (local; not in CI discovery).

Docker is mocked: these tests prove the driver's hardening argv, its stage/exit
mapping and its evidence binding. Real-engine container behaviour is validated
separately (see the C5-F4R evidence).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/sast"))
import check_trial_workflow as policy  # noqa: E402
import hosted_trial as driver  # noqa: E402

DOCKERFILE = policy.DOCKERFILE.read_text()
REAL_RUN = subprocess.run  # captured before any test patches driver.subprocess.run
IMAGE = "sha256:" + "a" * 64


def proc(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


class ContainerPolicy(unittest.TestCase):
    def check(self, dockerfile=DOCKERFILE, hardening=driver.HARDENING, base=driver.BASE_IMAGE):
        policy.container_policy(dockerfile, tuple(hardening), base)

    def rejects(self, **kwargs):
        with self.assertRaises(policy.Violation):
            self.check(**kwargs)

    def test_current_container_policy_passes(self):
        self.check()

    def test_rejects_dockerfile_mutations(self):
        digest = driver.BASE_IMAGE.split("@")[1]
        for old, new in ((f"FROM ubuntu@{digest}", "FROM ubuntu:24.04"),
                         (digest, "sha256:" + "b" * 64),
                         ("USER 1001:1001", "USER root"),
                         ("WORKDIR /repo", "WORKDIR /repo\nCOPY . /repo"),
                         ("python3=3.12.3-0ubuntu2.1", "python3"),
                         ("--no-install-recommends --snapshot", "--no-install-recommends --allow-unauthenticated --snapshot"),
                         ('apt-get update --snapshot "$UBUNTU_SNAPSHOT"', "apt-get update"),
                         ("rm -rf /var/lib/apt/lists/*;", "rm -rf /var/lib/apt/lists/*; curl -o /x https://example.invalid;")):
            with self.subTest(old=old):
                self.rejects(dockerfile=DOCKERFILE.replace(old, new))
        self.rejects(base="ubuntu:24.04")

    def test_rejects_hardening_mutations(self):
        h = list(driver.HARDENING)

        def without(*items):
            out = list(h)
            for item in items:
                i = out.index(item)
                del out[i:i + (2 if item.startswith("--") and item not in {"--rm", "--read-only"} else 1)]
            return out
        for mutated in (without("--network"), without("--read-only"), without("--cap-drop"), without("--rm"),
                        [x if x != "1001:1001" else "0:0" for x in h], [x if x != "none" else "host" for x in h],
                        [x if x != "no-new-privileges=true" else "seccomp=unconfined" for x in h],
                        h + ["--privileged"], h + ["--cap-add", "SYS_ADMIN"], h + ["--pid", "host"],
                        h + ["--security-opt", "apparmor=unconfined"], h + ["-v", "/var/run/docker.sock:/s"],
                        [x.replace("noexec,", "") for x in h]):
            with self.subTest(mutated=mutated[-2:]):
                self.rejects(hardening=mutated)


class DriverExitCodes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.iid = base / "iid"
        self.iid.write_text(IMAGE)
        self.wheels = base / "wheels"
        self.wheels.mkdir()
        self.venv = base / "venv"
        self.out = base / "out"
        patches = [mock.patch.object(driver, "OUT", self.out),
                   mock.patch.object(driver, "TRIAL", self.out / "hosted-trial.json"),
                   mock.patch.object(driver, "INSTALL_EVIDENCE", self.out / "container-install.json"),
                   mock.patch.object(driver, "RUN_EVIDENCE", self.out / "container-run.json"),
                   mock.patch.object(driver.shutil, "which", return_value="/usr/bin/docker"),
                   mock.patch("builtins.print")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def install(self, results):
        calls = []

        def fake(argv, **kwargs):
            calls.append(argv)
            return results.pop(0)
        with mock.patch.object(driver.subprocess, "run", side_effect=fake):
            code = driver.container_install(str(self.iid), str(self.wheels), str(self.venv))
        return code, calls

    def test_install_success_uses_hardened_offline_hash_locked_commands(self):
        code, calls = self.install([proc(), proc(), proc(0, "No broken requirements found.")])
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 3)
        for argv in calls:
            for flag in ("--network", "none", "--read-only", "--cap-drop", "ALL", "no-new-privileges=true",
                         "1001:1001", IMAGE):
                self.assertIn(flag, argv)
            self.assertFalse(any("--privileged" == a or a.startswith("--cap-add") for a in argv))
        pip = calls[1]
        for flag in ("--no-index", "--no-deps", "--only-binary=:all:", "--require-hashes", "/wheels"):
            self.assertIn(flag, pip)
        self.assertEqual(calls[2][-3:], ["-m", "pip", "check"])

    def test_install_failure_classes(self):
        cases = ((["pip"], [proc(), proc(1, "", "THESE PACKAGES DO NOT MATCH THE HASHES")], 2, "pip-install"),
                 (["check"], [proc(), proc(), proc(1, "semgrep requires mcp, which is not installed.")], 2, "pip-check"),
                 (["runtime"], [proc(125, "", "Unable to find image")], 6, "venv"),
                 (["venv"], [proc(1, "", "venv failed")], 6, "venv"))
        for _, results, expected, stage in cases:
            with self.subTest(stage=stage, expected=expected):
                if self.venv.exists():
                    for f in self.venv.iterdir():
                        f.unlink()
                code, _ = self.install(list(results))
                self.assertEqual(code, expected)
                record = json.loads((self.out / "container-install.json").read_text())
                self.assertIn(stage, record["reason"])

    def test_configuration_errors(self):
        self.venv.mkdir()
        (self.venv / "stale").write_text("x")
        self.assertEqual(self.install([])[0], 2)  # non-empty venv
        self.iid.write_text("latest")
        self.assertEqual(self.install([])[0], 2)  # malformed image id
        self.iid.unlink()
        self.assertEqual(self.install([])[0], 6)  # image never built
        self.iid.write_text(IMAGE)
        self.assertEqual(driver.container_install(str(self.iid), str(self.wheels / "missing"), str(self.venv / "n")), 2)

    def scan(self, docker_exit, write=None, timeout=False, gate=None):
        self.venv.mkdir(exist_ok=True)
        self.calls = []

        def fake(argv, **kwargs):
            self.calls.append(argv)
            if "--typescript-gate-only" in argv:  # C5-G4 host-side gate before any container
                return gate(argv) if gate else proc(0, "typescript gate: pass (attestation written)")
            if argv[1] == "kill":
                return proc()
            if timeout:
                raise subprocess.TimeoutExpired(argv, 1)
            nonce = kwargs["env"]["C5_TRIAL_NONCE"]
            if write is not None:
                self.out.mkdir(parents=True, exist_ok=True)
                (self.out / "hosted-trial.json").write_text(json.dumps(write(nonce)))
            return proc(docker_exit)
        with mock.patch.object(driver.subprocess, "run", side_effect=fake), \
                mock.patch.object(driver, "ROOT", Path(self.tmp.name)):
            return driver.container_run(str(self.iid), str(self.venv), 1)

    def test_scan_exit_mapping_and_evidence_binding(self):
        good = lambda code: (lambda nonce: {"nonce": nonce, "harness_exit": code})  # noqa: E731
        for harness_code in range(6):
            with self.subTest(harness=harness_code):
                self.assertEqual(self.scan(harness_code, good(harness_code)), harness_code)
        self.assertEqual(self.scan(125), 6)        # docker daemon/run error
        self.assertEqual(self.scan(137), 6)        # killed / OOM
        self.assertEqual(self.scan(0, timeout=True), 6)
        (self.out / "hosted-trial.json").unlink()
        self.assertEqual(self.scan(0, None), 7)    # evidence missing
        self.assertEqual(self.scan(0, lambda n: {"nonce": "0" * 32, "harness_exit": 0}), 7)  # stale evidence
        self.assertEqual(self.scan(1, good(0)), 7)  # exit/evidence disagreement
        record = json.loads((self.out / "container-run.json").read_text())
        self.assertEqual(record["result"], "evidence-missing")

    def test_e03_driver_failures_are_evidence_missing_not_findings(self):
        self.assertEqual(self.scan(7), 7)  # in-container driver could not produce evidence
        record = json.loads((self.out / "container-run.json").read_text())
        self.assertIn("could not produce evidence", record["reason"])
        out = []
        with mock.patch.object(driver, "_main", side_effect=PermissionError("secret C5CANARY")), \
                mock.patch("builtins.print", side_effect=out.append):
            self.assertEqual(driver.main(), 7)
        self.assertIn("PermissionError", out[0])
        self.assertNotIn("C5CANARY", out[0])

    def test_g4_host_typescript_gate_runs_first_and_fails_closed(self):
        good = lambda nonce: {"nonce": nonce, "harness_exit": 0}  # noqa: E731
        self.assertEqual(self.scan(0, good), 0)
        gate_argv, docker_argv = self.calls[0], self.calls[1]
        self.assertIn("--typescript-gate-only", gate_argv)
        nonce = gate_argv[gate_argv.index("--ts-nonce") + 1]
        self.assertRegex(nonce, r"^[0-9a-f]{32}$")
        self.assertEqual(json.loads((self.out / "container-run.json").read_text())["nonce"], nonce)
        self.assertEqual(docker_argv[1], "run")
        self.assertIn("--network", docker_argv)
        self.assertEqual(docker_argv[docker_argv.index("--network") + 1], "none")
        self.assertNotIn("--typescript-gate-only", docker_argv)
        for harness_code, expected in ((2, 2), (3, 3), (4, 4), (1, 3), (5, 3), (137, 3)):
            with self.subTest(gate_exit=harness_code):
                self.assertEqual(self.scan(0, good, gate=lambda argv, c=harness_code: proc(c, "typescript gate: STOP")), expected)
                self.assertEqual(len(self.calls), 1, "no container may start after a failed TypeScript gate")
                record = json.loads((self.out / "container-run.json").read_text())
                self.assertIn("TypeScript syntax gate failed", record["reason"])

        def slow(argv):
            raise subprocess.TimeoutExpired(argv, 300)
        self.assertEqual(self.scan(0, good, gate=slow), 3)
        self.assertEqual(len(self.calls), 1)

    def test_g4_in_container_run_passes_the_run_nonce(self):
        captured = {}

        def fake(argv, **kwargs):
            captured["argv"] = argv
            return proc(4)
        with mock.patch.object(driver.subprocess, "run", side_effect=fake), \
                mock.patch.dict(driver.os.environ, {"C5_TRIAL_NONCE": "ab" * 16}):
            driver.run(Path("/opt/sast/bin/semgrep"), 1, "container")
        self.assertEqual(captured["argv"][-2:], ["--ts-nonce", "ab" * 16])
        with mock.patch.object(driver.subprocess, "run", side_effect=fake):
            driver.run(Path("/opt/sast/bin/semgrep"), 1, "auto")
        self.assertNotIn("--ts-nonce", captured["argv"])

    def fake_node(self, version_output):
        node = Path(self.tmp.name) / f"node-{len(version_output)}"
        node.write_text("#!/bin/sh\necho '%s'\n" % version_output)
        node.chmod(0o755)
        return node

    def test_g4h_pinned_node_must_match_node_version_file(self):
        want = "v" + driver.NODE_VERSION_FILE.read_text().strip()
        self.assertEqual(driver.pinned_node(None), None)
        self.assertEqual(driver.pinned_node(str(self.fake_node(want))), self.fake_node(want))
        for bad in (self.fake_node("v22.17.1"), self.fake_node(want + "-rc"), self.fake_node("")):
            with self.subTest(node=bad.name), self.assertRaises(driver.Fail) as ctx:
                driver.pinned_node(str(bad))
            self.assertEqual(ctx.exception.code, 2)
        for raw in ("node", "relative/node", str(Path(self.tmp.name) / "missing")):
            with self.subTest(raw=raw), self.assertRaises(driver.Fail):
                driver.pinned_node(raw)

    def test_g4h_preflight_stops_before_any_container(self):
        want = "v" + driver.NODE_VERSION_FILE.read_text().strip()
        calls = []

        def fake(argv, **kwargs):
            calls.append(argv)
            if argv[-1] == "--version":
                return REAL_RUN(argv, capture_output=True, text=True, check=False)
            return proc(self.gate_code, "typescript gate: STOP" if self.gate_code else "typescript gate: pass")
        with mock.patch.object(driver.subprocess, "run", side_effect=fake):
            self.gate_code = 0
            self.assertEqual(driver.typescript_preflight(str(self.fake_node(want))), 0)
            gate = calls[-1]
            self.assertIn("--typescript-gate-only", gate)
            self.assertEqual(gate[gate.index("--node") + 1], str(self.fake_node(want)))
            self.assertRegex(gate[gate.index("--ts-nonce") + 1], r"^[0-9a-f]{32}$")
            for code, expected in ((2, 2), (3, 3), (4, 4), (9, 3)):
                with self.subTest(gate_exit=code):
                    self.gate_code = code
                    self.assertEqual(driver.typescript_preflight(str(self.fake_node(want))), expected)
            calls.clear()
            self.assertEqual(driver.typescript_preflight(str(self.fake_node("v20.0.0"))), 2)
            self.assertFalse(any("--typescript-gate-only" in c for c in calls), "no gate with an unpinned node")
        self.assertFalse(any(c and c[0].endswith("docker") for c in calls))

    def test_g4h_container_run_requires_pinned_node_before_gate_and_docker(self):
        want = "v" + driver.NODE_VERSION_FILE.read_text().strip()
        self.venv.mkdir(exist_ok=True)
        calls = []

        def fake(argv, **kwargs):
            calls.append(argv)
            if argv[-1] == "--version":
                return REAL_RUN(argv, capture_output=True, text=True, check=False)
            if "--typescript-gate-only" in argv:
                return proc(0, "typescript gate: pass")
            if argv[1] == "run":
                self.out.mkdir(parents=True, exist_ok=True)
                (self.out / "hosted-trial.json").write_text(json.dumps({"nonce": kwargs["env"]["C5_TRIAL_NONCE"],
                                                                          "harness_exit": 0}))
            return proc(0)
        with mock.patch.object(driver.subprocess, "run", side_effect=fake), \
                mock.patch.object(driver, "ROOT", Path(self.tmp.name)):
            self.assertEqual(driver.container_run(str(self.iid), str(self.venv), 1, str(self.fake_node("v20.0.0"))), 2)
            self.assertEqual([c for c in calls if c[-1] != "--version"], [], "nothing may run with an unpinned node")
            self.assertEqual(driver.container_run(str(self.iid), str(self.venv), 1, str(self.fake_node(want))), 0)
        gate = next(c for c in calls if "--typescript-gate-only" in c)
        self.assertEqual(gate[gate.index("--node") + 1], str(self.fake_node(want)))

    def test_scan_argv_is_hardened_and_never_leaks_values(self):
        captured = {}

        def fake(argv, **kwargs):
            captured["argv"] = argv
            return proc(0)
        self.venv.mkdir(exist_ok=True)
        with mock.patch.object(driver.subprocess, "run", side_effect=fake), \
                mock.patch.object(driver, "ROOT", Path(self.tmp.name)), \
                mock.patch.dict(driver.os.environ, {"TRIAL_AUTHORIZATION_REFERENCE": "owner approval x"}):
            driver.container_run(str(self.iid), str(self.venv), 1)
        argv = captured["argv"]
        self.assertIn("--isolation", argv)
        self.assertEqual(argv[argv.index("--isolation") + 1], "container")
        self.assertIn("TRIAL_AUTHORIZATION_REFERENCE", argv)
        self.assertNotIn("owner approval x", " ".join(argv))
        mounts = [argv[i + 1] for i, a in enumerate(argv) if a == "--mount"]
        self.assertTrue(any(m.endswith("target=/repo,readonly") for m in mounts))
        self.assertTrue(any(m.endswith("target=/opt/sast,readonly") for m in mounts))
        self.assertFalse(any("docker.sock" in m for m in mounts))


if __name__ == "__main__":
    unittest.main()
