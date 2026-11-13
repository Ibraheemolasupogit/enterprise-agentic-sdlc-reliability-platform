"""C4 static adversarial controls; no Azure/Kusto/DNS/SQL integration is executed."""

import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/delivery" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


policy = module("policy_c4", "policy.py")
parameters = module("parameters_c4", "validate_parameters.py")
diagnostics = module("diagnostics_c4", "diagnostics.py")


def resource(templates, template, kind, index=0):
    return [r for r in templates[template]["resources"] if r["type"] == kind][index]


def fixture():
    # Synthetic metadata only. No identity is created, registered or authenticated.
    return {
        "location": "uksouth", "prefix": "c4fixture", "registryName": "c4fixtureregistry", "ownerTag": "synthetic-owner",
        "expiresAt": "2026-11-14T00:00:00Z", "vnetCidr": "10.42.0.0/24", "acaSubnetCidr": "10.42.0.0/27",
        "privateEndpointSubnetCidr": "10.42.0.32/28", "reservedNetworks": ["10.43.0.0/24"], "reservedNetworksReviewed": True,
        "sqlServerName": "c4-fixture-sql", "sqlDatabase": "synthetic", "sqlAdminGroupObjectId": "11111111-1111-4111-8111-111111111111",
        "sqlAdminGroupName": "synthetic-admin-group", "releaseSha": "a" * 40, "configSha256": "b" * 64, "schemaVersion": 1,
        "apiDigest": "sha256:" + "c" * 64, "frontendDigest": "sha256:" + "d" * 64,
        "publicOrigin": "https://shop.example.test", "frontendClientCidr": "203.0.113.10/32", "oidcIssuer": "https://issuer.example.test/tenant/v2.0",
        "oidcJwksUri": "https://issuer.example.test/tenant/keys", "oidcAudience": "api://synthetic-api",
        "oidcRequiredRole": "CartUser", "oidcRequiredScope": "cart", "oidcSpaClientId": "synthetic-public-client",
        "oidcSpaScopes": "openid cart", "oidcConnectOrigin": "https://issuer.example.test", "dnsResolver": "168.63.129.16",
        "identityName": "c4fixture-release", "verifiedSubject": "repo:synthetic-owner/synthetic-repo:environment:reviewed",
        "credentialName": "synthetic-binding", "migrationOperation": "migrate",
    }


