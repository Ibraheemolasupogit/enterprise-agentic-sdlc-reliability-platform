"""Security invariants shared by local checks and mutation tests; not Azure enforcement."""

import json
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
    for command in ("npm ci --ignore-scripts", "npm run licenses", "npm run format:check", "npm run lint",
                    "npm run typecheck", "npm test", "npm run build", "npm audit --audit-level=high", "npm run test:e2e"):
        require(command in application_commands, "Missing required application check: " + command)
    require(gate.get("if") == "always()", "Required gate must inspect failed/skipped dependencies")
    require(set(gate["needs"]) == {"application", "policy", "containers", "codeql"}, "Missing gate dependency")
    require(any(s.get("run") == "python3 scripts/delivery/verify_proxy.py" for s in workflow["jobs"]["containers"]["steps"]), "Missing HTTPS proxy verification")
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
    assignments = [r for r in resources if r["type"].lower() == "microsoft.authorization/roleassignments"]
    require(len(assignments) == 1, "Unexpected bootstrap privilege grants")
    require("7f951dda-4ed3-4680-a7ca-43fe172d538d" in assignments[0]["properties"]["roleDefinitionId"], "Pull identity role escalation")
    require("Microsoft.ContainerRegistry/registries" in assignments[0]["scope"], "AcrPull not scoped to registry")
    federations = [r for r in resources if r["type"].endswith("/federatedIdentityCredentials")]
    require(len(federations) == 1, "Unexpected federation")
    trust = federations[0]["properties"]
    require(trust["issuer"] == "https://token.actions.githubusercontent.com", "Untrusted issuer")
    require(trust["audiences"] == ["api://AzureADTokenExchange"], "Wrong federation audience")
    require(trust["subject"] == "[parameters('verifiedSubject')]", "Guessed or wildcard subject")


def load_workflow():
    # BaseLoader preserves YAML's `on` key instead of treating it as YAML 1.1 true.
    return yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)


def load_templates():
    def expand(value, variables):
        if isinstance(value, str):
            match = re.fullmatch(r"\[variables\('([^']+)'\)\]", value)
            return expand(variables[match[1]], variables) if match else value
        if isinstance(value, list):
            return [expand(item, variables) for item in value]
        if isinstance(value, dict):
            return {key: expand(item, variables) for key, item in value.items()}
        return value

    templates = {}
    for p in (ROOT / "artifacts/m3/infra").glob("*.json"):
        template = json.loads(p.read_text())
        templates[p.stem] = expand(template, template.get("variables", {}))
    require(set(templates) == {"apps", "foundation", "registry-access", "federation"}, "Compile all four current templates first")
    return templates


if __name__ == "__main__":
    workflow_policy(load_workflow())
    infrastructure_policy(load_templates())
    print("PASS: workflow and compiled infrastructure security invariants")
