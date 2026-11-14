# Local Demo Script

This is a walkthrough of the synthetic local development environment, not a
production demonstration. Impact values are estimates, not probabilities.
Do not enter real organization data.

## Start and connect

From the repository root in PowerShell, with Docker Desktop running and a
local `.env` created from `.env.example`:

```powershell
docker compose --project-name ripple-effect --env-file .env up -d --wait --wait-timeout 240
python backend\scripts\smoke_compose.py
docker compose --project-name ripple-effect --env-file .env logs api
```

Confirm the three services are healthy and the smoke script prints:

```text
PASS API readiness
PASS web application
PASS web-to-API proxy
```

Open `http://127.0.0.1:5173`. From the API startup logs, copy the synthetic
North Campus organization and local user IDs into the app's local connection
form. The IDs are development fixture data.

## Walkthrough

1. Select the **North Campus Demo** organization.
2. Open the seeded **Advanced Computing Laboratory unavailable** event and
   inspect its trigger on **Advanced Computing Laboratory**.
3. Run analysis. Inspect the affected entities and the source-to-target path
   to **Practical Session A**. The previously verified seeded run returned
   eight results; Practical Session A scored 64.8/100.
4. Open the impact graph and its ordered-list alternative. Follow the
   dependency direction from source to target; do not interpret the score as
   a probability.
5. Create a scenario and apply a hypothetical mitigation to Practical Session
   A. Run the scenario and compare its estimate with the baseline. In the
   previously verified demo, a 50% mitigation changed that scenario estimate
   from 64.8 to 32.4. The intervention is scenario-only; it does not mutate
   live records.
6. Optionally connect as the synthetic City Transport user to demonstrate
   organization scoping. Do not treat this local flow as production
   authentication.

## End the demo

Stop the app without deleting its named database volume:

```powershell
docker compose --project-name ripple-effect --env-file .env down
```

Do not use `down --volumes` unless intentionally deleting local synthetic
database data. Backup and restore instructions are in [`README.md`](../../README.md).

## Evidence and limits

The local Compose startup, smoke checks, live seeded analysis, audit creation,
and cross-organization 404 check were verified on 2026-11-14. See
[`docs/progress.md`](../progress.md) and
[`docs/reports/phase11-report.md`](../reports/phase11-report.md). These
results do not prove cloud deployment, production identity, validated UX, or
production performance.
