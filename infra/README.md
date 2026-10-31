# Azure candidate definitions — validate only

These original Bicep files implement the planned Container Apps boundaries for
static validation, with M4B fail-closed app settings. **Deployment remains NO-GO.** They are not a complete M4
release and the M2 images must not be exposed as an authenticated durable cloud app.
See [delivery/identity/release design](../docs/delivery.md) and
[architecture](../docs/architecture.md).

| File | Boundary |
| --- | --- |
| [foundation.bicep](foundation.bicep) | Dedicated-RG candidate ACR Basic with admin/anonymous access disabled; VNet-integrated Consumption environment, pull identity and API runtime identity |
| [registry-access.bicep](registry-access.bicep) | Privileged bootstrap grants only AcrPull on this registry; separate from release |
| [apps.bicep](apps.bicep) | Two existing-environment apps with digest-only image parameters, managed pulls, TLS, internal API ingress, external frontend, separate liveness/readiness and max one replica |
| [federation.bicep](federation.bicep) | Administrator-managed exact GitHub OIDC issuer/audience/verified subject on an existing publisher or release identity; no RBAC |
| [release-role.example.json](release-role.example.json) | Unapplied candidate app-scoped updater role; placeholder scope must be replaced only after review |

All inputs naming real resources/region/owner are required. No subscription IDs,
tenant/client secrets, passwords, tokens, resource instances or deployment defaults
are embedded. Registry images use mandatory SHA-256 digest parameters; validate
the full hex format and approved registry manifest identity at release, not merely
the Bicep length constraints. No network/database/runtime deployment is authorized.

From repo root, with the pinned Bicep tool in PATH:

```sh
python3 scripts/delivery/validate_infra.py
python3 -m unittest discover -s tests/delivery -v
python3 scripts/delivery/scan_config.py
```

This runs lint/build **offline with respect to Azure**, compiled-template policy
checks and public scanner rules. It does not run `az deployment validate`, ARM
what-if, authorization, policy/quota checks or an apply. No Azure CLI/auth is
needed. Compiled output stays in ignored `artifacts/m3/infra/`.

The registry's authenticated public endpoint/Basic tier is an explicit small-demo
candidate, not a private registry claim. Private SQL requires a pre-reviewed ACA
subnet and private endpoint/DNS, not supplied here. ACR Private Link would require
a separate SKU/network/cost decision. Logs destination is deliberately `none` in
this skeleton: M6 adds purposeful telemetry; M4 must ensure adequate deployment
diagnostics without claiming M6 dashboards or SLOs. Consumption/max-one bounds
replicas, not spend; ACR/storage/network/database/log costs can continue at idle.

M4 blockers: approved region/subnet/quotas/SKUs and cost ceiling; SQL private
endpoint/DNS/public-access-disabled definitions and Entra users/migrator;
real engine/managed-identity and provider token/owner integration; actual ACA
DNS/HTTPS routing; registry
push/pull propagation, real OIDC/protected-environment/RBAC denial tests, schema
compatibility, approved deployment/rollback and teardown plan. The current local
demo Nginx uses Docker DNS/HTTP and strips Authorization. M4B's explicit HTTPS/OIDC
mode verifies CA/host/SNI and forwards bearer tokens, tested against a local TLS
fixture only. `apps.bicep` requires public origin, issuer/JWKS/audience/role/scope,
SPA settings, resolver and SQL host/database, selecting the API runtime identity's
client ID. It fixes cloud/OIDC/SQL modes and HTTPS trusted API host rather than
defaulting to anonymous SQLite. No real parameter file, SQL/network/Entra resources,
diagnostics or migrator job has been added. See [M4B evidence](../docs/evidence/m4b-local-preparation.md).

Primary schemas: [Container Apps](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2025-07-01/containerapps),
[managed environments](https://learn.microsoft.com/en-us/azure/templates/microsoft.app/2025-07-01/managedenvironments)
and [managed-identity pulls](https://learn.microsoft.com/azure/container-apps/managed-identity-image-pull).
Compile/type support does not establish regional feature availability or effective
permissions. Bootstrap/app/role/federation separation is intentional; no pipeline
identity receives authority to bootstrap or grant itself permissions.
