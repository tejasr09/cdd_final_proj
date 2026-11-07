# Ripple Effect

Ripple Effect is a decision-support application for exploring how a modeled change may propagate through directed dependencies. Impact values are transparent estimates, not probabilities or guaranteed predictions.

## Current status

Phase 1 foundation, the Phase 2 synthetic UX prototype, and Phase 3 data/tenancy foundations are present. Phase 4 adds tenant-authorized entity, dependency, event, and event-trigger API routes with pagination and an OpenAPI snapshot. Phase 2 remains partial: interviews, a human-owned Figma artifact, and usability validation are still TODO(human). The frontend prototype remains separate from the API and its mock results are not analysis output; the analysis engine is not yet implemented.

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

The frontend currently opens the synthetic Phase 2 click-through prototype.
Its generated graph contains 10,018 synthetic entities and 30,017 synthetic
relationships across two demo organizations. Result scores and scenario
deltas are illustrative placeholders, not engine output or benchmark results.
See [`docs/ux/prototype-readme.md`](./docs/ux/prototype-readme.md) before using
or presenting it.

## Verify

Frontend:

```powershell
Set-Location frontend
npm run lint
npm run typecheck
npm run format:check
npm run build
```

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