class C4InfrastructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.templates = policy.load_templates()

    def test_c4_all_eight_compiled_contracts_and_manifests_pass(self):
        self.assertEqual(set(self.templates), {"apps", "foundation", "registry-access", "federation", "network", "sql", "migrator", "diagnostics"})
        policy.infrastructure_policy(self.templates)
        policy.identity_and_secret_contract_policy()

    def test_c4_compiled_network_sql_and_diagnostics_mutations_are_rejected(self):
        # Each mutation must fail its intended invariant, not setup/compilation.
        cases = [
            ("network", "Microsoft.Network/virtualNetworks", ["properties", "subnets", 0, "properties", "delegations"], [], "delegation"),
            ("network", "Microsoft.Network/virtualNetworks", ["properties", "subnets", 1, "properties", "addressPrefix"], "[parameters('acaSubnetCidr')]", "CIDR"),
            ("network", "Microsoft.Network/virtualNetworks", ["properties", "subnets", 1, "properties", "privateEndpointNetworkPolicies"], "Disabled", "NSG"),
            ("network", "Microsoft.Network/virtualNetworks", ["properties", "subnets", 0, "properties", "networkSecurityGroup", "id"], "foreign", "NSG"),
            ("network", "Microsoft.Network/virtualNetworks", ["properties", "dhcpOptions", "dnsServers"], ["8.8.8.8"], "DNS"),
            ("network", "Microsoft.Network/networkSecurityGroups", ["properties", "securityRules", 4, "properties", "destinationPortRange"], "*", "NSG port"),
            ("network", "Microsoft.Network/networkSecurityGroups", ["properties", "securityRules", 7, "properties", "access"], "Allow", "NSG port"),
            ("network", "Microsoft.Network/privateDnsZones/virtualNetworkLinks", ["properties", "registrationEnabled"], True, "DNS link"),
            ("network", "Microsoft.Network/privateDnsZones/virtualNetworkLinks", ["properties", "virtualNetwork", "id"], "foreign", "DNS link"),
            ("sql", "Microsoft.Sql/servers", ["properties", "publicNetworkAccess"], "Enabled", "SQL public"),
            ("sql", "Microsoft.Sql/servers", ["properties", "minimalTlsVersion"], "1.0", "SQL public"),
            ("sql", "Microsoft.Sql/servers", ["properties", "administrators", "azureADOnlyAuthentication"], False, "SQL Entra"),
            ("sql", "Microsoft.Sql/servers", ["properties", "administrators", "principalType"], "Application", "SQL Entra"),
            ("sql", "Microsoft.Sql/servers/connectionPolicies", ["properties", "connectionType"], "Redirect", "connection policy"),
            ("sql", "Microsoft.Sql/servers/databases", ["properties", "maxSizeBytes"], 10737418240, "SQL storage"),
            ("sql", "Microsoft.Sql/servers/databases", ["sku", "tier"], "Premium", "SQL SKU"),
            ("sql", "Microsoft.Sql/servers/databases/transparentDataEncryption", ["properties", "state"], "Disabled", "encryption"),
            ("sql", "Microsoft.Sql/servers/databases/backupShortTermRetentionPolicies", ["properties", "retentionDays"], 1, "retention"),
            ("sql", "Microsoft.Network/privateEndpoints", ["properties", "subnet", "id"], "aca", "PE subnet"),
            ("sql", "Microsoft.Network/privateEndpoints", ["properties", "privateLinkServiceConnections", 0, "properties", "groupIds"], ["vault"], "PE service"),
            ("sql", "Microsoft.Network/privateEndpoints/privateDnsZoneGroups", ["properties", "privateDnsZoneConfigs"], [], "PE DNS"),
            ("foundation", "Microsoft.App/managedEnvironments", ["properties", "appLogsConfiguration", "destination"], "log-analytics", "log sink"),
            ("foundation", "Microsoft.App/managedEnvironments", ["properties", "peerAuthentication", "mtls", "enabled"], False, "mTLS"),
            ("foundation", "Microsoft.OperationalInsights/workspaces", ["properties", "features", "disableLocalAuth"], False, "shared keys"),
            ("diagnostics", "Microsoft.OperationalInsights/workspaces", ["properties", "retentionInDays"], 365, "retention"),
            ("diagnostics", "Microsoft.OperationalInsights/workspaces", ["properties", "workspaceCapping", "dailyQuotaGb"], -1, "ingestion"),
            ("diagnostics", "Microsoft.OperationalInsights/workspaces", ["properties", "defaultDataCollectionRuleResourceId"], "foreign", "DCR link"),
            ("diagnostics", "Microsoft.Insights/dataCollectionRules", ["properties", "dataFlows", 0, "transformKql"], "source", "payload"),
            ("diagnostics", "Microsoft.Insights/dataCollectionRules", ["properties", "destinations", "logAnalytics", 0, "workspaceResourceId"], "foreign", "destination"),
            ("diagnostics", "Microsoft.Insights/diagnosticSettings", ["condition"], True, "Premature"),
            ("diagnostics", "Microsoft.Insights/diagnosticSettings", ["properties", "logs", 0, "category"], "allLogs", "HTTP/query"),
        ]
        for template, kind, path, value, message in cases:
            with self.subTest(template=template, resource=kind, field=path):
                changed = copy.deepcopy(self.templates)
                parent = resource(changed, template, kind)
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                with self.assertRaisesRegex(ValueError, message):
                    policy.infrastructure_policy(changed)

    def test_c4_migration_identity_capacity_and_readiness_mutations_are_rejected(self):
        for mutation in ("retry", "parallel", "schedule", "timeout", "identity-sharing", "pull-token", "ddl-client", "password", "secret-ref", "image", "foreign-image", "sidecar", "startup", "compute", "readiness", "probe-timeout", "replicas", "frontend-ingress", "correlation", "sql-ip", "export-default"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.templates)
                job = resource(changed, "migrator", "Microsoft.App/jobs")
                config = job["properties"]["configuration"]
                container = job["properties"]["template"]["containers"][0]
                api = resource(changed, "apps", "Microsoft.App/containerApps")
                if mutation in ("retry", "parallel", "schedule", "timeout"):
                    if mutation == "retry": config["replicaRetryLimit"] = 1
                    elif mutation == "parallel": config["manualTriggerConfig"]["parallelism"] = 2
                    elif mutation == "timeout": config["replicaTimeout"] = 601
                    else: config["triggerType"] = "Schedule"
                elif mutation == "identity-sharing":
                    api["identity"] = copy.deepcopy(job["identity"])
                elif mutation == "pull-token": config["identitySettings"][0]["lifecycle"] = "All"
                elif mutation == "ddl-client":
                    next(e for e in container["env"] if e["name"] == "SQL_MIGRATOR_CLIENT_ID")["value"] = "runtime"
                elif mutation == "password": container["env"].append({"name": "SQL_PASSWORD", "value": "non-live-canary"})
                elif mutation == "secret-ref": config["secrets"] = [{"name": "unexpected", "value": "non-live-canary"}]
                elif mutation == "image": container["image"] = "demo:latest"
                elif mutation == "foreign-image": container["image"] = container["image"].replace("morrow-api", "foreign-api")
                elif mutation == "sidecar": api["properties"]["template"]["initContainers"] = [{"name": "unsafe"}]
                elif mutation == "startup": api["properties"]["template"]["containers"][0]["command"] = ["sh"]
                elif mutation == "compute": container["resources"]["memory"] = "4Gi"
                elif mutation == "readiness": api["properties"]["template"]["containers"][0]["probes"][1]["httpGet"]["path"] = "/"
                elif mutation == "probe-timeout": api["properties"]["template"]["containers"][0]["probes"][1]["timeoutSeconds"] = 999
                elif mutation == "replicas": api["properties"]["template"]["scale"]["minReplicas"] = 1
                elif mutation == "correlation": api["properties"]["template"]["revisionSuffix"] = "fixed"
                elif mutation == "frontend-ingress": resource(changed, "apps", "Microsoft.App/containerApps", 1)["properties"]["configuration"]["ingress"]["ipSecurityRestrictions"] = []
                elif mutation == "sql-ip": next(e for e in container["env"] if e["name"] == "SQL_SERVER")["value"] = "10.42.0.35"
                else: changed["diagnostics"]["parameters"]["diagnosticExportEnabled"]["defaultValue"] = True
                with self.assertRaises(ValueError): policy.infrastructure_policy(changed)

    def test_c4_additional_or_missing_resource_is_never_silently_uncovered(self):
        for kind in ("Microsoft.Sql/servers/firewallRules", "Microsoft.Network/natGateways", "Microsoft.Unknown/uncovered"):
            changed = copy.deepcopy(self.templates)
            changed["sql"]["resources"].append({"type": kind, "name": "unsafe"})
            with self.subTest(kind=kind), self.assertRaises(ValueError): policy.infrastructure_policy(changed)
        changed = copy.deepcopy(self.templates)
        changed["network"]["resources"] = [r for r in changed["network"]["resources"] if not r["type"].endswith("virtualNetworkLinks")]
        with self.assertRaisesRegex(ValueError, "coverage"): policy.infrastructure_policy(changed)

    def test_c4_missing_stale_and_extra_compiled_files_fail_closed(self):
        for mutation in ("missing", "stale", "extra", "binding"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix="morrow-c4-static-") as folder:
                folder = Path(folder)
                shutil.copytree(ROOT / "artifacts/m3/infra", folder / "infra")
                shutil.copy2(ROOT / "artifacts/m3/infra-bindings.json", folder / "infra-bindings.json")
                if mutation == "missing": (folder / "infra/sql.json").unlink()
                elif mutation == "stale": (folder / "infra/sql.json").write_text(json.dumps(self.templates["sql"]))
                elif mutation == "extra": (folder / "infra/extra.json").write_text('{}')
                else: (folder / "infra-bindings.json").write_text('[]')
                with self.assertRaises(ValueError): policy.load_templates(folder / "infra")

    def test_c4_identity_grant_and_secret_manifests_reject_escalation(self):
        original = json.loads((ROOT / "infra/identity-contract.json").read_text())
        for mutation in ("sixth", "runtime-ddl", "runtime-owner", "migrator-shared", "migrator-permissions", "permanent-bootstrap-data", "operations-write", "release-scope", "grant-role"):
            identity = copy.deepcopy(original)
            if mutation == "sixth": identity["dedicatedManagedIdentities"].append("sql-directory")
            elif mutation == "runtime-ddl": identity["sqlContainedUsers"]["api-runtime"]["DDL"] = True
            elif mutation == "runtime-owner": identity["sqlContainedUsers"]["api-runtime"]["db_owner"] = True
            elif mutation == "migrator-shared": identity["sqlContainedUsers"]["migrator"]["runtimeAttachment"] = True
            elif mutation == "migrator-permissions": identity["sqlContainedUsers"]["migrator"]["databasePermissions"].append("CONTROL")
            elif mutation == "permanent-bootstrap-data": identity["sqlContainedUsers"]["migrator"]["replaceInitialSchemaDataGrantsWithObjectGrants"] = False
            elif mutation == "operations-write": identity["grants"][-1]["actions"].append("*/write")
            elif mutation == "release-scope": identity["grants"][2]["scope"] = "subscription"
            else: identity["grants"][0]["role"] = "Owner"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): policy.identity_and_secret_contract_policy(identity=identity)
        secret = json.loads((ROOT / "infra/secret-reference-contract.json").read_text())
        secret["secrets"].append({"name": "password", "value": "non-live-canary"})
        with self.assertRaises(ValueError): policy.identity_and_secret_contract_policy(secret=secret)

    def test_c4_parameter_topology_trust_hashes_and_expiry_fail_closed(self):
        now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        self.assertFalse(parameters.validate(fixture(), self.templates, now)["diagnosticExportEnabled"])
        cases = [("acaSubnetCidr", "10.42.0.0/28"), ("acaSubnetCidr", "10.43.0.0/27"),
                 ("privateEndpointSubnetCidr", "10.42.0.0/28"), ("vnetCidr", "8.8.0.0/16"),
                 ("vnetCidr", "172.30.0.0/16"), ("acaSubnetCidr", "10.42.0.1/27"), ("acaSubnetCidr", "::/27"),
                 ("reservedNetworks", ["10.42.0.0/16"]), ("reservedNetworksReviewed", False), ("apiDigest", "sha256:" + "g" * 64),
                 ("frontendDigest", "demo:latest"), ("releaseSha", "0" * 40), ("configSha256", "bad"), ("schemaVersion", 0), ("schemaVersion", 2),
                 ("publicOrigin", "http://shop.example.test"), ("publicOrigin", "https://shop.example.test/path"),
                 ("frontendClientCidr", "0.0.0.0/0"), ("frontendClientCidr", "10.42.0.0/24"),
                 ("oidcIssuer", "https://issuer.example.test/common/v2.0"), ("oidcIssuer", "https://user:password@issuer.example.test"),
                 ("oidcJwksUri", "https://foreign.example.test/keys"), ("oidcSpaScopes", "openid offline_access cart"),
                 ("oidcConnectOrigin", "https://issuer.example.test;unsafe"), ("dnsResolver", "127.0.0.11"),
                 ("sqlAdminGroupObjectId", "00000000-0000-0000-0000-000000000000"), ("sqlDatabase", "name;unsafe"),
                 ("expiresAt", "2026-11-12T00:00:00Z"), ("expiresAt", "2026-11-16T00:00:00Z"),
                 ("diagnosticExportEnabled", True), ("identityName", "c4fixture-api-runtime"), ("verifiedSubject", "repo:*"),
                 ("migrationOperation", "reset"), ("SQL_PASSWORD", "non-live-canary")]
        for name, value in cases:
            with self.subTest(field=name):
                values = fixture(); values[name] = value
                with self.assertRaises(ValueError) as error: parameters.validate(values, self.templates, now)
                self.assertNotIn("non-live-canary", str(error.exception))
        missing = fixture(); missing.pop("vnetCidr")
        with self.assertRaises(ValueError): parameters.validate(missing, self.templates, now)

    def test_c4_redaction_reference_model_binds_kql_and_discards_payload_canaries(self):
        # A Python reference model is intentionally NOT reported as executing KQL.
        for filename in ("diagnostics-console.kql", "diagnostics-system.kql"):
            query = (ROOT / "infra" / filename).read_text().strip()
            for fault, expected in (("ENOTFOUND", "DNS"), ("certificate failed", "TLS"), ("DATABASE_UNAVAILABLE", "SQL"), ("schema mismatch", "SCHEMA"), ("unknown", "REDACTED")):
                row = {"TimeGenerated": "2026-11-13T00:00:00Z", "ContainerAppName": "c4fixture-api", "RevisionName": "reviewed-revision", "ContainerImage": "registry/reviewed@sha256:digest", "_ResourceId": "reviewed-resource"}
                canaries = ["nonlive-token-canary", "nonlive-credential-canary", "nonlive-subject-canary", "nonlive-body-canary"]
                row.update(Log=fault + " " + " ".join(canaries), Authorization=canaries[0], ConnectionString=canaries[1], owner=canaries[2], body=canaries[3])
                result = diagnostics.project_candidate(query, row)
                self.assertEqual(result["Log"], expected)
                self.assertFalse(any(c in json.dumps(result) for c in canaries))
            with self.assertRaises(ValueError): diagnostics.project_candidate(query.replace("Log = case(", "RawLog = case("), row)

    def test_c4_static_ci_checks_cannot_be_skipped(self):
        for command in ("python3 scripts/delivery/validate_infra.py", "python3 -m unittest discover -s tests/delivery -v", "python3 scripts/delivery/scan_config.py"):
            for mutation in ("omit", "conditional"):
                workflow = copy.deepcopy(policy.load_workflow())
                steps = workflow["jobs"]["policy"]["steps"]
                step = next(s for s in steps if s.get("run") == command)
                if mutation == "omit": steps.remove(step)
                else: step["if"] = "false"
                with self.subTest(command=command, mutation=mutation), self.assertRaises(ValueError): policy.workflow_policy(workflow)
