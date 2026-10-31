import copy
import importlib.util
import json
import os
import random
import string
import subprocess
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("policy", ROOT / "scripts/delivery/policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class DeliverySecurityTests(unittest.TestCase):
    def test_current_workflow_passes(self):
        policy.workflow_policy(policy.load_workflow())

    def test_required_gate_executes_fail_closed(self):
        script = policy.load_workflow()["jobs"]["required"]["steps"][0]["run"]
        good = {"APPLICATION": "success", "POLICY": "success", "CONTAINERS": "success",
                "CODEQL": "success", "CODEQL_ENABLED": "true", "GITHUB_EVENT_NAME": "push"}
        cases = [(good, 0)]
        for job in ("APPLICATION", "POLICY", "CONTAINERS", "CODEQL"):
            for result in ("failure", "cancelled", "skipped"):
                cases.append(({**good, job: result}, 1))
        cases.append(({**good, "CODEQL": "skipped", "GITHUB_EVENT_NAME": "pull_request"}, 0))
        cases.append(({**good, "CODEQL": "skipped", "CODEQL_ENABLED": "false"}, 0))
        for values, expected in cases:
            with self.subTest(values=values):
                result = subprocess.run(["bash", "--noprofile", "--norc", "-e", "-c", script],
                                        env={**os.environ, **values}, capture_output=True)
                self.assertEqual(result.returncode, expected)

    def test_candidate_release_role_excludes_broad_authority(self):
        role = json.loads((ROOT / "infra/release-role.example.json").read_text())
        self.assertEqual(role["DataActions"], [])
        self.assertTrue(role["Actions"])
        for action in role["Actions"]:
            self.assertTrue(action.startswith("Microsoft.App/containerApps/"))
            self.assertNotIn("*", action)
            self.assertNotIn("delete", action.lower())
            self.assertNotIn("secret", action.lower())
        self.assertNotEqual(role["AssignableScopes"], ["/"])

    def test_workflow_rejects_oidc_and_privileged_pr_mutations(self):
        for mutation in ("oidc", "trigger", "pin", "persist", "bypass", "gate", "codeql", "omit"):
            with self.subTest(mutation=mutation):
                workflow = copy.deepcopy(policy.load_workflow())
                if mutation == "oidc":
                    workflow["jobs"]["application"]["permissions"] = {"contents": "read", "id-token": "write"}
                elif mutation == "trigger":
                    workflow["on"]["pull_request_target"] = {}
                elif mutation == "pin":
                    workflow["jobs"]["application"]["steps"][0]["uses"] = "actions/checkout@main"
                elif mutation == "persist":
                    workflow["jobs"]["application"]["steps"][0]["with"]["persist-credentials"] = "true"
                elif mutation == "bypass":
                    workflow["jobs"]["policy"]["steps"][-1]["continue-on-error"] = "true"
                elif mutation == "gate":
                    workflow["jobs"]["required"]["if"] = "success()"
                elif mutation == "codeql":
                    workflow["jobs"]["codeql"]["if"] = "always()"
                else:
                    workflow["jobs"]["application"]["steps"] = [s for s in workflow["jobs"]["application"]["steps"] if s.get("run") != "npm audit --audit-level=high"]
                with self.assertRaises(ValueError):
                    policy.workflow_policy(workflow)

    def test_compiled_infrastructure_passes(self):
        policy.infrastructure_policy(policy.load_templates())

    def test_infrastructure_rejects_boundary_auth_and_trust_mutations(self):
        original = policy.load_templates()
        for mutation in ("api", "tls", "admin", "anonymous", "role", "audience", "subject", "image", "pull"):
            with self.subTest(mutation=mutation):
                templates = copy.deepcopy(original)
                resources = [r for t in templates.values() for r in t["resources"]]
                api = next(r for r in resources if r["type"] == "Microsoft.App/containerApps" and "-api'" in r["name"])
                registry = next(r for r in resources if r["type"] == "Microsoft.ContainerRegistry/registries")
                federation = next(r for r in resources if r["type"].endswith("/federatedIdentityCredentials"))
                if mutation == "api":
                    api["properties"]["configuration"]["ingress"]["external"] = True
                elif mutation == "tls":
                    api["properties"]["configuration"]["ingress"]["allowInsecure"] = True
                elif mutation == "admin":
                    registry["properties"]["adminUserEnabled"] = True
                elif mutation == "anonymous":
                    registry["properties"]["anonymousPullEnabled"] = True
                elif mutation == "role":
                    next(r for r in resources if r["type"] == "Microsoft.Authorization/roleAssignments")["properties"]["roleDefinitionId"] = "Owner"
                elif mutation == "audience":
                    federation["properties"]["audiences"] = ["untrusted"]
                elif mutation == "subject":
                    federation["properties"]["subject"] = "repo:*"
                elif mutation == "image":
                    api["properties"]["template"]["containers"][0]["image"] = "demo:latest"
                else:
                    api["properties"]["configuration"]["identitySettings"][0]["lifecycle"] = "All"
                with self.assertRaises(ValueError):
                    policy.infrastructure_policy(templates)

    def test_secret_scanner_blocks_a_generated_non_live_canary(self):
        # Construct a deterministic dummy, never a credential or cloud authentication.
        randomizer = random.Random(37)
        dummy = "ghp_" + "".join(randomizer.choices(string.ascii_letters + string.digits, k=36))
        with tempfile.TemporaryDirectory(prefix="morrow-secret-test-") as folder:
            Path(folder, "fixture.txt").write_text("github_token=" + dummy + "\n")
            result = subprocess.run(["gitleaks", "dir", "--no-banner", "--redact", "--exit-code", "1", folder],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, "Scanner failed to reject the synthetic canary")
        self.assertIn("leaks found", result.stderr)


if __name__ == "__main__":
    unittest.main()
