"""Security invariants shared by local checks and mutation tests; not Azure enforcement."""

import json
import hashlib
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def workflow_policy(workflow):
    events = workflow["on"]
    require(set(events) == {"pull_request", "push", "workflow_dispatch"}, "Unsafe trigger")
    require(workflow["permissions"] == {"contents": "read"}, "Global permission escalation")
    for name, job in workflow["jobs"].items():
        require("timeout-minutes" in job, "Unbounded job")
        require("environment" not in job, "M3 must not deploy")
        permissions = job.get("permissions", workflow["permissions"])
        expected = {"contents": "read", "security-events": "write"} if name == "codeql" else {"contents": "read"}
        require(permissions == expected, "Unexpected job permissions/OIDC")
        if name == "codeql":
            guard = job.get("if", "")
            for restriction in ("github.event_name != 'pull_request'", "github.ref == 'refs/heads/main'", "vars.CODEQL_ENABLED == 'true'"):
                require(restriction in guard, "CodeQL write scope exposed to PR/unapproved entitlement")
        for step in job.get("steps", []):
            require(step.get("continue-on-error", "false") == "false", "Security failure bypass")
            if "uses" in step:
                require(re.fullmatch(r"[\w./-]+@[a-f0-9]{40}", step["uses"]), "Unpinned action")
                if step["uses"].startswith("actions/checkout@"):
                    require(step.get("with", {}).get("persist-credentials") == "false", "Checkout credential persistence")
                require(not step["uses"].startswith(("azure/", "docker/login-action", "docker/build-push-action")), "Cloud/publish action forbidden in M3")
            run = step.get("run", "")
            require(not re.search(r"\b(?:az login|az deployment|docker push|gh auth)\b", run), "Cloud/publish command forbidden")
            require("${{ github.event." not in run, "Untrusted event interpolation into shell")
    gate = workflow["jobs"]["required"]
    application_commands = {step.get("run") for step in workflow["jobs"]["application"]["steps"]}
    browser_version = json.loads((ROOT / "apps/octocat-supply/package-lock.json").read_text())["packages"]["node_modules/@playwright/test"]["version"]
    browser_container = workflow["jobs"]["application"].get("container", {})
    require(re.fullmatch(r"mcr\.microsoft\.com/playwright:v" + re.escape(browser_version) + r"-noble@sha256:[a-f0-9]{64}", browser_container.get("image", "")), "Unpinned or mismatched Playwright CI image")
    require(browser_container.get("options") == "--user 1001", "Browser CI container privilege change")
    for command in ("npm ci --ignore-scripts", "npm run licenses", "npm run format:check", "npm run lint",
                    "npm run typecheck", "npm test", "npm run build", "npm audit --audit-level=high",
                    "npm exec -- playwright install chromium", "npm run test:e2e",
                    "npm run test:auth-capture", "npm run test:e2e:oidc", "npm run test:auth-mutations"):
        require(command in application_commands, "Missing required application check: " + command)
    steps = workflow["jobs"]["application"]["steps"]
    runs = [step.get("run") for step in steps]
    oidc = runs.index("npm run test:e2e:oidc")
    require(0 < oidc < len(runs) - 1 and runs[oidc - 1] == "npm run test:auth-capture" and runs[oidc + 1] == "npm run test:auth-capture", "OIDC capture must be checked before and after browser execution")
    for step in steps:
        if step.get("run") in ("npm run test:auth-capture", "npm run test:e2e:oidc", "npm run test:auth-mutations"):
            require("if" not in step, "OIDC validation cannot be conditionally skipped")
    require(gate.get("if") == "always()", "Required gate must inspect failed/skipped dependencies")
    require(set(gate["needs"]) == {"application", "policy", "containers", "codeql"}, "Missing gate dependency")
    require(any(s.get("run") == "python3 scripts/delivery/verify_proxy.py" for s in workflow["jobs"]["containers"]["steps"]), "Missing HTTPS proxy verification")
    for command in ("python3 scripts/delivery/validate_infra.py", "python3 -m unittest discover -s tests/delivery -v", "python3 scripts/delivery/scan_config.py"):
        matches = [s for s in workflow["jobs"]["policy"]["steps"] if s.get("run") == command]
        require(len(matches) == 1 and "if" not in matches[0], "Static infrastructure validation cannot be omitted/conditional")
    text = json.dumps(gate)
    for check in ('test \\"$APPLICATION\\" = success', 'test \\"$POLICY\\" = success', 'test \\"$CONTAINERS\\" = success'):
        require(check in text, "Required gate permits failed validation")


