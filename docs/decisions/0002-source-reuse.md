# ADR 0002 — Source reuse and original-code licensing

Date: 2026-10-30. Status: **direct upstream application reuse not cleared;
independent implementation recommended, awaiting owner selection**.
Supersedes the conditional S01 adoption recommendation from M1; no application
implementation is authorized by this assessment. Owner: repository owner.
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
have already been inspected. No implementation has begun.

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

Recommend **MIT** for original project code, using the actual rights holder/year.
It fits a simple permissive portfolio with private development and optional public
publication. It does not require making the repository public. Owner selection
and addition of a proper LICENSE are future steps; no license is issued by this
ADR and no employer/contributor ownership is assumed.
MIT grants recipients redistribution rights; private repository access controls
do not impose a private-only license on copies legitimately received under MIT.

Third-party material keeps its own terms. At adoption, record exact package/base
versions, provenance, license/notice files and any modifications; preserve MIT
copyright/permission notices, and applicable Apache-2.0 license/NOTICE content and
modification notices. Review other licenses independently rather than assuming
that an MIT root license covers everything. Apache-2.0 for original code remains
an alternative if explicit patent licensing is required; MIT is simpler for the
current need. No dependency/asset selection or license audit is complete yet.

## Alternatives, gates and consequences

| Path | Disposition and gate |
| --- | --- |
| Complete upstream application/assets | Not cleared; obtain permission from actual rights holders or a clearly licensed revision covering intended files/assets and distribution. Attribution is insufficient |
| API-only MIT reuse plus new frontend | Potentially permitted within the declared package grant, subject to provenance/notice/scope review; not selected because it does not simplify the small workload enough |
| Independent synthetic functionality | Recommended; owner must select it and the original-code license before M2 implementation; third-party dependency/asset checks still apply |
| Another fork/starter | Not a rights shortcut; requires its own scope/provenance/license review |

Choosing the independent route removes the need to obtain permission for upstream
material **we do not copy**; it does not declare that material reusable or erase
future dependency obligations. If later selecting direct reuse, retain its rights
gate and update this ADR before import. Current owner decisions are strategy and
original license; there is no further permission we can infer from public access.
The [M2 handoff](../milestones/m2-scope.md) carries the recommended route and gates.
Stop after this assessment: no import, app implementation, deployment, commit or push.
