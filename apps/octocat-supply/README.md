# Morrow Supply — local commerce baseline

An independently written React/TypeScript and TypeScript/SQLite demonstration.
All twelve products, prices, illustrations and UI are original synthetic material.
OctoCAT Supply is a conceptual reference; none of its source, tests, schema, images
or branding was copied. Original code is [MIT](LICENSE); dependency terms are in
[the project register](../../THIRD_PARTY_NOTICES.md), [exact inventory](dependencies.json)
and the browser's `/third-party-notices.txt`.

## Prerequisites and clean local setup

Use **Node 24.22.2 and its bundled npm 11.19.1**, plus Docker Desktop/Compose for
containers. `.node-version`, package engines and immutable Docker base digests
record the chosen toolchain. Obtain Node from its official distribution or your
version manager; do not substitute the system Node 22. One application-level
manifest/lockfile serves both folders; no workspace manager is required.

From this directory (`apps/octocat-supply`):

```sh
node --version
npm --version
npm ci --ignore-scripts
npm run licenses
npm run typecheck
npm run lint
npm run build
npm test
npm exec -- playwright install chromium
npm run test:e2e
```

`npm ci --ignore-scripts` intentionally disables lifecycle scripts; the locked
platform binaries used by Vite/tsx work without them on the tested platforms.
`licenses` regenerates the inventory and browser notices from installed primary
package metadata/text. Do not assume the root MIT license relicenses dependencies.
The E2E command starts an isolated API at 4174 and UI at 4173, initializes only
`data/e2e.sqlite`, then shuts its children down. Test DBs are separate from normal
demo data; browser tests exercise the real API and do not require cloud accounts.

For a native interactive session, prepare data explicitly:

```sh
npm run db:migrate
npm run db:seed
npm run start:api
```

In another terminal in the same directory:

```sh
npm run dev:web
```

Open `http://127.0.0.1:5173`. Stop both processes with Ctrl+C. The API binds only
127.0.0.1:3000. It never migrates, seeds or resets automatically on startup; its
readiness is 503 until the schema and expected fixture are present. To inspect the
whole production frontend/proxy boundary, use the container path below instead.

## Production containers on localhost:8080

Start Docker Desktop first. From this directory:

```sh
docker compose build
docker compose run --rm api node api/dist/database-cli.js migrate
docker compose run --rm api node api/dist/database-cli.js seed
docker compose up -d --wait --wait-timeout 40
```

Open `http://127.0.0.1:8080`. Only that loopback port is published; the API is
reachable only on the Compose network. Both services run as non-root with read-only
root filesystems, dropped capabilities and bounded resources. API data/WAL lives
in the dedicated `morrow-supply-m2_demo-data` local named volume, not network storage.
Nginx uses the same API upstream for `/api` and `/health/ready`. `/health/live`
only checks the process; static homepage success does not prove dependency health.

Run browser smoke tests through the actual built Nginx/API containers:

```sh
E2E_BASE_URL=http://127.0.0.1:8080 npm run test:e2e
npm run test:containers
```

`test:containers` temporarily recreates these local API/frontend containers, checks
retained-volume cart persistence, and changes only the frontend's dependency port
3000→3001. It first verifies 3001 is closed, expects static 200 versus journey/
readiness 503, restores 3000 in `finally`, verifies fresh recovery, and deletes only
its own synthetic cart. It writes `test-results/container-smoke.json`; it never
changes Azure resources or claims an SRE Agent performed the repair. Do not run
this disruptive local test during another demonstration. It accepts only the
project names `morrow-supply-m2` and `morrow-supply-m2-clean`.

## Data, reset, configuration and teardown

Seed: IDs 1–12; feeder 12999p, toy 1999p, remaining products 1500p. Categories are
feeding/play/everyday. Search trims and ignores case, treats SQL wildcards literally,
and supports category plus name/price sorting with stable ID ties. Cart updates set
absolute integer quantities 1–99 and never trust browser prices. Maximum 100 lines.
No public product administration, checkout, tax, shipping, accounts or real payments.

The user-requested discount extends the earlier design: **10% off a subtotal of
30000p or more, rounded down to whole pence**, automatic and non-stacking. Two
feeders plus three toys: subtotal 31995p, discount 3199p, total 28796p. Below the
threshold the discount is zero. Totals are server-authoritative integer arithmetic.

Reset invalidates carts. Stop the native API or demo first, then explicitly run:

```sh
npm run db:reset
```

For the container volume instead:

```sh
docker compose stop
docker compose run --rm api node api/dist/database-cli.js reset --confirm-demo-reset
docker compose up -d --wait
```

Reset is transactional deletion/reseeding of this demo's own tables, not recursive
filesystem removal. The CLI only permits relative `data/demo.sqlite` or
`data/e2e.sqlite`, rejects absolute/URL/unrelated/linked paths, and requires the
explicit reset flag. Migrations are ordered and checksummed; editing an applied
migration fails. Never reset an unknown DB to bypass a migration mismatch.

`.env.example` documents non-secret options; Vite/native Node read environment
variables supplied by the shell (they do not automatically load that example).
For a manual container fault, run `API_PORT=3001 docker compose up -d --no-deps
--force-recreate frontend`, then restore with `API_PORT=3000` using the same command.
No permissive CORS: requests from foreign browser origins are rejected, and no
cloud credentials or external image/font calls are needed.

```sh
docker compose down
```

This stops/removes only this project's containers/network and retains data. For a
deliberate **destructive** disposal of this project's synthetic data, use
`docker compose down --volumes`; it is not the normal stop command. A fresh named
volume needs explicit migrate/seed again. Do not use global Docker prune commands.

## Scope and verification limits

Node's bundled `node:sqlite` is used instead of a separately compiled native addon;
it is release-candidate API in this exact Node version. Local tests do not establish
cloud driver compatibility, durable backups, availability SLOs, payment correctness
or authentication. Cart IDs are opaque demo references, not credentials. The
application is only for loopback synthetic use. Azure SQL/auth/deployment, agents,
CI/CD and cloud telemetry remain later milestones.

See [M2 evidence](../../docs/evidence/m2-baseline.md) for actual commands, outcomes,
clean-copy reproduction, platform versions, source provenance and remaining gaps.
