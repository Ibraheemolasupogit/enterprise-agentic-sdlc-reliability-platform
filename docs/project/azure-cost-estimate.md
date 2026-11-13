# M4A — Provisional Azure cost and control plan

Assessed 2026-10-31. **No spend approved; not a subscription-specific quote.**
Region candidate UK South; currency GBP, PAYG retail, taxes/discounts/credits and
free grants excluded. Subscription/offer/region/SKU eligibility remain unverified.
Basis: [primary retail meter snapshot and reproducible arithmetic](../evidence/m4a-preflight.json)
from [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices).
Missing rates are labelled **allowance**, not fabricated API results. Some queries
returned HTTP 429/no applicable rows; pricing pages did not expose numeric rates.
Requote these lines and confirm managed-resource charges before approval.

## Itemised low-duty month

Assume 730 provisioned hours (30.4167 days), two apps each active 20 hours/month,
0.25 vCPU/0.5 GiB per app, min 0/max 1 replica, 100,000 external requests,
one Basic registry within included storage, one Basic B SQL DB (5 DTU/2 GB), one
SQL private endpoint, one private DNS zone/10,000 queries and 1 GB Analytics log
ingestion. Reserve one managed public IPv4 and managed load-balancer costs for
the custom-VNet environment. Resource counts/billing need actual confirmation.

| Component | Rate / quantity assumption | GBP/month |
| --- | --- | ---: |
| ACA active CPU | 36,000 vCPU-seconds × £0.000026 | 0.94 |
| ACA active RAM | 72,000 GiB-seconds × £0.000003 | 0.22 |
| ACA requests | 0.1 million × £0.301898/million | 0.03 |
| ACR Basic | 30.4167 days × £0.125741/day; no ACR Tasks | 3.82 |
| Azure SQL Basic B | 30.4167 days × £0.151704/day; 2 GB included | 4.61 |
| SQL private endpoint | **Allowance £8/month**, endpoint meter not verified; one, 730 hours | 8.00 |
| Private DNS | First-zone rate £0.377373 + 0.01 million queries × £0.301898/million | 0.38 |
| Log Analytics | 1 GB × £2.173667/GB paid ingestion tier; do not assume shared free allowance | 2.17 |
| Managed public IPv4 | Assumed one × 730 hours × £0.003774/hour | 2.76 |
| Managed load balancer | **Allowance £15/month**, configuration/count/rate not verified | 15.00 |
| Internet/PE data processing | **Allowance £1** for small 2 GB-scale traffic; actual meters unresolved | 1.00 |
| Backup storage/overage | **Allowance £2**, Basic retention/included backup terms need confirmation | 2.00 |
| Bounded migration compute | Aggregate 1 replica-hour/month reserved, same CPU/RAM; no always-on migrator | 0.03 |
| **Model subtotal** | Round only after summing exact row values in JSON | **40.96** |
| **With 25% contingency** | Provisional planning envelope, pre-tax | **51.20** |

Of the subtotal, £26 is explicit allowance. This is an estimate with meaningful
unquoted components, not a precise expected invoice. Standard managed identity/
OIDC/app-registration features have no separate usage line assumed; premium Entra
features, GitHub licensing/runner/artifact charges and paid SAST are excluded and
require separate entitlement/cost review. No new hosted run was started in M4A.

