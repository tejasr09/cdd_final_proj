# Ripple Effect

Ripple Effect is a decision-support application for exploring how a modeled change may propagate through directed dependencies. Impact values are transparent estimates, not probabilities or guaranteed predictions.

## Current status

Phases 1 and 3–7 are implemented, including the tenant-authorized API, deterministic analysis, scenario simulation, and the React/TypeScript workflow. Phase 8 is complete and its closure was approved on 2026-11-11: the pinned Python Alpine API image passes local full-severity Trivy scans; Compose migration, seed, health, proxy, smoke, and event-to-analysis checks pass. GitHub CI run [43055479057](https://github.com/tejasr09/cdd_final_proj/actions/runs/43055479057) passed all checks. Phase 9 preparation is in progress on `feature/phase9-acr-aci`: Bicep templates and a human-operated ACR/ACI runbook are drafted for an existing PostgreSQL service. The templates have not been compiled, and no image was pushed or cloud resource deployed. Public ingress remains disabled because production authentication and TLS ingress are not implemented. Phase 2 remains partial: interviews, a human-owned Figma artifact, and usability validation are still TODO(human).

The project brief is maintained in [`agent-brief.md`](./agent-brief.md) and [`agent-brief-continuation.md`](./agent-brief-continuation.md); read them together. Phase 9 preparation and its limits are recorded in [`docs/reports/phase9-report.md`](./docs/reports/phase9-report.md) and the human-operated [`docs/runbooks/phase9-acr-aci.md`](./docs/runbooks/phase9-acr-aci.md).

## Requirements

- Node.js 24.14.1 or a compatible version supported by Vite.
- Python 3.11 or newer within the selected support range.
- npm and uv.
- Docker Desktop for the optional local Compose stack. Compose builds and startup are verified locally; the current Phase 8 GitHub CI run is linked above.

If `uv` is not installed, install the pinned tool from PyPI. With a pip `--user` install on Windows, add its Scripts directory to the current PowerShell session:

```powershell
python -m pip install --user uv==0.13.7
$pythonTag = python -c "import sys; print(f'Python{sys.version_info.major}{sys.version_info.minor}')"
$uvScripts = Join-Path (python -m site --user-base) "$pythonTag\Scripts"
$env:PATH = "$uvScripts;$env:PATH"
uv --version
```

## Run locally

The following backend walkthrough uses a local SQLite database. SQLite is
convenient for development and tests; PostgreSQL remains the authoritative
persistence target.

In PowerShell, from the repository root, prepare the backend database and
seed synthetic data:

```powershell
Set-Location backend
uv sync --locked
$env:DATABASE_URL = "sqlite:///./ripple_effect.sqlite3"
uv run --locked alembic upgrade head
$env:APP_ENV = "development"
uv run --locked python -m app.seed
$env:ENABLE_LOCAL_AUTH = "true"
```

In the same terminal, start the API:

```powershell
uv run --locked uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, start the frontend:

```powershell
Set-Location frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open `http://localhost:5173`. API liveness and readiness are available at:

- `http://127.0.0.1:8000/api/v1/health/live`
- `http://127.0.0.1:8000/api/v1/health/ready`
- `http://127.0.0.1:8000/docs`

Liveness reports process status; readiness checks database connectivity and
returns HTTP 503 when the database is unavailable. The local seed is
deterministic, idempotent and synthetic; it is restricted to development/test
and local databases. Local API requests use the seed user and organization IDs
printed by the seed command in the `X-Local-User-ID` and
`X-Active-Organization-ID` headers. Local authentication is disabled by
default; enabling it as shown is only for local development/test and is not
production authentication.

See [`docs/api/README.md`](./docs/api/README.md) for routes, authorization,
pagination, errors, concurrency checks, and OpenAPI snapshot instructions.
Use the analysis routes documented there to run an open seeded event and
inspect its paginated results and path provenance. Analysis values are
heuristic estimates, not probabilities or guaranteed predictions.
The scenarios routes create versioned what-if overlays from a completed live
analysis, run against its immutable snapshot, and compare estimated changes
without mutating live records.

The frontend connects to the API through Vite's same-origin `/api` proxy by
default; leave the API base URL blank in the connection form when running the
local stack above. The local user and organization IDs are printed by the
synthetic seed command. Local identity headers are development-only, not
production authentication. The former synthetic click-through prototype is
documented as historical UX work in
[`docs/ux/prototype-readme.md`](./docs/ux/prototype-readme.md).

## Verify

Frontend:

```powershell
Set-Location frontend
npm run lint
npm run typecheck
npm run format:check
npm test
npm run build
```

The Playwright workflow test can use an installed browser. With Google Chrome
installed, run it in PowerShell with:

```powershell
$env:PLAYWRIGHT_USE_CHROME = "1"
npm run test:e2e
Remove-Item Env:PLAYWRIGHT_USE_CHROME
```

Otherwise, install the Playwright Chromium browser once with
`npx playwright install chromium`, then run `npm run test:e2e`.

Backend:

```powershell
Set-Location backend
uv run --locked pytest
uv run --locked ruff check app tests scripts
uv run --locked ruff format --check app tests scripts
$env:DATABASE_URL = "sqlite:///./ripple_effect.sqlite3"
uv run --locked alembic check
```

## Run with Docker Compose

The Compose stack is for local development and uses PostgreSQL, the
migration-aware API image, and a production-built static frontend. It enables
the local identity adapter and synthetic seed data only inside this local
Compose configuration. Do not expose this setup as a production identity
solution.

In PowerShell from the repository root, copy the example and replace its
database password with a local-only, URL-safe value. `.env` is ignored by Git
and is not copied into either image:

```powershell
Copy-Item .env.example .env
notepad .env
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
python backend\scripts\smoke_compose.py
```

The API waits for PostgreSQL, applies Alembic migrations, and idempotently seeds
synthetic demo records before becoming healthy. The web service starts after
the API readiness check succeeds. PostgreSQL uses a named volume and is not
published to the host. The API and web ports bind only to `127.0.0.1`.

Open `http://127.0.0.1:5173`; the frontend proxies API calls over the internal
Compose network. `http://127.0.0.1:8000/docs` exposes the local API docs. To
find the local demo user and organization IDs, inspect the seed output:

```powershell
docker compose logs api
```

Enter the appropriate ID pair into the local connection form. Smoke-test
success prints:

```text
PASS API readiness
PASS web application
PASS web-to-API proxy
```

Stop the stack with `docker compose down`; the named local database volume is
preserved.

Compose builds separate local-only image tags, `ripple-effect-api:local` and
`ripple-effect-web:local`. For a release, use a version tag and a commit-SHA
tag for each image; do not use `latest` as the only identifier. After an
approved registry push, inspect and record each registry-reported digest:

```powershell
docker buildx imagetools inspect <registry>/<namespace>/ripple-effect-api:<version>
docker buildx imagetools inspect <registry>/<namespace>/ripple-effect-web:<version>
```

Use the reported `sha256` digest to promote the same image between
environments, rather than rebuilding. ACR is the approved cloud target, but no
registry instance or release digest has been created or published.

When Docker is available, Compose configuration can also be inspected with:

```powershell
docker compose --env-file .env.example config --quiet
```

PostgreSQL is the authoritative target. The migration and seed commands above
also work with a local PostgreSQL URL supplied through `DATABASE_URL`; ensure
it points only to a local development database when seeding.

## Pull-request checks

The approved workflow in `.github/workflows/ci.yml` runs on pull requests and
pushes to `feature/delivery-build`. It runs frontend and backend quality
checks, dependency audits, a Compose image build/start, Trivy scans of both
images, and the Compose smoke test. Actions are pinned to immutable commit
SHAs, with read-only repository permissions. GitHub Actions run
[43055479057](https://github.com/tejasr09/cdd_final_proj/actions/runs/43055479057)
passed all configured checks, including dependency audits and both image
scans. Phase 9 changes have not yet been included in CI.

## Project guidance

- [`AGENTS.md`](./AGENTS.md) contains persistent coding and safety rules.
- [`docs/progress.md`](./docs/progress.md) is the phase handoff and evidence index.
- [`docs/adr/`](./docs/adr/) records approved design decisions.
- [`docs/viva-notes.md`](./docs/viva-notes.md) distinguishes planned concepts from implemented work.
- [`docs/architecture/deployment.md`](./docs/architecture/deployment.md) summarizes the local and proposed cloud deployment architecture.