def infrastructure_policy(templates):
    resources = [r for template in templates.values() for r in template["resources"]]
    apps = [r for r in resources if r["type"].lower() == "microsoft.app/containerapps"]
    require(len(apps) == 2, "Expected exactly two application boundaries")
    api = next(r for r in apps if "-api'" in r["name"])
    frontend = next(r for r in apps if "-frontend'" in r["name"])
    require(api["properties"]["configuration"]["ingress"]["external"] is False, "Public API ingress")
    require(frontend["properties"]["configuration"]["ingress"]["external"] is True, "Frontend boundary changed")
    api_env = {e["name"]: e["value"] for e in api["properties"]["template"]["containers"][0].get("env", [])}
    web_env = {e["name"]: e["value"] for e in frontend["properties"]["template"]["containers"][0].get("env", [])}
    require(all(api_env.get(k) == v for k, v in {"APP_ENV": "cloud", "AUTH_MODE": "oidc", "DATABASE_BACKEND": "sql"}.items()), "Cloud identity/persistence fallback")
    require(web_env.get("PROXY_MODE") == "https" and web_env.get("AUTH_MODE") == "oidc", "Cloud proxy/auth fallback")
    require("SQL_CLIENT_ID" in api_env and "TRUSTED_API_HOST" in web_env and "DNS_RESOLVER" in web_env, "Missing explicit identity/proxy trust")
    for app in apps:
        config = app["properties"]["configuration"]
        require(config["ingress"]["allowInsecure"] is False, "Plaintext ingress")
        require(not config.get("secrets"), "Embedded registry/cloud secret")
        require(config["identitySettings"][0]["lifecycle"] == "None", "Pull identity exposed to application code")
        for registry in config["registries"]:
            require("identity" in registry and "passwordSecretRef" not in registry, "Registry password authentication")
        for container in app["properties"]["template"]["containers"]:
            require("@" in container["image"] and "Digest" in container["image"], "Mutable image reference")
            require({p["type"] for p in container["probes"]} == {"Liveness", "Readiness"}, "Missing dependency health contract")
        require(app["properties"]["template"]["scale"]["maxReplicas"] == 1, "Unreviewed capacity/cost increase")
    registry = next(r for r in resources if r["type"].lower() == "microsoft.containerregistry/registries")
    require(registry["properties"]["adminUserEnabled"] is False, "ACR admin credentials enabled")
    require(registry["properties"]["anonymousPullEnabled"] is False, "Anonymous registry pull")
    require(registry["sku"] == {"name": "Basic"} and registry["properties"]["publicNetworkAccess"] == "Enabled"
            and registry["properties"]["policies"]["azureADAuthenticationAsArmPolicy"] == {"status": "enabled"}, "Unreviewed registry network/SKU/authentication change")
    assignments = [r for r in resources if r["type"].lower() == "microsoft.authorization/roleassignments"]
    require(len(assignments) == 2, "Only separate registry pull/publisher grants are defined")
    for assignment, role_id, identity in zip(assignments,
            ("7f951dda-4ed3-4680-a7ca-43fe172d538d", "8311e382-0749-4cb8-b61a-304f252e45ec"), ("-pull", "-publisher")):
        require(role_id in assignment["properties"]["roleDefinitionId"], "Registry identity role escalation")
        require(identity in assignment["properties"]["principalId"], "Wrong registry principal")
        require("Microsoft.ContainerRegistry/registries" in assignment["scope"], "Registry grant scope escalation")
    federations = [r for r in resources if r["type"].endswith("/federatedIdentityCredentials")]
    require(len(federations) == 1, "Unexpected federation")
    trust = federations[0]["properties"]
    require(trust["issuer"] == "https://token.actions.githubusercontent.com", "Untrusted issuer")
    require(trust["audiences"] == ["api://AzureADTokenExchange"], "Wrong federation audience")
    require(trust["subject"] == "[parameters('verifiedSubject')]", "Guessed or wildcard subject")
    c4_infrastructure_policy(templates)


