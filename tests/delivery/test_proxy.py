import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("verify_proxy", ROOT / "scripts/delivery/verify_proxy.py")
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


class ProxyHarnessTests(unittest.TestCase):
    def test_only_public_fixture_files_are_readable_across_container_uids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            names = [name for name, _ in proxy.FIXTURES] + ["peer.mjs"]
            for name in names:
                (path / name).write_text("public test material")
                (path / name).chmod(0o600)
            unrelated = path / "unrelated.txt"
            unrelated.write_text("not a fixture")
            unrelated.chmod(0o600)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)
            proxy.allow_peer_fixture_reads(path)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o755)
            for name in names:
                self.assertEqual(stat.S_IMODE((path / name).stat().st_mode), 0o644)
                self.assertEqual((path / name).read_text(), "public test material")
            self.assertEqual(stat.S_IMODE(unrelated.stat().st_mode), 0o600)

    def test_peer_exit_surfaces_container_exit_and_last_http_response(self):
        state = subprocess.CompletedProcess([], 0, json.dumps({"Running": False, "ExitCode": 1}), "")
        with patch.object(proxy, "get", return_value=(503, b'{"code":"UPSTREAM_UNAVAILABLE"}')), \
                patch.object(proxy, "docker", return_value=state), patch.object(proxy.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "tls-peer exited \\(1\\).*HTTP 503.*UPSTREAM_UNAVAILABLE"):
                proxy.wait_status("/api/echo", 200)
            sleep.assert_not_called()

    def test_timeout_retains_last_connection_error(self):
        state = subprocess.CompletedProcess([], 0, json.dumps({"Running": True}), "")
        with patch.object(proxy, "get", side_effect=OSError("connection refused")), \
                patch.object(proxy, "docker", return_value=state), patch.object(proxy.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "never reached 200; last response: connection refused"):
                proxy.wait_status("/api/echo", 200, attempts=2)

    def test_diagnostics_are_best_effort_redacted_and_saved_for_failure(self):
        calls = []

        def docker(*args, **_kwargs):
            calls.append(args)
            if args[0] == "inspect":
                raise OSError("daemon diagnostic unavailable")
            return subprocess.CompletedProcess([], 1, "", "Bearer public-non-live-fixture")

        with tempfile.TemporaryDirectory() as folder, patch.object(proxy, "docker", side_effect=docker), \
                patch.object(proxy, "ROOT", Path(folder)), patch("builtins.print"):
            diagnostics = proxy.collect_diagnostics()
            proxy.write_record({"result": "FAIL", "diagnostics": diagnostics})
            contents = (Path(folder) / "artifacts/m4b/proxy.json").read_text()
            self.assertEqual(json.loads(contents)["result"], "FAIL")
            self.assertIn("daemon diagnostic unavailable", contents)
            self.assertIn("nginx-config", contents)
            self.assertIn("network", contents)
            self.assertNotIn("Bearer public-non-live-fixture", contents)
            self.assertTrue(any(args[:2] == ("logs", "--tail") for args in calls))
            self.assertFalse(any(".Env" in arg for args in calls for arg in args))


if __name__ == "__main__":
    unittest.main()