The [Basic SQL limits](https://learn.microsoft.com/en-us/azure/azure-sql/database/resource-limits-dtu-single-databases?view=azuresql)
fit a small synthetic candidate by size, not proven performance/recovery. Serverless
is not selected as a zero-idle-cost shortcut; readiness traffic/connection pools can
prevent pause. No measured latency/SLO/RPO/RTO follows from this tier selection.

## Short exercise and stress cases

| Scenario | Exact assumptions | Subtotal / +25% contingency, pre-tax |
| --- | --- | ---: |
| 48-hour rehearsal | Each app active 6 hours, 10k requests, 0.25 GB logs, 1k DNS queries, 10-minute migrator; fixed daily/hourly items prorated; conservatively charge the whole DNS zone month; £0.25 each transfer/backup allowance | £4.02 / **£5.03** |
| Low-duty retained month | Above itemised model | £40.96 / **£51.20** |
| Both apps continuously active | Two × 730 active replica-hours; same fixed/traffic/log assumptions | £81.86 / **£102.32** |

Health, test and user activity can keep replicas active. Scale-to-zero/free grants
are not a spending guarantee. The stress case is compute sensitivity, not a load
forecast; increased traffic/logs/DB tier would add cost. Temporary rollout replicas
and retrying migrations must be included in the actual approval window.

ACA environment Private Endpoint/advanced features can add an environment fee:
the returned Environment Private Endpoint meter alone is £0.094343/hour, or
**£68.87 per 730-hour month**, before other applicable fees. The candidate uses an
internal API app, not an ACA environment Private Endpoint; do not confuse that
with the separate SQL private endpoint. Do not enable advanced/dedicated features
without repricing. [ACA billing](https://learn.microsoft.com/en-us/azure/container-apps/billing)
also documents subscription-wide free grants; this estimate deliberately does not
deduct them. [Custom-VNet guidance](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks?tabs=workload-profiles-env)
warns that managed network resources have associated charges.

ACR Premium alone would be about £38.26/month at the returned rate instead of
£3.82 Basic, before registry private endpoints/networking. NAT Gateway, Firewall,
Application Gateway/WAF, private DNS Resolver, Dedicated profiles, geo-replication,
custom domains, long-term backup retention and permanent test VMs are excluded.
If policy requires them, stop and produce a revised scope/estimate; do not hide
their costs or weaken private SQL/authentication to keep this estimate.

## Proposed approval and budget alerts

Recommend a **48-hour rehearsal first**, proposed £10 pre-tax exercise ceiling
after rates/managed-resource fees are confirmed. A retained low-duty environment
would need a separate proposed **£55/month** budget; the continuously-active case
exceeds it. Neither amount is approved. Confirm billing currency/tax and offer
before binding a financial limit; budgets are alerts, not hard caps.

Propose a subscription-scoped budget filtered to the project RG **and the actual
ACA managed-infrastructure RG**, so network charges are included. If that filter
cannot cover all associated charges, use an additional reviewed scope/alert.
Notify the owner at 50%, 80% and 100% actual and 100% forecast. Do not put private
contact details in source. No budget, action group, notification or automation is
created in M4A. Budget creation requires appropriate Cost Management permissions.

[Budget evaluation](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)
can lag usage; it cannot safely enforce a two-day ceiling by itself. Record an
absolute UTC expiry, check usage/resource inventory at least every six hours
during rehearsal, stop new changes at 80% of the approved envelope and perform
human-approved teardown at the deadline/ceiling. No automatic destructive agent
is proposed. Keep max replicas/log ingestion low, and require explicit approval
for retries, tier changes, extended duration or restored DBs.

## Teardown and residual-cost verification

Before first creation, record all owned resource IDs, tags/expiry, platform-managed
RG, role assignments, identities/federations, Entra app registrations and any
shared dependencies. Pin the source/digest/config/schema manifest and owner/actor.
The future deletion scope must be approved explicitly; M4A authorizes none.

1. Stop release/migration/probe activity. Preserve sanitized run evidence and any
   specifically approved data backup; review data loss and retention obligations.
2. Remove only the approved project apps/jobs and dependencies, then the dedicated
   project resources/RG. Never delete a shared VNet/DNS zone, unrelated RG or any
   Claims Processing resource. Let ACA remove its managed infrastructure through
   supported environment deletion; do not manually delete arbitrary managed RGs.
3. Remove dedicated federation/role bindings and outside-RG Entra app registrations
   only when ownership and absence of other users are confirmed. Clean project
   release variables/environments only with separate GitHub settings authorization.
4. Verify project and managed RG resources, public IPs/LB, registry, SQL DB/server,
   endpoints/DNS links, workspace and any orphan identities are gone as intended.
   Inventory retained/deleted DB backups, LTR/exports, soft-delete assets and locks;
   do not purge recovery artifacts without explicit approval.
5. Review Cost Analysis after its ingestion delay and again after the billing
   window; record any residual retained resources/charges. Stopping apps, deleting
   containers or a green deletion command does not prove zero future cost.

Final authorization must name the actual subscription/tenant/region, exact resource
scope, expiry, financial ceiling, operator, rollback/data handling and teardown
verification. Those fields remain unresolved until a usable existing Azure
session and owner decisions are available.

## C4 definition assumptions — 2026-11-13, no spend or quote

C4 implements local definitions only; it incurred no Azure/provider service usage
and created no resource or budget. The earlier tables/rates and arithmetic remain
the **2026-10-31 historical model**, not a current price, approved ceiling or quote.
No retail meters, subscription offer or regional SKU/quota were re-verified in C4.
[C4 evidence](../evidence/m4c-c4-infrastructure.md) and
[infrastructure contract](../../infra/README.md) record exact limits.

| Defined assumption | Cost/review consequence before a live rehearsal |
| --- | --- |
| One VNet, two subnets/two NSGs, one SQL PE and DNS zone/link; system routes/Azure DNS | Retains the model's one endpoint/zone footprint, subject to actual endpoint, data-processing and managed ACA IP/LB charges. No paid resolver, NAT, Firewall, environment PE or ACR Premium is selected |
| Public authenticated ACR Basic and outbound Internet HTTPS | A private registry/FQDN firewall is not provided. Confirm current ACR/NSG/platform/policy compatibility in C7; a requirement for ACR PE/Premium or egress appliances triggers new scope/repricing, never an automatic upgrade |
| Basic SQL, 5 DTU/2 GB, seven-day Local backups/TDE | Same compute/size candidate, with explicit local backup redundancy. Retained backups, restore overlap and overage need pricing; no geo-recovery, LTR/CMK, performance or RPO/RTO claim |
| Two 0.25-vCPU/0.5-GiB Consumption apps, min 0/max 1 | Same steady-state candidate; health activity and revision overlap can add active compute. One required frontend client CIDR limits admitted sources, not the bill |
| Manual 0.25-vCPU/0.5-GiB migrator, 600 seconds, one replica, no retry | Every separately approved migrate/seed execution consumes compute; two operations are two executions. A definition is not execution and a failed/repeated job needs fresh approval |
| One Analytics workspace/two tables, 30-day retention and 0.1-GB/day safeguard; one workspace-transform DCR | Diagnostic export defaults off. Once separately enabled, ingestion, transformation processing and retention/query pricing must be quoted for actual tables/region. No dashboards, extra collectors, Event Hub, storage archive, AMPLS or private Monitor endpoints are added |
| Five managed identities; existing admin/operations groups and separate grant manifests | No new credential or sixth SQL directory identity/Graph permission is selected. Any premium identity/governance entitlement remains outside this model and needs its own decision |

As a **historical-rate sensitivity only**, 0.1 GB/day × 730/24 days is about
3.04 GB/month. At the old £2.173667/GB meter that is about **£6.61/month ingestion**
instead of the old 1-GB assumption's £2.17, before transformation/other costs.
This is not a cap-based forecast or a refreshed whole-project estimate. A
[Log Analytics daily cap](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/daily-cap)
can overshoot and stop collection; neither it nor expiry tags/max replicas enforces
a spending ceiling. [Transformation processing](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations)
has its own billing considerations, to be requoted before export is enabled.

The old proposed £10/48-hour and £55/month envelopes remain unapproved. C7 must
reprice the exact design, including actual managed RG/network costs, backup/data
transfer, diagnostic volumes/transforms and teardown/retained assets, then obtain
an owner-approved ceiling/expiry/review/teardown scope. C4 does not begin C7 or
authorize a paid-service query, sign-in, ARM call or apply.
