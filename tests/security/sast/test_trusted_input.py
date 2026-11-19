"""C5 R2(a) P1 trusted-input enforcement tests (local; not in CI discovery; no network, Docker or Semgrep).

Synthetic GitHub Actions environments and workflow_dispatch payloads exercise the driver's fail-closed
check. Rejected paths must exit 2 before any subprocess (Node, pip, Docker or the Semgrep harness) runs.
Payload shape follows the canonical workflow_dispatch schema (octokit/webhooks): required inputs, ref,
repository (id, fork, private, owner{id, login}), sender (id, login) and workflow.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/sast"))
import hosted_trial as driver  # noqa: E402

PINS = json.loads((ROOT / "security/sast/trusted-inputs.json").read_text())
REPO_ID, OWNER_ID = PINS["repository_id"], PINS["repository_owner_id"]
OWNER = "owner-login"  # synthetic login; the trust decision rests on the pinned numeric IDs


class Context:
    """Builds a valid hosted context (environment + event payload file) that individual tests then break."""

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.payload = {"inputs": {"confirm": "x", "authorization_reference": "y"}, "ref": "refs/heads/main",
                        "workflow": ".github/workflows/c5-sast-hosted-trial.yml",
                        "repository": {"id": REPO_ID, "full_name": f"{OWNER}/repo", "fork": False, "private": True,
                                       "owner": {"id": OWNER_ID, "login": OWNER}},
                        "sender": {"id": OWNER_ID, "login": OWNER}}
        self.env = {"GITHUB_ACTIONS": "true", "GITHUB_RUN_ID": "123", "GITHUB_EVENT_NAME": "workflow_dispatch",
                    "GITHUB_REF": "refs/heads/main", "GITHUB_REPOSITORY_ID": str(REPO_ID),
                    "GITHUB_REPOSITORY_OWNER": OWNER, "GITHUB_REPOSITORY_OWNER_ID": str(OWNER_ID),
                    "GITHUB_ACTOR": OWNER, "GITHUB_ACTOR_ID": str(OWNER_ID), "GITHUB_TRIGGERING_ACTOR": OWNER,
                    "RUNNER_ENVIRONMENT": "github-hosted", "GITHUB_WORKFLOW_REF": "o/r/.github/workflows/x.yml@refs/heads/main"}

    def write(self, payload=None, raw: bytes | None = None) -> dict:
        path = self.tmp / "event.json"
        path.write_bytes(raw if raw is not None else json.dumps(self.payload if payload is None else payload).encode())
        return {**self.env, "GITHUB_EVENT_PATH": str(path)}


class TrustedContext(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="c5-trust-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.ctx = Context(self.tmp)

    def rejects(self, env, pins_path=None):
        with self.assertRaises(driver.Fail) as caught:
            driver.trusted_context(env, pins_path)
        self.assertEqual(caught.exception.code, 2, str(caught.exception))
        return str(caught.exception)

    # ---- positive
    def test_owner_dispatch_on_main_is_trusted(self):
        result = driver.trusted_context(self.ctx.write())
        self.assertEqual(result, {"mode": "hosted", "trusted": True, "event": "workflow_dispatch",
                                  "ref": "refs/heads/main", "repository_id": REPO_ID, "actor_id": OWNER_ID})

    def test_local_development_is_preserved(self):
        self.assertEqual(driver.trusted_context({}), {"mode": "local", "trusted": True})
        # Tokens and unrelated variables never make a context hosted (and never establish trust).
        noise = {"ACTIONS_RUNTIME_TOKEN": "x", "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "x", "GITHUB_TOKEN": "x",
                 "GH_TOKEN": "x", "PATH": "/usr/bin:/bin", "HOME": "/tmp", "CI": "true"}
        self.assertEqual(driver.trusted_context(noise)["mode"], "local")

    def test_pinned_configuration_is_the_reviewed_one(self):
        pins = driver.load_trusted_inputs()
        self.assertEqual((pins["ref"], pins["events"], pins["require_private"]), ("refs/heads/main", ["workflow_dispatch"], True))
        self.assertTrue(driver._is_id(pins["repository_id"]) and driver._is_id(pins["repository_owner_id"]))

    # ---- events and refs
    def test_rejects_untrusted_events(self):
        for event in ("push", "pull_request", "pull_request_target", "schedule", "workflow_run", "merge_group",
                      "repository_dispatch", "workflow_call", "issue_comment", "WORKFLOW_DISPATCH", "workflow_dispatch "):
            with self.subTest(event=event):
                env = self.ctx.write()
                env["GITHUB_EVENT_NAME"] = event
                self.rejects(env)

    def test_rejects_untrusted_refs(self):
        for ref in ("refs/heads/feature", "refs/pull/1/merge", "refs/tags/v1", "refs/heads/main-evil", "refs/heads/Main",
                    "refs/heads/main ", "main", "refs/heads/main/x", "refs/remotes/origin/main"):
            with self.subTest(ref=ref):
                payload = dict(self.ctx.payload, ref=ref)
                env = self.ctx.write(payload)
                env["GITHUB_REF"] = ref
                self.rejects(env)

    # ---- repositories
    def test_rejects_untrusted_repositories(self):
        cases = {
            "env repository id": ({"GITHUB_REPOSITORY_ID": str(REPO_ID + 1)}, {}),
            "env owner id": ({"GITHUB_REPOSITORY_OWNER_ID": str(OWNER_ID + 1)}, {}),
            "payload repository id": ({}, {"repository": dict(self.ctx.payload["repository"], id=REPO_ID + 1)}),
            "payload fork": ({}, {"repository": dict(self.ctx.payload["repository"], fork=True)}),
            "payload fork flag missing": ({}, {"repository": {k: v for k, v in self.ctx.payload["repository"].items() if k != "fork"}}),
            "payload public": ({}, {"repository": dict(self.ctx.payload["repository"], private=False)}),
            "payload private as string": ({}, {"repository": dict(self.ctx.payload["repository"], private="true")}),
            "payload owner id": ({}, {"repository": dict(self.ctx.payload["repository"], owner={"id": OWNER_ID + 1, "login": OWNER})}),
            "payload owner login": ({}, {"repository": dict(self.ctx.payload["repository"], owner={"id": OWNER_ID, "login": "other"})}),
            "payload repository id as string": ({}, {"repository": dict(self.ctx.payload["repository"], id=str(REPO_ID))}),
            "payload repository id as bool": ({}, {"repository": dict(self.ctx.payload["repository"], id=True)}),
        }
        for name, (env_over, payload_over) in cases.items():
            with self.subTest(case=name):
                env = self.ctx.write(dict(self.ctx.payload, **payload_over))
                env.update(env_over)
                self.rejects(env)

    # ---- actors
    def test_rejects_untrusted_actors(self):
        cases = {
            "actor id": ({"GITHUB_ACTOR_ID": str(OWNER_ID + 1)}, {}),
            "actor login": ({"GITHUB_ACTOR": "someone-else"}, {}),
            "triggering actor (re-run by another user)": ({"GITHUB_TRIGGERING_ACTOR": "someone-else"}, {}),
            "bot triggering actor": ({"GITHUB_TRIGGERING_ACTOR": "github-actions[bot]"}, {}),
            "sender id": ({}, {"sender": {"id": OWNER_ID + 1, "login": OWNER}}),
            "sender login": ({}, {"sender": {"id": OWNER_ID, "login": "someone-else"}}),
            "sender missing": ({}, {"sender": None}),
        }
        for name, (env_over, payload_over) in cases.items():
            with self.subTest(case=name):
                env = self.ctx.write(dict(self.ctx.payload, **payload_over))
                env.update(env_over)
                self.rejects(env)

    # ---- missing, malformed and contradictory context
    def test_rejects_missing_hosted_context(self):
        full = self.ctx.write()
        for key in driver.HOSTED_REQUIRED:
            with self.subTest(missing=key):
                self.rejects({k: v for k, v in full.items() if k != key})
            with self.subTest(empty=key):
                self.rejects({**full, key: ""})

    def test_rejects_contradictory_markers(self):
        full = self.ctx.write()
        for value in (None, "false", "TRUE", "1", ""):
            with self.subTest(github_actions=value):
                env = {k: v for k, v in full.items() if k != "GITHUB_ACTIONS"}
                if value is not None:
                    env["GITHUB_ACTIONS"] = value
                self.rejects(env)
        for marker in driver.HOSTED_MARKERS:  # any single marker alone means hosted, so it must not pass as local
            with self.subTest(lone_marker=marker):
                self.rejects({marker: "x"})

    def test_rejects_malformed_ids_and_logins(self):
        for key, value in (("GITHUB_REPOSITORY_ID", "0"), ("GITHUB_REPOSITORY_ID", "-1"), ("GITHUB_REPOSITORY_ID", "12a"),
                           ("GITHUB_ACTOR_ID", f" {OWNER_ID}"), ("GITHUB_REPOSITORY_OWNER_ID", "1" * 25),
                           ("GITHUB_ACTOR", "a b"), ("GITHUB_REPOSITORY_OWNER", "-lead"), ("GITHUB_TRIGGERING_ACTOR", "x" * 40)):
            with self.subTest(key=key, value=value):
                self.rejects({**self.ctx.write(), key: value})

    def test_rejects_bad_event_payloads(self):
        good = self.ctx.write()
        cases = {"malformed JSON": b"{not json", "not an object": b"[]", "not UTF-8": b"\xff\xfe\x00",
                 "too large": b" " * (driver.MAX_EVENT_BYTES + 1)}
        for name, raw in cases.items():
            with self.subTest(case=name):
                self.rejects(self.ctx.write(raw=raw))
        for name, payload in {"ref contradicts GITHUB_REF": dict(self.ctx.payload, ref="refs/heads/other"),
                              "missing inputs": {k: v for k, v in self.ctx.payload.items() if k != "inputs"},
                              "missing workflow": {k: v for k, v in self.ctx.payload.items() if k != "workflow"},
                              "repository not an object": dict(self.ctx.payload, repository=[])}.items():
            with self.subTest(case=name):
                self.rejects(self.ctx.write(payload))
        with self.subTest(case="relative path"):
            self.rejects({**good, "GITHUB_EVENT_PATH": "event.json"})
        with self.subTest(case="missing file"):
            self.rejects({**good, "GITHUB_EVENT_PATH": str(self.tmp / "absent.json")})
        with self.subTest(case="symlink"):
            link = self.tmp / "link.json"
            link.symlink_to(self.tmp / "event.json")
            self.rejects({**good, "GITHUB_EVENT_PATH": str(link)})

    # ---- pinned configuration
    def test_rejects_altered_configuration(self):
        env = self.ctx.write()
        base = json.loads((ROOT / "security/sast/trusted-inputs.json").read_text())
        cases = {"extra key": dict(base, extra=1), "ref": dict(base, ref="refs/heads/dev"),
                 "push allowed": dict(base, events=["workflow_dispatch", "push"]), "id as string": dict(base, repository_id=str(REPO_ID)),
                 "id as bool": dict(base, repository_owner_id=True), "id zero": dict(base, repository_id=0),
                 "public allowed": dict(base, require_private=False), "schema": dict(base, schema="c5-trusted-inputs/2")}
        for name, pins in cases.items():
            with self.subTest(case=name):
                path = self.tmp / f"pins-{abs(hash(name))}.json"
                path.write_text(json.dumps(pins))
                self.rejects(env, path)
        with self.subTest(case="missing"):
            self.rejects(env, self.tmp / "absent.json")
        with self.subTest(case="symlink"):
            link = self.tmp / "pins-link.json"
            link.symlink_to(ROOT / "security/sast/trusted-inputs.json")
            self.rejects(env, link)
        with self.subTest(case="malformed"):
            bad = self.tmp / "pins-bad.json"
            bad.write_text("{")
            self.rejects(env, bad)


class SubcommandsFailClosed(unittest.TestCase):
    """Every hosted entry point refuses an untrusted context before any subprocess (Node, pip, Docker, harness)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="c5-trust-sub-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        out = self.tmp / "artifacts/sast"
        out.mkdir(parents=True)
        for name, path in (("OUT", out), ("IMAGE_EVIDENCE", out / "container-image.json"),
                           ("INSTALL_EVIDENCE", out / "container-install.json"), ("RUN_EVIDENCE", out / "container-run.json"),
                           ("TRIAL", out / "hosted-trial.json"), ("FACTS", out / "hosted-runner-facts.json")):
            patcher = mock.patch.object(driver, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.iid = self.tmp / "iid"
        self.iid.write_text("sha256:" + "a" * 64)
        (self.tmp / "wheels").mkdir()
        (self.tmp / "venv").mkdir()
        self.node = self.tmp / "node"
        self.node.write_text("#!/bin/sh\necho v24.22.2\n")
        self.node.chmod(0o755)
        self.ctx = Context(self.tmp)

    def untrusted_envs(self):
        good = self.ctx.write()
        yield "pull_request", {**good, "GITHUB_EVENT_NAME": "pull_request"}
        yield "branch", {**good, "GITHUB_REF": "refs/heads/feature"}
        yield "fork repository", {**good, "GITHUB_REPOSITORY_ID": str(REPO_ID + 1)}
        yield "other actor", {**good, "GITHUB_ACTOR_ID": str(OWNER_ID + 1)}
        yield "incomplete", {"GITHUB_ACTIONS": "true", "GITHUB_RUN_ID": "1"}
        yield "contradictory", {**good, "GITHUB_ACTIONS": "false"}

    def calls(self):
        return {"run": mock.patch.object(driver.subprocess, "run", side_effect=AssertionError("subprocess.run on a rejected path")),
                "popen": mock.patch.object(driver.subprocess, "Popen", side_effect=AssertionError("Popen on a rejected path")),
                "which": mock.patch.object(driver.shutil, "which", return_value="/usr/bin/docker")}

    def invoke(self, name):
        return {"typescript-preflight": lambda: driver.typescript_preflight(str(self.node)),
                "container-build": lambda: driver.container_build(str(self.tmp / "out.iid")),
                "container-install": lambda: driver.container_install(str(self.iid), str(self.tmp / "wheels"), str(self.tmp / "venv")),
                "container-run": lambda: driver.container_run(str(self.iid), str(self.tmp / "venv"), 1, str(self.node))}[name]()

    def test_each_entry_point_refuses_before_any_subprocess(self):
        evidence = {"container-build": driver.IMAGE_EVIDENCE, "container-install": driver.INSTALL_EVIDENCE,
                    "container-run": driver.RUN_EVIDENCE}
        for command in ("typescript-preflight", "container-build", "container-install", "container-run"):
            for label, env in self.untrusted_envs():
                with self.subTest(command=command, context=label):
                    patches = self.calls()
                    with mock.patch.dict(driver.os.environ, env, clear=True), patches["run"] as run, \
                            patches["popen"] as popen, patches["which"], mock.patch("builtins.print"):
                        self.assertEqual(self.invoke(command), 2)
                    run.assert_not_called()
                    popen.assert_not_called()
                    if command in evidence:
                        record = json.loads(evidence[command].read_text())
                        self.assertEqual((record["exit"], record["result"]), (2, "configuration-error"))
                        self.assertTrue(record.get("reason"))
                        self.assertNotIn("trusted_input", record)

    def test_trust_check_cli(self):
        for label, env in self.untrusted_envs():
            with self.subTest(context=label), mock.patch.dict(driver.os.environ, env, clear=True), \
                    mock.patch("builtins.print") as printed:
                self.assertEqual(driver.trust_check(), 2)
                self.assertIn("trust-check: exit 2", printed.call_args[0][0])
        with mock.patch.dict(driver.os.environ, self.ctx.write(), clear=True), mock.patch("builtins.print") as printed:
            self.assertEqual(driver.trust_check(), 0)
            self.assertIn("hosted: workflow_dispatch on refs/heads/main", printed.call_args[0][0])
        with mock.patch.dict(driver.os.environ, {"PATH": "/usr/bin:/bin"}, clear=True), mock.patch("builtins.print") as printed:
            self.assertEqual(driver.trust_check(), 0)
            self.assertIn("local", printed.call_args[0][0])

    def test_trusted_hosted_context_reaches_the_existing_steps(self):
        """With a trusted context the check passes and the step proceeds to its normal (here: mocked) work."""
        with mock.patch.dict(driver.os.environ, self.ctx.write(), clear=True), \
                mock.patch.object(driver.subprocess, "run",
                                  return_value=driver.subprocess.CompletedProcess([], 1, "", "mocked build failure")) as run, \
                mock.patch.object(driver.shutil, "which", return_value="/usr/bin/docker"), mock.patch("builtins.print"):
            code = driver.container_build(str(self.tmp / "out.iid"))
        self.assertTrue(run.called, "a trusted context must reach the build step")
        record = json.loads(driver.IMAGE_EVIDENCE.read_text())
        self.assertEqual(record["trusted_input"]["mode"], "hosted")
        self.assertNotEqual(code, 0)  # the mocked docker failure, not the trust check

    def test_cli_subcommand_is_registered(self):
        with mock.patch.dict(driver.os.environ, {"PATH": "/usr/bin:/bin"}, clear=True), \
                mock.patch.object(sys, "argv", ["hosted_trial.py", "trust-check"]), mock.patch("builtins.print"):
            self.assertEqual(driver.main(), 0)
        with mock.patch.dict(driver.os.environ, {"GITHUB_ACTIONS": "true"}, clear=True), \
                mock.patch.object(sys, "argv", ["hosted_trial.py", "trust-check"]), mock.patch("builtins.print"):
            self.assertEqual(driver.main(), 2)


if __name__ == "__main__":
    unittest.main()
