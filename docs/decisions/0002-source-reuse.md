# ADR 0002 — Source reuse and original-code licensing

Date: 2026-10-30. Status: **direct upstream application reuse not cleared;
independent implementation and MIT selected by the owner for M2**.
Supersedes the conditional S01 adoption recommendation from M1. The later M2
implementation request explicitly authorizes independent functionality and MIT;
this does not authorize reuse of upstream application material. Owner: repository owner.
Requirements: R02, R14–R17, R21. Primary evidence and limitations:
[current source assessment](../source-assessment.md#bounded-m2-source-reuse-and-licensing-assessment).

## Evidence and decision

Current public `Azure-Samples/octocat-supply` main still resolves to
`65299c9df87fc466be28a6eec56d53ea1e4fa915`. Its complete tree has no named license or
notice file; metadata reports no repository license. The API manifest declares
MIT, a meaningful package-specific statement, but no frontend grant was located.
The frontend contains a copyright/all-rights-reserved footer. Artwork and designs
have no separately established reuse terms. AI authorship statements are not a
license grant or a reliable ownership/public-domain determination.

**Do not copy/adapt/distribute the complete application or its assets merely with
attribution. Permission has not been established for that use.** Do not describe
this as a finding that the API is unlicensed: its declared MIT terms may permit
selective reuse within their actual scope, with applicable copyright and license
notices. That scope/provenance does not establish rights for frontend/artwork;
partial reuse adds complexity and is not the recommended path.

Recommend independently writing the existing catalogue/search/cart/pricing and
synthetic persistence behaviours from our own requirements, including original
UI, data, tests, migrations, configuration and simple visuals. Retain the two-app
architecture and candidate `apps/octocat-supply/` directory for continuity; the
path is an internal reference label, not a claim to distribute the upstream app.
Use a neutral original display identity such as `Supply Demo`. Acknowledge the
OctoCAT reference with a factual source link without copying its code, prose,
layout, logos or images. Do not ask agents to translate/paraphrase upstream code.
This is independent authorship, **not a certified clean-room process**; references
have already been inspected. The M2 implementation is recorded below.

## Private repository and public portfolio

Private development does not supply missing copy/adapt rights. Legitimately
MIT-covered components can be used privately and distributed with required
notices; MIT does not require publication of our own source. GitHub's public
viewing/service-fork rights are not a blanket external reuse license. See the
primary sources linked in the assessment, including
[GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
and [MIT terms](https://opensource.org/license/mit).

For eventual public publication, review source/history, images/frontend bundles,
container layers, documentation and video/screenshots. Keep unknown-rights content
out of all history made public, not just the final tree. Prefer recordings of our
own implementation with original visuals. Treat brand use separately and avoid
implied Microsoft/GitHub endorsement. No visibility change is authorized here.

## Original license and retained obligations

The owner selected **MIT** for original project code; the root/app LICENSE files
use the project contributors attribution and 2026 year.
It fits a simple permissive portfolio with private development and optional public
publication. It does not require making the repository public. The license text
is in LICENSE, not this ADR; third-party work is excluded from original authorship.
MIT grants recipients redistribution rights; private repository access controls
do not impose a private-only license on copies legitimately received under MIT.

Third-party material keeps its own terms. At adoption, record exact package/base
versions, provenance, license/notice files and any modifications; preserve MIT
copyright/permission notices, and applicable Apache-2.0 license/NOTICE content and
modification notices. Review other licenses independently rather than assuming
that an MIT root license covers everything. Apache-2.0 for original code remains
an alternative if explicit patent licensing is required; MIT is simpler for the
current need. M2 records adopted packages, retained runtime licenses and original
assets in the notices/inventory; this is not a comprehensive legal certification.

## Alternatives, gates and consequences

| Path | Disposition and gate |
| --- | --- |
| Complete upstream application/assets | Not cleared; obtain permission from actual rights holders or a clearly licensed revision covering intended files/assets and distribution. Attribution is insufficient |
| API-only MIT reuse plus new frontend | Potentially permitted within the declared package grant, subject to provenance/notice/scope review; not selected because it does not simplify the small workload enough |
| Independent synthetic functionality | Selected by owner with MIT; implemented in M2; third-party dependency/asset obligations still apply |
| Another fork/starter | Not a rights shortcut; requires its own scope/provenance/license review |

Choosing the independent route removes the need to obtain permission for upstream
material **we do not copy**; it does not declare that material reusable or erase
future dependency obligations. If later selecting direct reuse, retain its rights
gate and update this ADR before import. Owner decisions close the independent strategy and
original-license gates; public upstream access still supplies no additional rights.
The [M2 handoff](../milestones/m2-scope.md) carries the recommended route and gates.
M2 stops at the local baseline: no upstream app import, later milestone work,
cloud deployment, commit or push.

## M2 execution decision

The owner explicitly selected independently authored code, original UI/assets and
MIT in the M2 implementation request. These strategy/original-license gates are
closed. [Root LICENSE](../../LICENSE) and the application LICENSE cover original
code; third-party terms remain separate. No OctoCAT application material is copied.
See [M2 evidence](../evidence/m2-baseline.md) and the exact dependency inventory.
Direct upstream reuse remains not cleared; its historical findings above are not
changed by implementing our own workload. Earlier awaiting-selection statements
in this decision describe the assessment stage, not the current execution gate.