def c4_infrastructure_policy(templates):
    """Deliberately narrow compiled-resource contract, never an ARM evaluator."""
    def resources(template, kind):
        return [r for r in templates[template]["resources"] if r["type"].lower() == kind.lower()]

    def one(template, kind):
        items = resources(template, kind)
        require(len(items) == 1, "Missing/extra C4 resource: " + template + "/" + kind)
        return items[0]

    all_resources = [r for t in templates.values() for r in t["resources"]]
    forbidden = ("firewallrules", "virtualnetworkrules", "vaults", "natgateways", "azurefirewalls", "routetables", "deployments", "roledefinitions")
    require(not any(any(k in r["type"].lower() for k in forbidden) for r in all_resources), "Unreviewed bootstrap/network/credential resource")
    require(all(not r.get("condition") for r in all_resources if r["type"] != "Microsoft.Insights/diagnosticSettings"), "Mandatory infrastructure cannot be conditional")
    # Every declared resource type must be covered, including future additions.
    counts = {}
    for r in all_resources:
        counts[r["type"].lower()] = counts.get(r["type"].lower(), 0) + 1
    expected = {
        "Microsoft.App/containerApps": 2, "Microsoft.App/managedEnvironments": 1, "Microsoft.App/jobs": 1,
        "Microsoft.ContainerRegistry/registries": 1, "Microsoft.ManagedIdentity/userAssignedIdentities": 5,
        "Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials": 1,
        "Microsoft.Authorization/roleAssignments": 2, "Microsoft.Network/networkSecurityGroups": 2,
        "Microsoft.Network/virtualNetworks": 1, "Microsoft.Network/privateDnsZones": 1,
        "Microsoft.Network/privateDnsZones/virtualNetworkLinks": 1, "Microsoft.Network/privateEndpoints": 1,
        "Microsoft.Network/privateEndpoints/privateDnsZoneGroups": 1, "Microsoft.Sql/servers": 1,
        "Microsoft.Sql/servers/connectionPolicies": 1, "Microsoft.Sql/servers/databases": 1,
        "Microsoft.Sql/servers/databases/transparentDataEncryption": 1,
        "Microsoft.Sql/servers/databases/backupShortTermRetentionPolicies": 1,
        "Microsoft.OperationalInsights/workspaces": 2, "Microsoft.OperationalInsights/workspaces/tables": 2,
        "Microsoft.Insights/dataCollectionRules": 1, "Microsoft.Insights/diagnosticSettings": 1,
    }
    require(counts == {k.lower(): v for k, v in expected.items()}, "Missing/unreviewed compiled resource coverage")

    vnet = one("network", "Microsoft.Network/virtualNetworks")
    vp = vnet["properties"]
    require(vp["addressSpace"] == {"addressPrefixes": ["[parameters('vnetCidr')]"]}, "Unreviewed VNet range")
    require(vp["dhcpOptions"] == {"dnsServers": []} and not vp.get("virtualNetworkPeerings"), "Unreviewed DNS/peering")
    subnets = vp["subnets"]
    require([s["name"] for s in subnets] == ["aca", "private-endpoints"], "Dedicated subnet boundaries")
    for subnet, cidr, nsg in zip(subnets, ("acaSubnetCidr", "privateEndpointSubnetCidr"), ("-aca-nsg", "-endpoint-nsg")):
        p = subnet["properties"]
        require(p["addressPrefix"] == "[parameters('" + cidr + "')]", "Wrong subnet CIDR input")
        require(nsg in p["networkSecurityGroup"]["id"] and p["privateEndpointNetworkPolicies"] == "Enabled", "NSG attachment/endpoint policy bypass")
        require(not p.get("serviceEndpoints") and not p.get("routeTable") and not p.get("natGateway"), "Unreviewed service endpoint/route/NAT")
    require(subnets[0]["properties"]["delegations"] == [{"name": "aca", "properties": {"serviceName": "Microsoft.App/environments"}}]
            and subnets[1]["properties"]["delegations"] == [], "ACA/PE delegation or sharing")

    # Exact rules prevent an earlier allow-all from silently defeating a later deny.
    rules = {
        "IntraSubnetIn": (100, "Inbound", "Allow", "*", "*", "[parameters('acaSubnetCidr')]", "[parameters('acaSubnetCidr')]"),
        "LoadBalancerProbes": (110, "Inbound", "Allow", "Tcp", "30000-32767", "AzureLoadBalancer", "[parameters('acaSubnetCidr')]"),
        "DenyOtherIn": (4096, "Inbound", "Deny", "*", "*", "*", "*"),
        "IntraSubnetOut": (100, "Outbound", "Allow", "*", "*", "[parameters('acaSubnetCidr')]", "[parameters('acaSubnetCidr')]"),
        "PrivateSqlProxy": (110, "Outbound", "Allow", "Tcp", "1433", "[parameters('acaSubnetCidr')]", "[parameters('privateEndpointSubnetCidr')]"),
        "AzureDns": (120, "Outbound", "Allow", "*", "53", "[parameters('acaSubnetCidr')]", "AzurePlatformDNS"),
        "RequiredPublicHttps": (130, "Outbound", "Allow", "Tcp", "443", "[parameters('acaSubnetCidr')]", "Internet"),
        "DenyOtherOut": (4096, "Outbound", "Deny", "*", "*", "*", "*"),
    }
    endpoint_rules = {k: rules[k] for k in ("DenyOtherIn", "DenyOtherOut")}
    endpoint_rules["AcaSqlProxy"] = (100, "Inbound", "Allow", "Tcp", "1433", "[parameters('acaSubnetCidr')]", "[parameters('privateEndpointSubnetCidr')]")
    fields = ("priority", "direction", "access", "protocol", "destinationPortRange", "sourceAddressPrefix", "destinationAddressPrefix")
    for nsg, contract in zip(resources("network", "Microsoft.Network/networkSecurityGroups"), (rules, endpoint_rules)):
        actual = nsg["properties"]["securityRules"]
        require(len(actual) == len(contract) and {r["name"] for r in actual} == set(contract), "NSG rule inventory")
        for rule in actual:
            props = rule["properties"]
            require(set(props) == set(fields) | {"sourcePortRange"} and props["sourcePortRange"] == "*"
                    and tuple(props[k] for k in fields) == contract[rule["name"]], "NSG port/source/priority bypass")

    dns = one("network", "Microsoft.Network/privateDnsZones")
    link = one("network", "Microsoft.Network/privateDnsZones/virtualNetworkLinks")["properties"]
    require("privatelink" in dns["name"] and "sqlServerHostname" in dns["name"], "SQL private DNS zone")
    require(link["registrationEnabled"] is False and "-vnet" in link["virtualNetwork"]["id"], "DNS link target/auto-registration")
    env = one("foundation", "Microsoft.App/managedEnvironments")["properties"]
    require(env["vnetConfiguration"]["internal"] is False and "'aca'" in env["vnetConfiguration"]["infrastructureSubnetId"], "ACA VNet binding")
    require(env["workloadProfiles"] == [{"name": "Consumption", "workloadProfileType": "Consumption"}]
            and env["peerAuthentication"] == {"mtls": {"enabled": True}}, "Workload profile/mTLS boundary")
    require(env["appLogsConfiguration"] == {"destination": "azure-monitor"}, "Key-based/uncontrolled environment log sink")

    server = one("sql", "Microsoft.Sql/servers")["properties"]
    require(server["publicNetworkAccess"] == "Disabled" and server["minimalTlsVersion"] == "1.2"
            and server["restrictOutboundNetworkAccess"] == "Enabled", "SQL public access/TLS/outbound bypass")
    require(not any("password" in k.lower() or k == "administratorLogin" for k in server), "SQL credential provisioning")
    admin = server["administrators"]
    require(admin == {"administratorType": "ActiveDirectory", "principalType": "Group", "login": "[parameters('sqlAdminGroupName')]",
                      "sid": "[parameters('sqlAdminGroupObjectId')]", "tenantId": "[subscription().tenantId]", "azureADOnlyAuthentication": True}, "SQL Entra admin/only-auth boundary")
    require(one("sql", "Microsoft.Sql/servers/connectionPolicies")["properties"] == {"connectionType": "Proxy"}, "SQL connection policy requires revised port review")
    db = one("sql", "Microsoft.Sql/servers/databases")
    require(db["sku"] == {"name": "Basic", "tier": "Basic", "capacity": 5}, "Unreviewed SQL SKU/capacity")
    require(db["properties"] == {"createMode": "Default", "maxSizeBytes": 2147483648, "collation": "SQL_Latin1_General_CP1_CI_AS", "requestedBackupStorageRedundancy": "Local", "zoneRedundant": False, "readScale": "Disabled"}, "SQL storage/protection contract")
    require(one("sql", "Microsoft.Sql/servers/databases/transparentDataEncryption")["properties"] == {"state": "Enabled"}, "SQL encryption disabled")
    require(one("sql", "Microsoft.Sql/servers/databases/backupShortTermRetentionPolicies")["properties"] == {"retentionDays": 7}, "SQL backup retention changed")
    pe = one("sql", "Microsoft.Network/privateEndpoints")["properties"]
    require("'private-endpoints'" in pe["subnet"]["id"] and "-vnet" in pe["subnet"]["id"], "SQL PE subnet isolation")
    connections = pe["privateLinkServiceConnections"]
    require(len(connections) == 1 and connections[0]["properties"]["groupIds"] == ["sqlServer"]
            and "Microsoft.Sql/servers" in connections[0]["properties"]["privateLinkServiceId"], "SQL PE service target")
    zone = one("sql", "Microsoft.Network/privateEndpoints/privateDnsZoneGroups")["properties"]["privateDnsZoneConfigs"]
    require(len(zone) == 1 and "privatelink" in zone[0]["properties"]["privateDnsZoneId"] and "sqlServerHostname" in zone[0]["properties"]["privateDnsZoneId"], "Missing/misdirected PE DNS association")

    identities = resources("foundation", "Microsoft.ManagedIdentity/userAssignedIdentities")
    require([next(s for s in ("-pull", "-api-runtime", "-migrator", "-publisher", "-release") if s in r["name"]) for r in identities]
            == ["-pull", "-api-runtime", "-migrator", "-publisher", "-release"], "Five distinct dedicated identities")
    job = one("migrator", "Microsoft.App/jobs")
    jc = job["properties"]["configuration"]
    require(jc["triggerType"] == "Manual" and jc["replicaTimeout"] == 600 and jc["replicaRetryLimit"] == 0
            and jc["manualTriggerConfig"] == {"parallelism": 1, "replicaCompletionCount": 1}
            and not jc.get("scheduleTriggerConfig") and not jc.get("eventTriggerConfig"), "Unbounded/automatic migration execution")
    require(job["properties"]["workloadProfileName"] == "Consumption" and "-env" in job["properties"]["environmentId"], "Migrator private environment/cost")
    for item, suffixes in [(a, ("-pull", "-api-runtime") if "-api'" in a["name"] else ("-pull",)) for a in resources("apps", "Microsoft.App/containerApps")] + [(job, ("-pull", "-migrator"))]:
        require(item["identity"]["type"] == "UserAssigned" and len(item["identity"]["userAssignedIdentities"]) == len(suffixes), "Runtime identity sharing/count")
        for suffix in suffixes:
            require(sum(suffix in key for key in item["identity"]["userAssignedIdentities"]) == 1, "Runtime/migrator/publisher identity sharing")
        config = item["properties"]["configuration"]
        settings = config["identitySettings"]
        require(len(settings) == len(suffixes) and all(any(suffix in s["identity"] and s["lifecycle"] == ("None" if suffix == "-pull" else "Main") for s in settings) for suffix in suffixes), "Identity endpoint lifecycle exposure")
        require(config.get("secrets") == [], "Current contract forbids all secret slots")
        workload = item["properties"]["template"]
        require(len(workload["containers"]) == 1 and not workload.get("initContainers") and not workload.get("volumes"), "Unreviewed sidecar/init/storage")
        for container in item["properties"]["template"]["containers"]:
            require(container["resources"] == {"cpu": "[json('0.25')]", "memory": "0.5Gi"}, "Unreviewed compute capacity")
            require("@" in container["image"] and "Digest" in container["image"], "Mutable migrator/app image")
            image_name, digest_name = ("morrow-frontend", "frontendDigest") if "-frontend'" in item["name"] else ("morrow-api", "apiDigest")
            expected_image = "[format('{0}/" + image_name + "@{1}', reference(resourceId('Microsoft.ContainerRegistry/registries', parameters('registryName')), '2025-04-01').loginServer, parameters('" + digest_name + "'))]"
            require(container["image"] == expected_image, "Foreign registry/image target")
            require(item["type"] == "Microsoft.App/jobs" or not container.get("command") and not container.get("args"), "Unreviewed application startup override")
            for entry in container.get("env", []):
                require(set(entry) == {"name", "value"} and not any(s in entry["name"] for s in ("PASSWORD", "SECRET", "TOKEN", "CONNECTION_STRING")), "Inline credential or unreviewed secret reference")
            ev = {e["name"]: e["value"] for e in container.get("env", [])}
            if "SQL_SERVER" in ev:
                require("sqlServerName" in ev["SQL_SERVER"] and "sqlServerHostname" in ev["SQL_SERVER"], "Normal TLS-verified SQL FQDN required")
                require("-api-runtime" in ev["SQL_CLIENT_ID"], "Wrong SQL runtime identity")
    container = job["properties"]["template"]["containers"][0]
    require(container["command"] == ["node"] and container["args"] == ["api/dist/sql-cli.js", "[parameters('migrationOperation')]", "--confirm-sql-change"], "Unreviewed migrator command")
    require("-migrator" in next(e["value"] for e in container["env"] if e["name"] == "SQL_MIGRATOR_CLIENT_ID"), "SQL DDL identity sharing")
    for app in resources("apps", "Microsoft.App/containerApps"):
        t = app["properties"]["template"]
        ingress = app["properties"]["configuration"]["ingress"]
        if "-frontend'" in app["name"]:
            require(ingress["ipSecurityRestrictions"] == [{"name": "approved-client", "action": "Allow", "ipAddressRange": "[parameters('frontendClientCidr')]"}], "Frontend client ingress scope")
        require(t["scale"] == {"minReplicas": 0, "maxReplicas": 1}, "Replica floor/ceiling cost")
        require(all(k in t["revisionSuffix"] for k in ("releaseSha", "configSha256", "schemaVersion")), "Release/config/schema correlation missing")
        probes = {p["type"]: p for p in t["containers"][0]["probes"]}
        require(probes["Readiness"]["httpGet"]["path"] == "/health/ready" and probes["Liveness"]["httpGet"]["path"] == "/health/live", "Static-only readiness or recursive liveness")
        port, timeout = (8080, 3) if "-frontend'" in app["name"] else (3000, 2)
        require(probes == {"Liveness": {"type": "Liveness", "httpGet": {"path": "/health/live", "port": port}, "initialDelaySeconds": 5, "periodSeconds": 10},
                           "Readiness": {"type": "Readiness", "httpGet": {"path": "/health/ready", "port": port}, "periodSeconds": 5, "timeoutSeconds": timeout}}, "Probe deadline/port contract")

    for template in ("foundation", "diagnostics"):
        w = one(template, "Microsoft.OperationalInsights/workspaces")["properties"]
        require(w["sku"] == {"name": "PerGB2018"} and w["retentionInDays"] == 30
                and w["workspaceCapping"] == {"dailyQuotaGb": "[json('0.1')]"}, "Log retention/ingestion bound")
        require(w["features"] == {"disableLocalAuth": True, "enableLogAccessUsingOnlyResourcePermissions": False}, "Workspace shared keys/resource-only query access")
        require(w["publicNetworkAccessForIngestion"] == w["publicNetworkAccessForQuery"] == "Enabled", "Workspace network model changed; reprice/review required")
    tables = resources("foundation", "Microsoft.OperationalInsights/workspaces/tables")
    require({t["properties"]["schema"]["name"] for t in tables} == {"ContainerAppConsoleLogs", "ContainerAppSystemLogs"}
            and all(t["properties"]["plan"] == "Analytics" and t["properties"]["retentionInDays"] == t["properties"]["totalRetentionInDays"] == 30 for t in tables), "Table coverage/retention")
    dcr = one("diagnostics", "Microsoft.Insights/dataCollectionRules")
    require(dcr["kind"] == "WorkspaceTransforms", "No ingestion-time redaction")
    require(dcr["properties"]["destinations"] == {"logAnalytics": [{"name": "safeLogs", "workspaceResourceId": "[resourceId('Microsoft.OperationalInsights/workspaces', format('{0}-logs', parameters('prefix')))]"}]}, "Foreign/missing diagnostic destination")
    require(one("diagnostics", "Microsoft.OperationalInsights/workspaces")["properties"]["defaultDataCollectionRuleResourceId"] == "[resourceId('Microsoft.Insights/dataCollectionRules', format('{0}-redaction', parameters('prefix')))]", "Workspace DCR link")
    flows = dcr["properties"]["dataFlows"]
    require(len(flows) == 2, "Missing/extra log transform")
    for flow, table, filename in zip(flows, ("ContainerAppConsoleLogs", "ContainerAppSystemLogs"), ("diagnostics-console.kql", "diagnostics-system.kql")):
        require(flow["streams"] == ["Microsoft-Table-" + table] and flow["destinations"] == ["safeLogs"], "Unredacted log stream/destination")
        # Bicep trim(loadTextContent(...)) compiles as an ARM trim expression.
        formula = 'Log = case(Log contains "ENOTFOUND", "DNS", Log contains "certificate", "TLS", Log contains "DATABASE_UNAVAILABLE", "SQL", Log contains "schema", "SCHEMA", "REDACTED")'
        expected_query = 'source | project TimeGenerated, ContainerAppName, RevisionName' + (', ContainerImage' if table == "ContainerAppConsoleLogs" else '') + ', ' + formula + ', _ResourceId'
        compiled_query = flow["transformKql"]
        if compiled_query.startswith("[trim('") and compiled_query.endswith("')]"):
            compiled_query = compiled_query[7:-3].replace("''", "'").strip()
        require(compiled_query == expected_query and "Log = case(" in compiled_query and "REDACTED" in compiled_query, "Diagnostic payload pass-through")
    export = one("diagnostics", "Microsoft.Insights/diagnosticSettings")
    require(export["condition"] == "[parameters('diagnosticExportEnabled')]" and templates["diagnostics"]["parameters"]["diagnosticExportEnabled"]["defaultValue"] is False, "Premature diagnostic collection")
    require(export["properties"]["logAnalyticsDestinationType"] == "Dedicated" and export["properties"]["logs"] == [{"category": "ContainerAppConsoleLogs", "enabled": True}, {"category": "ContainerAppSystemLogs", "enabled": True}]
            and export["properties"]["metrics"] == [] and not any(k in export["properties"] for k in ("storageAccountId", "eventHubAuthorizationRuleId", "marketplacePartnerId")), "Unreviewed HTTP/query/audit log export")
    for template in templates.values():
        for name, p in template.get("parameters", {}).items():
            require("defaultValue" not in p or (name == "diagnosticExportEnabled" and p["defaultValue"] is False), "Unapproved real deployment default")
    require(templates["apps"]["parameters"]["schemaVersion"]["allowedValues"] == [1], "Unreviewed schema correlation version")


