"""Offline verification of retained and synthetic C5 trial evidence."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import warnings
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/sast/verify_trial_artifact.py"
MANIFEST = ROOT / "security/sast/approved-trial-inputs.json"
HISTORY = Path(__file__).parent / "fixtures/g4h-run-44393309563.zip"
HISTORY_DIGEST = "sha256:388dc3baca1ba774e1a708514791aed36b45fca9d10ce0928af60c4cdf4e0cf8"
BASELINE = "cde7b64f11c0ce7b4a67a603156ab7f221219527"
PRE_P2 = "8f89d4125a1546ad01b2dfd2af4731ae128d1c4e"
RUN_ID = 101010
CONTAINER_FILES = ("container-image.json", "container-install.json", "container-run.json")

spec = importlib.util.spec_from_file_location("p3_verifier", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TrialArtifactTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / "trial.zip"
        self.manifest_path = self.root / "manifest.json"
        self.metadata_path = self.root / "run.json"
        self.manifest = json.loads(MANIFEST.read_bytes())
        self.assertEqual(self.manifest["baseline_commit"], BASELINE)
        with zipfile.ZipFile(HISTORY) as archive:
            self.records = {entry.filename: json.loads(archive.read(entry)) for entry in archive.infolist()}
        for facts in (self.records["hosted-runner-facts.json"], self.trial["facts"]):
            facts["github"]["GITHUB_SHA"] = BASELINE
            facts["github"]["GITHUB_RUN_ID"] = str(RUN_ID)
        self.trial["input_sha256sum"] = [
            f"{digest}  {path}" for path, digest in self.manifest["inputs"].items()
        ]
        identity = {"id": 181765037, "login": "Ibraheemolasupogit"}
        repository = {
            "id": 1439889276, "full_name": "Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform",
            "owner": identity, "private": True, "fork": False,
        }
        self.metadata = {
            "id": RUN_ID, "run_attempt": 1, "head_sha": BASELINE, "head_branch": "main",
            "event": "workflow_dispatch", "path": ".github/workflows/c5-sast-hosted-trial.yml@main",
            "status": "completed", "conclusion": "success", "repository": deepcopy(repository),
            "head_repository": deepcopy(repository), "actor": deepcopy(identity), "triggering_actor": deepcopy(identity),
        }
        for name in CONTAINER_FILES:
            self.records[name]["trusted_input"] = {
                "mode": "hosted", "trusted": True, "event": "workflow_dispatch", "ref": "refs/heads/main",
                "repository_id": 1439889276, "actor_id": 181765037,
            }

    @property
    def trial(self):
        return self.records["hosted-trial.json"]

    def write_trial(self, members=None):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.metadata_path.write_text(json.dumps(self.metadata), encoding="utf-8")
        if members is None:
            members = [(name, json.dumps(record)) for name, record in self.records.items()]
        with zipfile.ZipFile(self.archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in members:
                archive.writestr(name, data)

    def verify(self, expected_digest=None, main_tip=BASELINE):
        return verifier.verify(self.archive, expected_digest or sha(self.archive), ROOT, main_tip,
                               self.manifest_path, self.metadata_path)

    def rejects(self, reason, main_tip=BASELINE):
        self.write_trial()
        with self.assertRaisesRegex(verifier.Rejected, reason):
            self.verify(main_tip=main_tip)

    def test_real_historical_archive_has_separate_integrity_result(self):
        proc = subprocess.run([
            sys.executable, "-I", str(SCRIPT), str(HISTORY), "--expected-digest", HISTORY_DIGEST,
            "--git-repo", str(ROOT), "--main-tip", BASELINE, "--historical-run-1",
        ], capture_output=True, text=True, check=True)
        self.assertIn("Historical integrity verified for run 44393309563/1", proc.stdout)
        self.assertIn("Current trust policy was not evaluated", proc.stdout)
        self.assertNotIn("P3 trust policy passed", proc.stdout)

    def test_valid_current_archive_offline(self):
        self.write_trial()
        self.assertEqual(self.verify(), (RUN_ID, 1, BASELINE))

    def test_historical_mode_cannot_accept_a_current_archive(self):
        self.write_trial()
        with self.assertRaisesRegex(verifier.Rejected, "limited to the original"):
            verifier.verify(self.archive, sha(self.archive), ROOT, BASELINE, historical=True)

    def test_current_mode_requires_independent_run_metadata(self):
        with self.assertRaisesRegex(verifier.Rejected, "independent GitHub"):
            verifier.verify(HISTORY, HISTORY_DIGEST, ROOT, BASELINE, MANIFEST)

    def test_archive_digest_is_checked_before_opening_zip(self):
        self.write_trial()
        self.archive.write_bytes(b"not a ZIP")
        with self.assertRaisesRegex(verifier.Rejected, "archive SHA-256 mismatch"):
            self.verify("0" * 64)

    def test_missing_and_seventh_member(self):
        valid = [(name, json.dumps(value)) for name, value in self.records.items()]
        for members in (valid[:-1], valid + [("seventh.json", "{}")]):
            with self.subTest(count=len(members)):
                self.write_trial(members)
                with self.assertRaisesRegex(verifier.Rejected, "exactly six"):
                    self.verify()

    def test_duplicate_zip_member(self):
        valid = [(name, json.dumps(value)) for name, value in self.records.items()]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.write_trial(valid[:-1] + [valid[0]])
        with self.assertRaisesRegex(verifier.Rejected, "duplicate path"):
            self.verify()

    def test_malicious_archive_paths(self):
        valid = [(name, json.dumps(value)) for name, value in self.records.items()]
        for name in ("../c5-summary.json", "/c5-summary.json", "nested/c5-summary.json",
                     r"..\c5-summary.json", "C:/c5-summary.json", "C5-SUMMARY.JSON", "unrelated.json"):
            with self.subTest(path=name):
                self.write_trial(valid[:-1] + [(name, "{}")])
                with self.assertRaisesRegex(verifier.Rejected, "unexpected, unsafe"):
                    self.verify()

    def test_zip_symlink_with_allowlisted_name(self):
        valid = [(name, json.dumps(value)) for name, value in self.records.items()]
        name, data = valid[-1]
        symlink = zipfile.ZipInfo(name)
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.write_trial(valid[:-1] + [(symlink, data)])
        with self.assertRaisesRegex(verifier.Rejected, "irregular"):
            self.verify()

    def test_malformed_json_duplicate_keys_and_non_finite_numbers(self):
        valid = [(name, json.dumps(value)) for name, value in self.records.items()]
        for data in (b'{"schema"', b"\xff", '{"a":0,"a":1}', '{"a":NaN}', '{"a":1e999}', "[]"):
            with self.subTest(data=data):
                self.write_trial(valid[:-1] + [(valid[-1][0], data)])
                with self.assertRaisesRegex(verifier.Rejected, "JSON"):
                    self.verify()

    def test_modified_recorded_hash(self):
        line = self.trial["input_sha256sum"][0]
        self.trial["input_sha256sum"][0] = "0" * 64 + line[64:]
        self.rejects("recorded input hashes differ")

    def test_missing_unexpected_and_duplicate_recorded_inputs(self):
        inputs = self.trial["input_sha256sum"]
        for lines in (inputs[:-1], inputs[:-1] + ["0" * 64 + "  unexpected"], inputs[:-1] + inputs[:1]):
            with self.subTest(lines=len(lines)):
                self.trial["input_sha256sum"] = lines
                self.rejects("recorded input")

    def test_approval_manifest_requires_exact_git_baseline_inputs(self):
        path = "scripts/sast/feasibility.py"
        original = self.manifest["inputs"].copy()
        for changed in (
            {k: v for k, v in original.items() if k != path},
            {**original, "unexpected.py": "0" * 64},
            {**original, path: "0" * 64},
        ):
            with self.subTest(inputs=len(changed)):
                self.manifest["inputs"] = changed
                self.rejects("manifest input set or hashes")

    def test_approval_pins_p1_configuration(self):
        self.manifest["trusted_inputs_sha256"] = "0" * 64
        self.rejects("P1 trust-config digest")

    def test_git_rejects_run_before_current_approval(self):
        self.metadata["head_sha"] = PRE_P2
        for facts in (self.records["hosted-runner-facts.json"], self.trial["facts"]):
            facts["github"]["GITHUB_SHA"] = PRE_P2
        self.rejects("merge-base")

    def test_git_rejects_run_outside_independent_main_tip(self):
        self.rejects("merge-base", main_tip=PRE_P2)

    def test_git_does_not_accept_forged_recorded_hashes_at_changed_run_commit(self):
        self.manifest["baseline_commit"] = PRE_P2
        output = subprocess.check_output(
            ["git", "show", f"{PRE_P2}:.github/workflows/c5-sast-hosted-trial.yml"], cwd=ROOT)
        self.manifest["inputs"][".github/workflows/c5-sast-hosted-trial.yml"] = hashlib.sha256(output).hexdigest()
        self.trial["input_sha256sum"] = [f"{v}  {k}" for k, v in self.manifest["inputs"].items()]
        self.rejects("run commit changed approved input")

    def test_metadata_rejects_wrong_commit_branch_event_attempt_and_workflow(self):
        for key, bad in (
            ("head_sha", "0" * 40), ("head_branch", "feature"), ("event", "push"),
            ("run_attempt", 2), ("id", True), ("path", ".github/workflows/ci.yml"),
            ("status", "in_progress"), ("conclusion", "failure"),
        ):
            with self.subTest(field=key):
                previous = self.metadata[key]
                self.metadata[key] = bad
                self.rejects("metadata|GitHub context|unexpected workflow")
                self.metadata[key] = previous

    def test_metadata_rejects_wrong_repository_owner_and_actors(self):
        for group, key, value in (
            ("repository", "id", 2), ("head_repository", "fork", True), ("repository", "private", False),
            ("repository", "owner", {"id": 2}), ("head_repository", "full_name", "other/repository"),
            ("actor", "id", 2), ("actor", "login", "different"), ("triggering_actor", "id", None),
            ("triggering_actor", "login", "different"),
        ):
            with self.subTest(group=group, field=key):
                previous = self.metadata[group][key]
                self.metadata[group][key] = value
                self.rejects("GitHub")
                self.metadata[group][key] = previous

    def test_contradictory_container_facts_or_ref(self):
        self.trial["facts"]["github"]["GITHUB_REF"] = "refs/heads/feature"
        self.rejects("container runner facts")
        self.records["hosted-runner-facts.json"]["github"]["GITHUB_REF"] = "refs/heads/feature"
        self.rejects("runner GitHub context")

    def test_missing_p1_decision_in_each_container_record(self):
        for name in CONTAINER_FILES:
            with self.subTest(file=name):
                previous = self.records[name].pop("trusted_input")
                self.rejects("P1 decision")
                self.records[name]["trusted_input"] = previous

    def test_failed_or_contradictory_p1_decision(self):
        record = self.records["container-run.json"]["trusted_input"]
        for key, bad in (("trusted", False), ("trusted", 1), ("mode", "local"), ("actor_id", 2), ("reason", "failed")):
            with self.subTest(field=key, value=bad):
                self.records["container-run.json"]["trusted_input"] = {**record, key: bad}
                self.rejects("P1 decision")

    def test_nonce_summary_and_exit_contradictions_are_rejected(self):
        for file, key, bad in (
            ("container-run.json", "nonce", "f" * 32),
            ("hosted-trial.json", "harness_exit", 2),
            ("c5-summary.json", "semgrep_core_sha256", "0" * 64),
            ("container-install.json", "exit", False),
            ("container-run.json", "hardening", ["--network", "host"]),
        ):
            with self.subTest(file=file, field=key):
                previous = self.records[file][key]
                self.records[file][key] = bad
                self.rejects(f"invalid {key}")
                self.records[file][key] = previous

    def test_cli_failure_is_nonzero_and_never_reports_policy_pass(self):
        self.write_trial()
        proc = subprocess.run([
            sys.executable, "-I", str(SCRIPT), str(self.archive), "--expected-digest", "0" * 64,
            "--git-repo", str(ROOT), "--main-tip", BASELINE, "--manifest", str(self.manifest_path),
            "--run-metadata", str(self.metadata_path),
        ], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("archive SHA-256 mismatch", proc.stderr)
        self.assertNotIn("P3 trust policy passed", proc.stdout)


if __name__ == "__main__":
    unittest.main()
