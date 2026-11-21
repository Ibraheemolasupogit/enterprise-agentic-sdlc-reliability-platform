"""Mutation tests for the C5-F4 hosted trial workflow policy (local; not in CI discovery)."""

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
    trial, ci = yaml.load(trial_text, Loader=policy.TrialLoader), load(ci_text)
    if mutate:
        mutate(trial)
    if mutate_ci:
        mutate_ci(ci)
    policy.trial_policy(trial, trial_text, ci, ci_text)


def steps(trial):
    return job(trial)["steps"]


def job(trial):
    return trial["jobs"]["hosted-sast-trial"]


def move_after(trial, fragment, after):
    trial_steps = steps(trial)
    step = trial_steps.pop(find(trial, fragment))
    trial_steps.insert(find(trial, after) + 1, step)


def find(trial, fragment):
    """Index of the single step whose `run` contains `fragment`, or whose `uses` starts with it."""
    hits = [i for i, s in enumerate(steps(trial)) if fragment in s.get("run", "") or s.get("uses", "").startswith(fragment)]
    assert len(hits) == 1, (fragment, hits)
    return hits[0]


class TrialWorkflowPolicy(unittest.TestCase):
    def test_current_trial_passes(self):
        check()

    def rejects(self, **kwargs):
        with self.assertRaises((policy.Violation, KeyError, StopIteration, ValueError, TypeError)):
            check(**kwargs)

    def test_rejects_automatic_triggers(self):
        for event in ("push", "pull_request", "pull_request_target", "merge_group",
                      "schedule", "workflow_run", "repository_dispatch", "workflow_call"):
            with self.subTest(event=event):
                self.rejects(mutate=lambda t, e=event: t["on"].update({e: {"branches": ["main"]}}))
        self.rejects(mutate=lambda t: t["on"].pop("workflow_dispatch"))

    def test_rejects_permission_escalation(self):
        self.rejects(mutate=lambda t: t.update(permissions={"contents": "write"}))
        self.rejects(mutate=lambda t: t.pop("permissions"))
        self.rejects(mutate=lambda t: t["permissions"].update({"id-token": "write"}))
        self.rejects(mutate=lambda t: job(t).update(permissions={"security-events": "write"}))
        self.rejects(mutate=lambda t: job(t).update(permissions={"contents": "write"}))

    def test_rejects_weakened_trusted_job_condition(self):
        self.rejects(mutate=lambda t: job(t).pop("if"))
        for original, replacement in (
            ("'workflow_dispatch'", "'push'"),
            ("'refs/heads/main'", "'refs/tags/main'"),
            ("'refs/heads/main'", "'refs/heads/topic'"),
            ("'1439889276'", "'1439889277'"),
            ("'181765037'", "'181765038'"),
            ("github.actor_id == github.repository_owner_id &&", ""),
            ("github.actor == github.repository_owner &&", ""),
            ("github.triggering_actor == github.repository_owner &&", ""),
            ("github.event.repository.private == true", "true"),
            ("&&", "||"),
        ):
            with self.subTest(original=original, replacement=replacement):
                self.rejects(mutate=lambda t, a=original, b=replacement: job(t).update(
                    {"if": job(t)["if"].replace(a, b, 1)}))
        self.rejects(mutate=lambda t: job(t).update({"if": "${{ always() }}"}))
        self.rejects(trial_text=TRIAL_TEXT.replace("    runs-on: ubuntu-24.04",
                                                   "    if: ${{ always() }}\n    runs-on: ubuntu-24.04"))

    def test_rejects_checkout_target_overrides(self):
        for key, value in (("ref", "refs/heads/topic"), ("repository", "other/repository"),
                           ("path", "elsewhere"), ("token", "injected")):
            with self.subTest(key=key):
                self.rejects(mutate=lambda t, k=key, v=value: steps(t)[1]["with"].update({k: v}))
        self.rejects(mutate=lambda t: steps(t).append(dict(steps(t)[1])))

    def test_rejects_missing_conditional_or_replaced_trust_step(self):
        self.rejects(mutate=lambda t: steps(t).pop(2))
        self.rejects(mutate=lambda t: steps(t).append(dict(steps(t)[2])))
        for fields in ({"if": "false"}, {"continue-on-error": "true"}, {"shell": "bash"},
                       {"working-directory": "elsewhere"}, {"run": "echo trust-check"},
                       {"run": policy.TRUST_RUN + " || true"}):
            with self.subTest(fields=fields):
                self.rejects(mutate=lambda t, f=fields: steps(t)[2].update(f))

    def test_rejects_work_before_trust_or_after_rejection(self):
        for fragment in ("hosted_trial.py facts", "actions/setup-node@", "npm ci --ignore-scripts",
                         " -m pip download", "hosted_trial.py container-build", "hosted_trial.py container-install",
                         "hosted_trial.py container-run"):
            with self.subTest(fragment=fragment):
                self.rejects(mutate=lambda t, f=fragment: move_after(t, "hosted_trial.py trust-check", f))
        self.rejects(mutate=lambda t: steps(t).insert(2, {"run": "echo before trust"}))
        self.rejects(mutate=lambda t: steps(t)[0].update(run="echo before trust\n" + steps(t)[0]["run"]))
        for fragment in ("actions/setup-node@", "npm ci --ignore-scripts", " -m pip download",
                         "hosted_trial.py container-build", "hosted_trial.py container-run"):
            with self.subTest(fragment=fragment, conditional="always"):
                self.rejects(mutate=lambda t, f=fragment: steps(t)[find(t, f)].update({"if": "always()"}))

    def test_rejects_trust_environment_overrides(self):
        for key in ("GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "GITHUB_REF",
                    "GITHUB_REPOSITORY_ID", "GITHUB_REPOSITORY_OWNER_ID", "GITHUB_ACTOR_ID",
                    "GITHUB_TRIGGERING_ACTOR", "RUNNER_ENVIRONMENT", "PATH", "BASH_ENV", "LD_PRELOAD"):
            with self.subTest(key=key):
                self.rejects(mutate=lambda t, k=key: t.update(env={k: "override"}))
                self.rejects(mutate=lambda t, k=key: job(t).update(env={k: "override"}))
                self.rejects(mutate=lambda t, k=key: steps(t)[2].update(env={k: "override"}))
                self.rejects(mutate=lambda t, k=key: steps(t)[0]["env"].update({k: "override"}))
                self.rejects(mutate=lambda t, k=key: steps(t)[find(t, "hosted_trial.py container-run")]["env"].update(
                    {k: "override"}))

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
            build, install = find(t, "hosted_trial.py container-build"), find(t, "hosted_trial.py container-install")
            s[build], s[install] = s[install], s[build]
        self.rejects(mutate=swap)
        self.rejects(mutate=lambda t: steps(t).insert(7, {"run": "python3 -I scripts/sast/hosted_trial.py run --semgrep x"}))
        def override_isolation(t):
            steps(t)[find(t, "hosted_trial.py container-run")]["run"] += " --isolation auto"
        self.rejects(mutate=override_isolation)
        self.rejects(mutate=lambda t: steps(t)[find(t, "hosted_trial.py summarize")].pop("if"))
        self.rejects(mutate=lambda t: steps(t).pop(find(t, "hosted_trial.py container-install")))

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
        for reference in ("${{ secrets.TRIAL }}", "${{ SeCrEtS['TRIAL'] }}"):
            self.rejects(trial_text=TRIAL_TEXT.replace("${{ inputs.confirm }}", reference))

    def test_rejects_private_or_broad_uploads(self):
        for path in ("artifacts/sast-private/c5/source-1.json", "artifacts/sast/", "artifacts/**", "artifacts/m3/x.json"):
            self.rejects(mutate=lambda t, p=path: steps(t)[-1]["with"].update(path=p))
        self.rejects(mutate=lambda t: steps(t)[-1].pop("if"))
        self.rejects(mutate=lambda t: steps(t)[-1]["with"].update({"retention-days": "90"}))

    def test_rejects_harness_before_verified_install(self):
        def swap(t):  # by content, not position (C5-G4H inserted steps before the download)
            s = steps(t)
            a, b = find(t, " -m pip download"), find(t, "hosted_trial.py container-install")
            s[a], s[b] = s[b], s[a]
        self.rejects(mutate=swap)

    def test_trial_stays_non_blocking(self):
        self.rejects(mutate_ci=lambda c: c["jobs"]["required"]["needs"].append("hosted-sast-trial"))
        self.rejects(ci_text=CI_TEXT + "# c5-sast-hosted-trial\n")


