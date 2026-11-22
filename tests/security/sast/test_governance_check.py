"""Offline P4 tests through a fixture-backed GitHub HTTP transport."""

import base64
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from email.message import Message
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("p4_governance", ROOT / "scripts/sast/governance_check.py")
p4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p4)

OWNER = {"id": 181765037, "login": "Ibraheemolasupogit", "type": "User"}
REPO_NAME = "Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform"
REPO = f"https://api.github.com/repos/{REPO_NAME}"
TIP = "3d32d770653538a11d8981fd5d941057edcb42ca"
TREE_SHA = "a" * 40
REF = "/git/ref/heads/main"
COLLAB = "/collaborators?affiliation=all&per_page=100&page=1"
KEYS = "/keys?per_page=100&page=1"
ACTIONS = "/actions/permissions"
FORK = "/actions/permissions/fork-pr-workflows-private-repos"
TOKEN_POLICY = "/actions/permissions/workflow"
WORKFLOW_API = "/actions/workflows/c5-sast-hosted-trial.yml"
WORKFLOW = ".github/workflows/c5-sast-hosted-trial.yml"
DRIVER = "scripts/sast/hosted_trial.py"
TRUST_CONFIG = "security/sast/trusted-inputs.json"
MANIFEST = "security/sast/approved-trial-inputs.json"
TREE = f"/git/trees/{TREE_SHA}?recursive=1"
TOKEN = "offline_fixture_token"


def content_path(path):
    return f"/contents/{path}?ref={TIP}"


def file_record(path, raw):
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw, usedforsecurity=False).hexdigest()
    return {
        "path": path, "name": Path(path).name, "type": "file", "encoding": "base64",
        "content": base64.encodebytes(raw).decode("ascii"), "size": len(raw), "sha": blob,
    }


class Response(io.BytesIO):
    def __init__(self, payload, status=200, content_type="application/json", link=None):
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        super().__init__(data)
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if link is not None:
            self.headers["Link"] = link


