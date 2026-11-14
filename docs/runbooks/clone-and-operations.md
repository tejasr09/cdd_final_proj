# Clone, Run, Test, and Operate Ripple Effect

This guide is for a developer using a local Windows PC and PowerShell. It
covers the recommended Docker Compose setup, a native development setup, the
available tests, and the operations exposed by the app. It uses synthetic
demo data only.

> **Scope:** This is a local development/demo guide, not production
> deployment guidance. Local identity headers are not production
> authentication. Do not expose the app publicly or enter real organization
> data.

## 1. What the application does

Ripple Effect models directed dependencies between entities, then estimates
how an operational event could affect downstream entities. A dependency
`source -> target` means a change to the source may affect the target.
Displayed scores are heuristic estimates, not probabilities or guaranteed
predictions.

The application consists of:

- **React web client:** lets a user manage entities, dependencies, events,
  triggers, analyses, and what-if scenarios.
- **FastAPI backend:** validates requests, applies organization membership
  and role permissions, runs the analysis engine, and records audit events.
- **Database:** PostgreSQL in the recommended Compose setup; SQLite is
  available for native development and automated tests.
- **Analysis engine:** traverses the directed graph, scores impacts,
  preserves path provenance, and reports when configured safety limits make
  results potentially incomplete.

## 2. Prerequisites

Install these on the PC:

- Git
- Docker Desktop with the Linux container engine and Docker Compose V2
- For the native setup and test suites: Node.js 24.x, npm, Python 3.11 or
  newer within the project support range, and `uv`
- A current web browser