def identity_and_secret_contract_policy(identity=None, secret=None, release=None):
    identity = identity if identity is not None else json.loads((ROOT / "infra/identity-contract.json").read_text())
    secret = secret if secret is not None else json.loads((ROOT / "infra/secret-reference-contract.json").read_text())
    release = release if release is not None else json.loads((ROOT / "infra/release-role.example.json").read_text())
    require(identity["dedicatedManagedIdentities"] == ["pull", "api-runtime", "migrator", "publisher", "release"], "Identity ceiling/isolation")
    expected = [("pull", "registry"), ("publisher", "registry"), ("release", "each-api-and-frontend-app"), ("release", "environment"),
                ("release", "each-pull-and-api-runtime-identity"), ("approved-operations-group", "each-api-and-frontend-app"), ("approved-operations-group", "workspace")]
    require([(g["principal"], g["scope"]) for g in identity["grants"]] == expected, "Grant manifest scope/identity escalation")
    allowed_actions = [None, None, None,
        ["Microsoft.App/managedEnvironments/read", "Microsoft.App/managedEnvironments/join/action"],
        ["Microsoft.ManagedIdentity/userAssignedIdentities/read", "Microsoft.ManagedIdentity/userAssignedIdentities/assign/action"],
        ["Microsoft.App/containerApps/read", "Microsoft.App/containerApps/revisions/read"],
        ["Microsoft.OperationalInsights/workspaces/read", "Microsoft.OperationalInsights/workspaces/query/ContainerAppConsoleLogs/read", "Microsoft.OperationalInsights/workspaces/query/ContainerAppSystemLogs/read"]]
    for grant, actions in zip(identity["grants"], allowed_actions):
        require(grant.get("actions") == actions, "Unexpected deployment/operations action")
    require([g.get("role") for g in identity["grants"][:3]] == ["AcrPull", "AcrPush", "release-role.example.json"], "Grant role escalation")
    sql = identity["sqlContainedUsers"]
    require(sql["api-runtime"] == {"SELECT": ["dbo.products", "dbo.schema_migrations", "dbo.carts", "dbo.cart_items"], "INSERT": ["dbo.carts", "dbo.cart_items"], "UPDATE": ["dbo.carts", "dbo.cart_items"], "DELETE": ["dbo.carts", "dbo.cart_items"], "DDL": False, "db_owner": False}, "Runtime SQL DDL/data overreach")
    require(sql["migrator"]["runtimeAttachment"] is False and sql["migrator"]["db_owner"] is False, "Migrator ownership/sharing")
    require(sql["migrator"]["databasePermissions"] == ["CONNECT", "CREATE TABLE"]
            and sql["migrator"]["schemaPermissions"] == {"dbo": ["ALTER", "REFERENCES"]}
            and sql["migrator"]["initialCreationOnlySchemaPermissions"] == {"dbo": ["SELECT", "INSERT"]}
            and sql["migrator"]["replaceInitialSchemaDataGrantsWithObjectGrants"] is True
            and sql["migrator"]["objectPermissions"] == {"dbo.schema_migrations": ["SELECT", "INSERT"], "dbo.products": ["SELECT", "INSERT"]}, "Migrator permission escalation")
    require(secret["secrets"] == secret["environmentSecretRefs"] == [], "Unexpected secret contract slots")
    require(secret["futureReferenceContract"]["secretShape"] == ["name", "keyVaultUrl", "identity"]
            and secret["futureReferenceContract"]["environmentShape"] == ["name", "secretRef"], "Inline credential/fallback contract")
    expected_release = ["Microsoft.App/containerApps/" + a for a in ("read", "write", "revisions/read", "revisions/activate/action", "revisions/deactivate/action", "revisions/restart/action")]
    require(release["Actions"] == expected_release and release["DataActions"] == release["NotActions"] == release["NotDataActions"] == [], "Release action escalation")
    require(release["AssignableScopes"] == ["/subscriptions/REPLACE_SUBSCRIPTION/resourceGroups/REPLACE_DEDICATED_RG"], "Unreviewed release scope")


