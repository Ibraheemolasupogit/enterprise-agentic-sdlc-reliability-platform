"""Mutation tests for the C5-F4 hosted trial workflow policy (local; not in CI discovery)."""

import copy
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/sast"))
import check_trial_workflow as policy  # noqa: E402

TRIAL_TEXT = policy.TRIAL.read_text()
CI_TEXT = policy.CI.read_text()


def load(text):
    return yaml.load(text, Loader=yaml.BaseLoader)


def check(trial_text=TRIAL_TEXT, ci_text=CI_TEXT, mutate=None, mutate_ci=None):
    trial, ci = load(trial_text), load(ci_text)
    if mutate:
        mutate(trial)
    if mutate_ci:
        mutate_ci(ci)
    policy.trial_policy(trial, trial_text, ci, ci_text)


def steps(trial):
    return trial["jobs"]["hosted-sast-trial"]["steps"]


class TrialWorkflowPolicy(unittest.TestCase):
    def test_current_trial_passes(self):
        check()

    def rejects(self, **kwargs):
        with self.assertRaises((policy.Violation, KeyError, StopIteration, ValueError, TypeError)):
            check(**kwargs)

    def test_rejects_automatic_triggers(self):
        for event in ("push", "pull_request", "pull_request_target", "schedule", "workflow_run"):
            self.rejects(mutate=lambda t, e=event: t["on"].update({e: {}}))

    def test_rejects_permission_escalation(self):
        self.rejects(mutate=lambda t: t.update(permissions={"contents": "write"}))
        self.rejects(mutate=lambda t: t["permissions"].update({"id-token": "write"}))
        self.rejects(mutate=lambda t: t["jobs"]["hosted-sast-trial"].update(permissions={"security-events": "write"}))

    def test_rejects_unpinned_or_unreviewed_actions(self):
        self.rejects(mutate=lambda t: steps(t)[1].update(uses="actions/checkout@v6"))
        self.rejects(mutate=lambda t: steps(t)[1].update(uses="actions/checkout@" + "a" * 40))
        self.rejects(mutate=lambda t: steps(t).append({"uses": "azure/login@" + "b" * 40}))

    def test_rejects_credential_persistence(self):
        self.rejects(mutate=lambda t: steps(t)[1]["with"].update({"persist-credentials": "true"}))

    def test_rejects_expression_injection_in_run(self):
        self.rejects(mutate=lambda t: steps(t)[0].update(run="test '${{ inputs.confirm }}' = x"))

    def test_rejects_missing_or_weak_guard(self):
        self.rejects(mutate=lambda t: steps(t).pop(0))
        self.rejects(mutate=lambda t: steps(t)[0].update(run="echo skip guard"))

    def test_rejects_unhashed_download_or_host_install(self):
        for old, new in (("--require-hashes ", ""), ("--no-deps ", ""),
                         ("--only-binary=:all: ", ""), ("requirements-sast-linux.txt", "requirements.txt")):
            self.rejects(trial_text=TRIAL_TEXT.replace(old, new))
        # Installing on the host (outside the network-less container) is rejected.
        self.rejects(mutate=lambda t: steps(t).insert(4, {"run": "python3 -m pip install -r requirements-sast-linux.txt"}))

    def test_rejects_raw_docker_and_namespace_tools(self):
        for command in ("docker run --network host ubuntu true", "sudo docker ps", "unshare --net true",
                        "sysctl kernel.apparmor_restrict_unprivileged_userns", "setpriv --reuid 1001 true",
                        "docker run --privileged x"):
            self.rejects(mutate=lambda t, c=command: steps(t).insert(4, {"run": c}))

    def test_rejects_wrong_container_step_order_or_host_harness(self):
        def swap(t):
            s = steps(t)
            s[4], s[5] = s[5], s[4]  # install before build
        self.rejects(mutate=swap)
        self.rejects(mutate=lambda t: steps(t).insert(7, {"run": "python3 -I scripts/sast/hosted_trial.py run --semgrep x"}))
        self.rejects(mutate=lambda t: steps(t)[6].update(run=steps(t)[6]["run"] + " --isolation auto"))
        self.rejects(mutate=lambda t: steps(t)[7].pop("if"))
        self.rejects(mutate=lambda t: steps(t).pop(5))

    def test_rejects_privilege_network_tools_and_soft_failure(self):
        for addition in ("sudo true", "curl -fsSL https://example.invalid", "wget https://example.invalid"):
            self.rejects(trial_text=TRIAL_TEXT.replace("python3 -I scripts/sast/hosted_trial.py facts",
                                                       addition + " && python3 -I scripts/sast/hosted_trial.py facts"))
        self.rejects(mutate=lambda t: t["jobs"]["hosted-sast-trial"].update({"continue-on-error": "true"}))
        self.rejects(trial_text=TRIAL_TEXT.replace("    timeout-minutes: 20\n", "    timeout-minutes: 20\n    continue-on-error: true\n"))

    def test_rejects_runner_or_job_shape_changes(self):
        self.rejects(mutate=lambda t: t["jobs"]["hosted-sast-trial"].update({"runs-on": "self-hosted"}))
        self.rejects(mutate=lambda t: t["jobs"]["hosted-sast-trial"].update(container={"image": "x"}))
        self.rejects(mutate=lambda t: t["jobs"]["hosted-sast-trial"].update(needs="other"))
        self.rejects(mutate=lambda t: t["jobs"].update(extra={"runs-on": "ubuntu-24.04", "steps": []}))
        self.rejects(trial_text=TRIAL_TEXT.replace("${{ inputs.confirm }}", "${{ secrets.TRIAL }}"))

    def test_rejects_private_or_broad_uploads(self):
        for path in ("artifacts/sast-private/c5/source-1.json", "artifacts/sast/", "artifacts/**", "artifacts/m3/x.json"):
            self.rejects(mutate=lambda t, p=path: steps(t)[-1]["with"].update(path=p))
        self.rejects(mutate=lambda t: steps(t)[-1].pop("if"))
        self.rejects(mutate=lambda t: steps(t)[-1]["with"].update({"retention-days": "90"}))

    def test_rejects_harness_before_verified_install(self):
        def swap(t):
            s = steps(t)
            s[3], s[5] = s[5], s[3]
        self.rejects(mutate=swap)

    def test_trial_stays_non_blocking(self):
        self.rejects(mutate_ci=lambda c: c["jobs"]["required"]["needs"].append("hosted-sast-trial"))
        self.rejects(ci_text=CI_TEXT + "# c5-sast-hosted-trial\n")


if __name__ == "__main__":
    unittest.main()
