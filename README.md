# Ripple Effect

Ripple Effect is a decision-support application for exploring how a modeled change may propagate through directed dependencies. Impact values are transparent estimates, not probabilities or guaranteed predictions.

## Current status

Phase 1 foundation: React/Vite frontend and FastAPI health API. Authentication, persistence, dependency editing, ripple analysis, and scenarios are planned for later approved phases and are not implemented yet.

The project brief is maintained in [`agent-brief.md`](./agent-brief.md) and [`agent-brief-continuation.md`](./agent-brief-continuation.md); read them together.

## Requirements

- Node.js 24.14.1 or a compatible version supported by Vite.
- Python 3.11 or newer within the selected support range.
- npm and uv.
- Docker Desktop only for the optional local Compose stack. The Docker daemon was unavailable during Phase 1 setup, so Compose has not been run.

If `uv` is not installed, install the pinned tool from PyPI. With a pip `--user` install on Windows, add its Scripts directory to the current PowerShell session:

```powershell
python -m pip install --user uv==0.13.7
$pythonTag = python -c "import sys; print(f'Python{sys.version_info.major}{sys.version_info.minor}')"
$uvScripts = Join-Path (python -m site --user-base) "$pythonTag\Scripts"
$env:PATH = "$uvScripts;$env:PATH"
uv --version
```

## Run locally

In PowerShell, from the repository root:

```powershell
Copy-Item .env.example .env
```

Replace the example database password in `.env` before starting Compose. Do not commit `.env`.

In one terminal, start the API:

```powershell
Set-Location backend
uv sync --locked
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
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

The Phase 1 readiness endpoint reports application startup only; database connectivity is not integrated until the data-foundation phase.

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
uv run pytest
uv run ruff check app tests
uv run ruff format --check app tests
```

Local Compose, if Docker Desktop is running:

```powershell
Set-Location ..
docker compose up --build
```

The current API does not yet use the database service. Migrations, database readiness, and seed data are later-phase work.

## Project guidance

- [`AGENTS.md`](./AGENTS.md) contains persistent coding and safety rules.
- [`docs/progress.md`](./docs/progress.md) is the phase handoff and evidence index.
- [`docs/adr/`](./docs/adr/) records approved design decisions.
- [`docs/viva-notes.md`](./docs/viva-notes.md) distinguishes planned concepts from implemented work.
