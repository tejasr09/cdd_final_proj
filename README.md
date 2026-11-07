# Ripple Effect

Ripple Effect is a decision-support application for exploring how a modeled change may propagate through directed dependencies. Impact values are transparent estimates, not probabilities or guaranteed predictions.

## Current status

Phase 1 foundation, Phase 3 data/tenancy foundations, Phase 4 APIs, and Phase 5 deterministic analysis are implemented. Phase 6 integrates the React/TypeScript frontend with the tenant-authorized API for event and trigger workflows, entity/dependency management, analysis history, impact explanations, and an accessible React Flow graph with a keyboard-friendly path alternative. Phase 2 remains partial: interviews, a human-owned Figma artifact, and usability validation are still TODO(human).

The project brief is maintained in [`agent-brief.md`](./agent-brief.md) and [`agent-brief-continuation.md`](./agent-brief-continuation.md); read them together.

## Requirements

- Node.js 24.14.1 or a compatible version supported by Vite.
- Python 3.11 or newer within the selected support range.
- npm and uv.
- Docker Desktop for the optional local Compose stack. Docker was unavailable during the latest data-foundation checks; Compose migration wiring remains future work.

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

Compose has not yet been updated to run Alembic before the API; that work is
part of the delivery phase. Do not treat the current Compose stack as a
reproducible database-backed startup path. When Docker is available, the
existing configuration can be inspected with:

```powershell
docker compose config
```

PostgreSQL is the authoritative target. The migration and seed commands above
also work with a local PostgreSQL URL supplied through `DATABASE_URL`; ensure
it points only to a local development database when seeding.

## Project guidance

- [`AGENTS.md`](./AGENTS.md) contains persistent coding and safety rules.
- [`docs/progress.md`](./docs/progress.md) is the phase handoff and evidence index.
- [`docs/adr/`](./docs/adr/) records approved design decisions.
- [`docs/viva-notes.md`](./docs/viva-notes.md) distinguishes planned concepts from implemented work.