def load_workflow():
    # BaseLoader preserves YAML's `on` key instead of treating it as YAML 1.1 true.
    return yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)


def load_templates(folder=None):
    def expand(value, variables):
        if isinstance(value, str):
            trim_variable = re.fullmatch(r"\[trim\(variables\('([^']+)'\)\)\]", value)
            if trim_variable:
                literal = variables[trim_variable[1]]
                require(isinstance(literal, str) and not literal.startswith("["), "Only literal KQL trim is evaluated locally")
                return literal.strip()
            match = re.fullmatch(r"\[variables\('([^']+)'\)\]", value)
            return expand(variables[match[1]], variables) if match else value
        if isinstance(value, list):
            return [expand(item, variables) for item in value]
        if isinstance(value, dict):
            return {key: expand(item, variables) for key, item in value.items()}
        return value

    templates = {}
    folder = folder or ROOT / "artifacts/m3/infra"
    for p in folder.glob("*.json"):
        template = json.loads(p.read_text())
        templates[p.stem] = expand(template, template.get("variables", {}))
    expected = {"apps", "foundation", "registry-access", "federation", "network", "sql", "migrator", "diagnostics"}
    require(set(templates) == expected == {p.stem for p in (ROOT / "infra").glob("*.bicep")}, "Compile every current template; no missing/stale/unknown template")
    bindings = json.loads((folder.parent / "infra-bindings.json").read_text())
    required_paths = {str(p.relative_to(ROOT)) for p in (ROOT / "infra").glob("*.bicep")} | {"infra/diagnostics-console.kql", "infra/diagnostics-system.kql", "infra/bicepconfig.json"}
    required_paths |= {"artifacts/m3/infra/" + p + ".json" for p in expected}
    require({b["path"] for b in bindings} == required_paths, "Incomplete compiled input/output binding inventory")
    for b in bindings:
        path = folder / Path(b["path"]).name if b["path"].startswith("artifacts/m3/infra/") else ROOT / b["path"]
        require(hashlib.sha256(path.read_bytes()).hexdigest() == b["sha256"], "Stale compiled input/output; rerun offline compilation")
    return templates


if __name__ == "__main__":
    workflow_policy(load_workflow())
    infrastructure_policy(load_templates())
    identity_and_secret_contract_policy()
    print("PASS: workflow and compiled infrastructure security invariants")