class Fixtures:
    def __init__(self):
        self.requests = []
        self.headers = {}
        self.errors = {}
        self.overrides = {}
        entries = []
        self.routes = {
            "": {"id": 1439889276, "full_name": REPO_NAME, "owner": deepcopy(OWNER), "private": True,
                 "visibility": "private", "fork": False, "default_branch": "main", "archived": False, "disabled": False},
            REF: {"ref": "refs/heads/main", "object": {"type": "commit", "sha": TIP}},
            COLLAB: [{**OWNER, "permissions": {"admin": True}}],
            KEYS: [],
            ACTIONS: {"enabled": True, "allowed_actions": "all"},
            FORK: {"run_workflows_from_fork_pull_requests": False, "send_write_tokens_to_workflows": False,
                   "send_secrets_and_variables": False, "require_approval_for_fork_pr_workflows": False},
            TOKEN_POLICY: {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False},
            WORKFLOW_API: {"id": 987, "path": WORKFLOW, "state": "active", "url": f"{REPO}/actions/workflows/987"},
            f"/git/commits/{TIP}": {"sha": TIP, "tree": {"sha": TREE_SHA}},
            TREE: {"sha": TREE_SHA, "truncated": False, "tree": entries},
        }
        for path in (WORKFLOW, DRIVER, TRUST_CONFIG):
            record = file_record(path, (ROOT / path).read_bytes())
            self.routes[content_path(path)] = record
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": record["sha"]})

    def open(self, request, timeout):
        assert request.full_url.startswith(REPO)
        path = request.full_url.removeprefix(REPO)
        self.requests.append((path, request, timeout))
        if path in self.errors:
            raise self.errors[path]
        if path in self.overrides:
            return self.overrides[path].pop(0)
        return Response(self.routes[path], **self.headers.get(path, {}))


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixtures()
        patcher = patch.object(p4, "build_opener", return_value=self.fixture)
        self.opener = patcher.start()
        self.addCleanup(patcher.stop)
        self.client = p4.GitHubReadClient(TOKEN)

    def check(self):
        return p4.check_governance(self.client)

    def assert_rejected(self, reason):
        with self.assertRaisesRegex(p4.Rejected, reason):
            self.check()

    def mutations(self, mapping, cases, reason):
        for key, value in cases:
            with self.subTest(field=key, value=value):
                previous = mapping[key]
                mapping[key] = value
                self.assert_rejected(reason)
                mapping[key] = previous

    def test_passing_posture_uses_only_expected_gets(self):
        self.assertEqual(self.check(), {"repository_id": 1439889276, "workflow_id": 987, "main_commit": TIP})
        expected = [
            "", REF, COLLAB, KEYS, ACTIONS, FORK, TOKEN_POLICY, WORKFLOW_API, f"/git/commits/{TIP}", TREE,
            content_path(WORKFLOW), content_path(DRIVER), content_path(TRUST_CONFIG), REF,
        ]
        self.assertEqual([entry[0] for entry in self.fixture.requests], expected)
        for _, request, timeout in self.fixture.requests:
            self.assertEqual(request.get_method(), "GET")
            self.assertIsNone(request.data)
            self.assertEqual(request.get_header("Authorization"), f"Bearer {TOKEN}")
            self.assertEqual(request.get_header("X-github-api-version"), "2026-03-10")
            self.assertGreater(timeout, 0)

    def test_wrong_repository_id_name_archival_or_disabled_state(self):
        self.mutations(self.fixture.routes[""], [
            ("id", 123), ("id", "1439889276"), ("full_name", "other/repo"), ("archived", True), ("disabled", True),
        ], "repository has invalid")

    def test_wrong_owner_id_login_or_account_type(self):
        self.mutations(self.fixture.routes[""]["owner"], [
            ("id", 15), ("login", "someone-else"), ("type", "Organization"),
        ], "repository owner")

    def test_public_fork_and_contradictory_visibility_fail(self):
        self.mutations(self.fixture.routes[""], [
            ("private", False), ("private", 1), ("visibility", "public"), ("visibility", "internal"), ("fork", True),
        ], "repository has invalid")

    def test_missing_repository_fields_fail(self):
        repository = self.fixture.routes[""]
        for key in ("id", "owner", "private", "visibility", "fork", "default_branch"):
            with self.subTest(field=key):
                value = repository.pop(key)
                self.assert_rejected("repository")
                repository[key] = value

    def test_wrong_default_branch_or_malformed_git_ref_fails(self):
        self.mutations(self.fixture.routes[""], [("default_branch", "feature")], "default_branch")
        self.mutations(self.fixture.routes[REF], [("ref", "refs/tags/main"), ("object", None)], "main reference")
        self.mutations(self.fixture.routes[REF]["object"], [("type", "tag"), ("sha", "short")], "main reference")

    def test_main_drift_during_check_fails(self):
        self.fixture.overrides[REF] = [
            Response(self.fixture.routes[REF]),
            Response({"ref": "refs/heads/main", "object": {"type": "commit", "sha": "f" * 40}}),
        ]
        self.assert_rejected("main changed")

    def test_empty_extra_duplicate_or_invalid_collaborator_list_fails(self):
        owner, = self.fixture.routes[COLLAB]
        for payload in ([], [owner, owner], [owner, {"id": 2}], {}, {"message": "Not found"}):
            with self.subTest(payload=payload):
                self.fixture.routes[COLLAB] = payload
                self.assert_rejected("collaborator list")

    def test_only_collaborator_is_pinned_owner_and_admin(self):
        collaborator, = self.fixture.routes[COLLAB]
        self.mutations(collaborator, [
            ("id", 7), ("login", "someone-else"), ("type", "Bot"), ("permissions", {"admin": False}),
        ], "collaborator")

    def test_pagination_never_proves_access_list_completeness(self):
        for path in (COLLAB, KEYS):
            with self.subTest(path=path):
                self.fixture.headers[path] = {"link": '<https://example.invalid/page2>; rel="next"'}
                self.assert_rejected("pagination")
                self.assertEqual(self.fixture.requests[-1][0], path)
                self.fixture.headers.clear()

    def test_deploy_key_or_malformed_key_list_fails(self):
        for payload in ([{"id": 1, "read_only": True}], {"keys": []}, None):
            with self.subTest(payload=payload):
                self.fixture.routes[KEYS] = payload
                self.assert_rejected("deploy key inventory")

    def test_disabled_or_invalid_actions_policy_fails(self):
        self.mutations(self.fixture.routes[ACTIONS], [
            ("enabled", False), ("enabled", 1), ("allowed_actions", "unknown"),
        ], "repository Actions policy")

    def test_fork_execution_write_tokens_and_secrets_are_rejected_independently(self):
        policy = self.fixture.routes[FORK]
        for key in ("run_workflows_from_fork_pull_requests", "send_write_tokens_to_workflows", "send_secrets_and_variables"):
            self.mutations(policy, [(key, True), (key, 0), (key, "false"), (key, None)], "fork PR workflow policy")
            value = policy.pop(key)
            self.assert_rejected("fork PR workflow policy")
            policy[key] = value

    def test_fork_approval_field_is_boolean_with_fork_execution_disabled(self):
        policy = self.fixture.routes[FORK]
        key = "require_approval_for_fork_pr_workflows"
        policy[key] = True
        self.check()
        policy.pop(key)
        self.assert_rejected("Boolean approval")

    def test_default_workflow_permissions_and_pr_approval_fail_closed(self):
        permissions = self.fixture.routes[TOKEN_POLICY]
        self.mutations(permissions, [
            ("default_workflow_permissions", "write"), ("default_workflow_permissions", None),
            ("can_approve_pull_request_reviews", True), ("can_approve_pull_request_reviews", 0),
        ], "default workflow token policy")
        permissions.pop("can_approve_pull_request_reviews")
        self.assert_rejected("can_approve_pull_request_reviews")

    def test_wrong_or_inactive_workflow_registration_fails(self):
        self.mutations(self.fixture.routes[WORKFLOW_API], [
            ("path", ".github/workflows/ci.yml"), ("state", "disabled_manually"), ("id", 0), ("id", True),
            ("url", "https://example.invalid/workflows/987"),
        ], "trial workflow registration")

    def test_wrong_commit_or_truncated_git_tree_fails(self):
        self.mutations(self.fixture.routes[f"/git/commits/{TIP}"], [
            ("sha", "e" * 40), ("tree", {"sha": "short"}),
        ], "main commit")
        self.mutations(self.fixture.routes[TREE], [
            ("sha", "e" * 40), ("truncated", True), ("tree", {}),
        ], "main Git tree")

    def test_missing_duplicate_symlink_and_submodule_entries_fail(self):
        tree = self.fixture.routes[TREE]
        previous = deepcopy(tree["tree"])
        for entries in (
            previous[1:], previous + [previous[0]],
            [{**previous[0], "mode": "120000"}, *previous[1:]],
            [{**previous[0], "type": "commit", "mode": "160000"}, *previous[1:]],
        ):
            with self.subTest(entries=entries):
                tree["tree"] = entries
                self.assert_rejected("main Git tree")

    def test_changed_live_workflow_driver_and_p1_pins_fail(self):
        for entry in self.fixture.routes[TREE]["tree"]:
            path = entry["path"]
            api_path = content_path(path)
            with self.subTest(path=path):
                previous = self.fixture.routes[api_path]
                changed = file_record(path, b"unapproved bytes")
                self.fixture.routes[api_path] = changed
                entry["sha"] = changed["sha"]
                self.assert_rejected("changed on main")
                self.fixture.routes[api_path] = previous
                entry["sha"] = previous["sha"]

    def test_malformed_remote_file_or_contradictory_git_blob_fails(self):
        self.mutations(self.fixture.routes[content_path(DRIVER)], [
            ("name", "other.py"), ("path", "other.py"), ("encoding", "none"), ("content", "!"),
            ("size", True), ("sha", "b" * 40),
        ], "approved file")
        self.fixture.routes[TREE]["tree"][1]["sha"] = "b" * 40
        self.assert_rejected("differs from its main Git tree")

    def test_local_approval_drift_stops_before_network(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in (WORKFLOW, DRIVER, TRUST_CONFIG, MANIFEST):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / path).read_bytes())
            (root / DRIVER).write_bytes(b"changed local driver")
            with self.assertRaisesRegex(p4.Rejected, "differs from the P3 approval"):
                p4.check_governance(self.client, root)
            self.assertEqual(self.fixture.requests, [])

    def test_local_p1_identity_checked_even_when_digest_matches(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in (WORKFLOW, DRIVER, TRUST_CONFIG, MANIFEST):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / path).read_bytes())
            trust = json.loads((root / TRUST_CONFIG).read_bytes())
            trust["repository_owner_id"] = 1
            raw = json.dumps(trust).encode()
            (root / TRUST_CONFIG).write_bytes(raw)
            manifest = json.loads((root / MANIFEST).read_bytes())
            manifest["trusted_inputs_sha256"] = hashlib.sha256(raw).hexdigest()
            (root / MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(p4.Rejected, "local P1 trust configuration"):
                p4.check_governance(self.client, root)
            self.assertEqual(self.fixture.requests, [])

    def test_http_auth_permission_rate_service_and_redirect_errors_fail(self):
        for status in (301, 302, 401, 403, 404, 429, 500):
            with self.subTest(status=status):
                headers = Message()
                headers["Location"] = "https://example.invalid/"
                self.fixture.errors[COLLAB] = HTTPError(REPO + COLLAB, status, TOKEN, headers, io.BytesIO(b"secret body"))
                self.assert_rejected(f"HTTP {status}")
                self.assertEqual(self.fixture.requests[-1][0], COLLAB)
        redirect_handler = self.opener.call_args.args[0]
        self.assertIsNone(redirect_handler.redirect_request(None, None, 302, "", {}, "https://example.invalid/"))

    def test_non_success_incomplete_and_non_json_responses_fail(self):
        for kwargs in ({"status": 206}, {"status": 204}, {"content_type": "text/html"}):
            with self.subTest(kwargs=kwargs):
                self.fixture.headers[TOKEN_POLICY] = kwargs
                self.assert_rejected("default workflow token policy")

    def test_malformed_json_utf8_duplicate_nonfinite_and_oversized_responses_fail(self):
        for raw in (b'{', b'\xff', b'{"key":1,"key":2}', b'{"key":NaN}', b'{"key":1e999}', b' ' * (p4.MAX_RESPONSE + 1)):
            with self.subTest(length=len(raw)):
                self.fixture.routes[FORK] = raw
                self.assert_rejected("fork PR workflow policy")

    def test_timeout_and_transport_errors_fail_without_exposing_details(self):
        for failure in (TimeoutError(TOKEN), URLError(TOKEN)):
            with self.subTest(failure=type(failure).__name__):
                self.fixture.errors[KEYS] = failure
                self.assert_rejected("deploy keys could not be read from GitHub")

    def test_cli_is_explicit_and_missing_invalid_tokens_stop_before_api(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                p4.main([])
            self.assertEqual(raised.exception.code, 2)
        for token in ("", "bad\nheader"):
            with self.subTest(length=len(token)), patch.dict("os.environ", {"P4_GITHUB_TOKEN": token}, clear=True):
                with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                    self.assertEqual(p4.main(["--live"]), 1)
        self.assertEqual(self.fixture.requests, [])

    def test_cli_output_excludes_token_and_raw_responses(self):
        out, err = io.StringIO(), io.StringIO()
        self.fixture.routes[""]["private_description"] = "private fixture text"
        with patch.dict("os.environ", {"P4_GITHUB_TOKEN": TOKEN}, clear=True):
            with redirect_stderr(err), redirect_stdout(out):
                self.assertEqual(p4.main(["--live"]), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["main_commit"], TIP)
        self.assertEqual(err.getvalue(), "")
        self.assertNotIn(TOKEN, out.getvalue())
        self.assertNotIn("private fixture text", out.getvalue())


if __name__ == "__main__":
    unittest.main()