class HostedTypeScriptGatePolicy(unittest.TestCase):
    """C5-G4H: pinned Node + lock-verified compiler + TypeScript preflight, all before any container."""

    def rejects(self, **kwargs):
        with self.assertRaises((policy.Violation, KeyError, StopIteration, ValueError, TypeError, AssertionError)):
            check(**kwargs)

    def test_current_layout(self):
        t = load(TRIAL_TEXT)
        order = [find(t, "actions/setup-node@"), find(t, "npm ci --ignore-scripts"),
                 find(t, "hosted_trial.py typescript-preflight"), find(t, " -m pip download"),
                 find(t, "hosted_trial.py container-build"), find(t, "hosted_trial.py container-install"),
                 find(t, "hosted_trial.py container-run")]
        self.assertEqual(order, sorted(order))
        node = steps(t)[order[0]]
        self.assertEqual(node["with"], {"node-version": (ROOT / "apps/octocat-supply/.node-version").read_text().strip(),
                                        "package-manager-cache": "false"})
        self.assertEqual(node["uses"].split("@")[1].split()[0], "249970729cb0ef3589644e2896645e5dc5ba9c38")
        self.assertEqual(steps(t)[order[1]]["working-directory"], "apps/octocat-supply")
        for i in (order[2], order[6]):
            self.assertIn('--node "$(command -v node)"', steps(t)[i]["run"])
        upload = [s for s in steps(t) if s.get("uses", "").startswith("actions/upload-artifact@")][0]
        self.assertEqual(len([p for p in upload["with"]["path"].splitlines() if p.strip()]), 6)

    def test_rejects_missing_unpinned_or_loose_setup_node(self):
        self.rejects(mutate=lambda t: steps(t).pop(find(t, "actions/setup-node@")))
        self.rejects(mutate=lambda t: steps(t)[find(t, "actions/setup-node@")].update(uses="actions/setup-node@v6"))
        self.rejects(mutate=lambda t: steps(t)[find(t, "actions/setup-node@")].update(uses="actions/setup-node@" + "c" * 40))
        for extra in ({"cache": "npm"}, {"registry-url": "https://example.invalid"}, {"token": "x"},
                      {"check-latest": "true"}, {"always-auth": "true"}):
            with self.subTest(extra=extra):
                self.rejects(mutate=lambda t, e=extra: steps(t)[find(t, "actions/setup-node@")]["with"].update(e))
        # setup-node v6 enables package-manager caching by default: the explicit opt-out is mandatory.
        self.rejects(mutate=lambda t: steps(t)[find(t, "actions/setup-node@")]["with"].pop("package-manager-cache"))
        for value in ("true", "", "False ", "0", "npm"):
            with self.subTest(package_manager_cache=value):
                self.rejects(mutate=lambda t, v=value: steps(t)[find(t, "actions/setup-node@")]["with"].update(
                    {"package-manager-cache": v}))
        for version in ("24", "24.x", "lts/*", "24.22.1", "22.17.1"):
            with self.subTest(version=version):
                self.rejects(mutate=lambda t, v=version: steps(t)[find(t, "actions/setup-node@")]["with"].update(
                    {"node-version": v}))
        self.rejects(mutate=lambda t: steps(t)[find(t, "actions/setup-node@")].update(
            {"with": {"node-version-file": "apps/octocat-supply/.node-version"}}))
        self.rejects(mutate=lambda t: steps(t).insert(2, dict(steps(t)[find(t, "actions/setup-node@")])))
        with self.assertRaises(policy.Violation):  # .node-version itself must be exact
            check_with_node_version("24")

    def test_rejects_weakened_or_extra_npm_install(self):
        def set_run(t, text):
            steps(t)[find(t, "npm ci --ignore-scripts")]["run"] = text
        for text in ("npm ci", "npm install --ignore-scripts", "npm ci --ignore-scripts && npm run build",
                     "npm ci --ignore-scripts --registry https://example.invalid", "npx --yes typescript@latest tsc",
                     "yarn install --frozen-lockfile", "pnpm install --frozen-lockfile"):
            with self.subTest(run=text):
                self.rejects(mutate=lambda t, x=text: set_run(t, x))
        self.rejects(mutate=lambda t: steps(t)[find(t, "npm ci --ignore-scripts")].pop("working-directory"))
        self.rejects(mutate=lambda t: steps(t)[find(t, "npm ci --ignore-scripts")].update({"working-directory": "."}))
        self.rejects(mutate=lambda t: steps(t)[find(t, "npm ci --ignore-scripts")]["env"].update(
            {"NPM_CONFIG_REGISTRY": "https://example.invalid"}))
        self.rejects(mutate=lambda t: steps(t)[find(t, "npm ci --ignore-scripts")]["env"].update(
            {"NODE_OPTIONS": "--require /tmp/x.js"}))
        self.rejects(mutate=lambda t: steps(t).insert(find(t, "hosted_trial.py container-run"),
                                                      {"run": "npm ci --ignore-scripts", "working-directory": "apps/octocat-supply"}))
        self.rejects(mutate=lambda t: steps(t).pop(find(t, "npm ci --ignore-scripts")))

    def test_rejects_missing_or_unpinned_preflight_and_scan_node(self):
        self.rejects(mutate=lambda t: steps(t).pop(find(t, "hosted_trial.py typescript-preflight")))
        self.rejects(mutate=lambda t: steps(t)[find(t, "hosted_trial.py typescript-preflight")].update(
            run="python3 -I scripts/sast/hosted_trial.py typescript-preflight --node /usr/local/bin/node"))
        self.rejects(mutate=lambda t: steps(t)[find(t, "hosted_trial.py container-run")].update(
            run=steps(t)[find(t, "hosted_trial.py container-run")]["run"].replace(' --node "$(command -v node)"', "")))
        self.rejects(mutate=lambda t: steps(t)[find(t, "hosted_trial.py typescript-preflight")].update(
            {"continue-on-error": "true"}), trial_text=TRIAL_TEXT + "\n# continue-on-error: true\n")

    def test_rejects_any_reordering_after_container_work_starts(self):
        for fragment in ("actions/setup-node@", "npm ci --ignore-scripts", "hosted_trial.py typescript-preflight"):
            for after in (" -m pip download", "hosted_trial.py container-build", "hosted_trial.py container-run"):
                with self.subTest(step=fragment, after=after):
                    self.rejects(mutate=lambda t, f=fragment, a=after: move_after(t, f, a))

        def preflight_before_install(t):
            s = steps(t)
            a, b = find(t, "npm ci --ignore-scripts"), find(t, "hosted_trial.py typescript-preflight")
            s[a], s[b] = s[b], s[a]
        self.rejects(mutate=preflight_before_install)

    def test_rejects_path_or_env_injection_between_preflight_and_scan(self):
        for line in ('echo "/tmp/evil" >> "$GITHUB_PATH"', 'echo "NODE_OPTIONS=--require /tmp/x" >> "$GITHUB_ENV"'):
            with self.subTest(line=line):
                text = TRIAL_TEXT + f"\n# {line}\n"
                self.rejects(trial_text=text, mutate=lambda t, x=line: steps(t).insert(
                    find(t, "hosted_trial.py container-run"), {"run": x}))

    def test_artifact_allowlist_is_exactly_six_files(self):
        def upload(t):
            return [s for s in steps(t) if s.get("uses", "").startswith("actions/upload-artifact@")][0]["with"]

        def edit(t, change):
            paths = [p.strip() for p in upload(t)["path"].splitlines() if p.strip()]
            upload(t)["path"] = "\n".join(change(paths)) + "\n"
        for name, change in (("add attestation", lambda p: p + ["artifacts/sast/ts-syntax-gate.json"]),
                             ("add compiler", lambda p: p + ["apps/octocat-supply/node_modules/typescript/lib/typescript.js"]),
                             ("drop one", lambda p: p[:-1]), ("reorder", lambda p: list(reversed(p))),
                             ("private", lambda p: p[:-1] + ["artifacts/sast-private/c5/source-1.json"])):
            with self.subTest(change=name):
                self.rejects(mutate=lambda t, c=change: edit(t, c))


def check_with_node_version(version):
    trial, ci = load(TRIAL_TEXT), load(CI_TEXT)
    policy.trial_policy(trial, TRIAL_TEXT, ci, CI_TEXT, node_version=version)


if __name__ == "__main__":
    unittest.main()