The Playwright browser test can use installed Google Chrome. Otherwise, its
Chromium browser can be installed from the frontend folder as described in
[Run the tests](#5-run-the-tests).

## 3. Clone the repository

The current documentation is on the Phase 11 feature branch. In PowerShell:

```powershell
git clone --branch feature/phase11-release-hardening https://github.com/tejasr09/cdd_final_proj.git
Set-Location .\cdd_final_proj
git status --short --branch
```

If that branch has been merged and you want the default branch instead, omit
`--branch feature/phase11-release-hardening` when cloning.

## 4. Start the recommended local stack

Docker Compose is the simplest way to run the full app with PostgreSQL,
migrations, synthetic seed data, API, and web client.

1. Start Docker Desktop and wait for its Linux engine to be ready.
2. From the repository root, create a local environment file and replace the
   placeholder password with a private, URL-safe development password. Never
   commit `.env` or use a production credential here.

```powershell
Copy-Item .env.example .env
notepad .env
```

3. Validate, build, start, and check the services:

```powershell
docker compose --project-name ripple-effect --env-file .env config --quiet
docker compose --project-name ripple-effect --env-file .env up --build --detach --wait --wait-timeout 240
docker compose --project-name ripple-effect --env-file .env ps
python backend\scripts\smoke_compose.py
```

The API container applies database migrations and idempotently seeds the
synthetic demo records before becoming healthy. The web container waits for
API readiness. The host ports are loopback-only:

- Web app: <http://127.0.0.1:5173>
- API documentation: <http://127.0.0.1:8000/docs>
- API liveness: <http://127.0.0.1:8000/api/v1/health/live>
- API readiness: <http://127.0.0.1:8000/api/v1/health/ready>

The smoke script should print:

```text
PASS API readiness
PASS web application
PASS web-to-API proxy
```

### Connect with the local demo identity

Read the API startup output to find the synthetic user and organization IDs:

```powershell
docker compose --project-name ripple-effect --env-file .env logs api
```

Open the web app and enter the North Campus user ID and North Campus
organization ID in the local connection form. Use the City Transport IDs to
view the other seeded organization. The local identity adapter is a
development convenience; it is not sign-in and does not make the app safe to
expose publicly.

### Stop and restart

Stop the containers without deleting the database volume:

```powershell
docker compose --project-name ripple-effect --env-file .env down
```

Start them again later with the `up --detach --wait` command above. The named
PostgreSQL volume persists across normal `down`/`up` operations. Do not use
`down --volumes` unless you intentionally want to delete local data. Local
backup and restore instructions are in [`README.md`](../../README.md).

## 5. Run the tests

Run the frontend and backend suites from their respective folders. The
commands below check style, types, unit/integration behavior, and production
builds without requiring a cloud account.

### Frontend checks

```powershell
Set-Location .\frontend
npm ci
npm run lint
npm run typecheck
npm run format:check
npm test
npm run build
```

These commands:

- install exactly the locked npm dependencies;
- check ESLint rules, TypeScript compilation, and Prettier formatting;
- run the Vitest component and API-client tests;
- compile and build the production frontend bundle.

### Browser workflow test

The Playwright test starts a temporary Vite server on `127.0.0.1:4173`. It
simulates API responses to check the UI journey from event creation through
trigger association and analysis result/path display; it is not a live
backend integration test.

If Google Chrome is installed:

```powershell
$env:PLAYWRIGHT_USE_CHROME = "1"
npm run test:e2e
Remove-Item Env:PLAYWRIGHT_USE_CHROME
```

Otherwise, install Playwright Chromium once and run the test:

```powershell
npx playwright install chromium
npm run test:e2e
```

### Backend checks

```powershell
Set-Location ..\backend
uv sync --locked
uv run --locked pytest
uv run --locked ruff check app tests scripts
uv run --locked ruff format --check app tests scripts
```

The backend tests cover graph direction and scoring, cycle/path bounds,
confidence and incomplete-run behavior, API lifecycle and validation,
membership/role authorization, cross-organization isolation, audit events,
scenario isolation, and database migrations.

To check migrations against a separate, disposable SQLite database:

```powershell
$env:DATABASE_URL = "sqlite:///./phase_check.sqlite3"
uv run --locked alembic upgrade head
uv run --locked alembic check
Remove-Item .\phase_check.sqlite3
Remove-Item Env:DATABASE_URL
```

Only run the migration check against a database you intend to use for this
check. Do not point it at production data.

### Dependency audits

From the frontend folder:

```powershell
npm audit --audit-level=low
```

From the backend folder:

```powershell
python -m uv audit --locked
```

An audit is a point-in-time check against the package advisories available to
the tool. It does not prove that the application is free of vulnerabilities.

### Compose smoke test

With the Compose stack running from the repository root:

```powershell
python backend\scripts\smoke_compose.py
```

This checks API readiness, that the web service serves the app, and that the
web server can proxy a readiness request to the API. It does not exercise
every UI workflow.

## 6. Walk through the application's operations

Use the seeded **North Campus Demo** organization for this walkthrough. The
exact labels can vary slightly with later UI updates.

### A. Manage entities

Entities represent resources, activities, groups, locations, or systems.
Create and edit entities, inspect their status and attributes, and archive
them when they should no longer be active. Archiving is a lifecycle change,
not a hard delete.

### B. Manage directed dependencies

Create a dependency from a source entity to a target entity, choose its
relationship, weight, and review status, then activate/deactivate or edit it.
The source-to-target direction is meaningful: downstream impact propagates
along the modeled direction. Self-links, duplicates, and cross-organization
references are rejected by the API.

### C. Create and open an event

Create an operational event with a title, severity, start time, and optional
duration. Associate one or more trigger entities and their exposure values.
An event must be open and have a trigger before analysis can run. Event
transitions are validated; reopening resolved or archived events is restricted
to administrators.

### D. Run and inspect an analysis

Run analysis from an open event. The API saves a run snapshot, algorithm
version, effective configuration, results, paths, and an audit record. In
the results, inspect:

- affected entity, estimated score, and impact level;
- minimum propagation depth;
- confidence value and explanation (dependency review quality, not
  likelihood);
- the primary source-to-target path and its dependency provenance;
- any safety-limit warning indicating the result may be incomplete.

Analysis is synchronous. Scores are heuristic estimates, not probabilities,
recommendations, or guarantees.

### E. Explore a what-if scenario

Create a scenario from a completed baseline run. Change its event overlay or
add scenario-only interventions such as entity mitigation, dependency weight
override, dependency deactivation, or a hypothetical dependency. Run the
scenario and compare estimated results with the baseline.

Scenario runs replay an immutable baseline snapshot and do not modify live
events, entities, or dependencies. The application does not provide a
“apply scenario to live data” operation.

### F. Organization boundaries and audit

The active organization scopes entities, dependencies, events, triggers,
analysis runs, and scenarios. The backend checks membership and role
permissions. A non-member receives 404 for another organization's protected
records; a member who lacks permission receives 403. Successful state changes
write audit events, but a user-facing audit-log browser is not implemented.

For the API routes, request/response behavior, pagination, status codes, and
OpenAPI contract, see [`docs/api/README.md`](../api/README.md) and
<http://127.0.0.1:8000/docs> while running locally.

## 7. Troubleshooting

- **Docker commands cannot connect:** start Docker Desktop and confirm its
  Linux engine is ready.
- **A port is already in use:** stop the other process using port 5173 or
  8000, or use the native frontend on a different Vite port. Do not expose
  the API to a public interface.
- **API stays unhealthy:** inspect `docker compose ... logs api db`; check
  `.env` values and PostgreSQL startup before restarting.
- **The browser cannot connect:** verify all three Compose services are
  healthy, then run `python backend\scripts\smoke_compose.py`.
- **The local form does not connect:** use the exact user and organization
  IDs printed by the seed output; do not enter a role value.
- **Playwright cannot find Chromium:** install it using
  `npx playwright install chromium`, or set `PLAYWRIGHT_USE_CHROME=1` if
  Google Chrome is installed.
- **Tests fail after changing files:** read the first failure and its test
  output. Do not dismiss a failure as a successful test run; rerun the
  smallest relevant command after fixing it.

## 8. Native development alternative

The native setup runs the API on SQLite and the frontend on Vite; use it when
you want hot reload without Docker. Follow the [Run locally](../../README.md#run-locally)
and [Verify](../../README.md#verify) sections in the root README. Run the API
and frontend in separate PowerShell terminals. Set `DATABASE_URL`,
`APP_ENV=development`, and `ENABLE_LOCAL_AUTH=true` only in the backend
terminal. Seed data must remain synthetic and local.

## 9. Related documentation

- [Root README](../../README.md): project overview, setup, Compose, backup,
  and restore.
- [API guide](../api/README.md): routes, authorization, errors, analysis,
  scenarios, and OpenAPI.
- [Demo walkthrough](./phase11-demo.md): short seeded demonstration.
- [Limitations](../limitations.md): outstanding human evidence, production
  gaps, and future work.
- [Phase 11 evidence index](../evidence-index.md): what has and has not been
  verified.
