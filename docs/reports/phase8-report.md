# Phase 8 Report — Docker, Compose and CI

Date: 2026-11-11
Branch: `feature/delivery-build`
Base commit: `4580fe9`; latest completed GitHub run reviewed here is
[43051236619](https://github.com/tejasr09/cdd_final_proj/actions/runs/43051236619)
for commit `6bc7306`.

## 1. Objective

Provide production-oriented local images, a reproducible PostgreSQL/API/web
Compose stack, smoke checks, and approved pull-request CI. Phase 8 was approved
by the human. Local Compose acceptance is verified. The latest GitHub CI run
passed quality, the web image scan, and Compose smoke, but failed the API image
scan. Debian OS advisories remain in that image without current package fixes.
Exit criteria remain partial; Phase 9 is not started.

## 2. Work completed

- Replaced the backend image with a locked, non-root runtime; added startup
  migration and optional synthetic-seed handling in
  [`backend/Dockerfile`](../../backend/Dockerfile) and
  [`backend/docker-entrypoint.sh`](../../backend/docker-entrypoint.sh).
- Added a multi-stage frontend build served by unprivileged Nginx, including
  SPA routing, `/api/` proxying, and health checks in
  [`frontend/Dockerfile`](../../frontend/Dockerfile) and
  [`frontend/nginx.conf`](../../frontend/nginx.conf).
- Updated the final Nginx image stage to upgrade Alpine packages from the
  current v3.23 repositories, then return to the image's non-root UID. The
  rebuilt web image passes the configured local Trivy 0.74.0 scan.
- Updated [`docker-compose.yml`](../../docker-compose.yml) for health-ordered
  PostgreSQL/API/web startup, a named database volume, loopback-only host
  ports, and local-only auth and seed configuration.
- Added [`backend/scripts/smoke_compose.py`](../../backend/scripts/smoke_compose.py),
  excluded local secrets/databases from build contexts, added organization IDs
  to seed output, and documented local startup and image tag/digest policy in
  [`README.md`](../../README.md).
- After separate approval, added
  [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) for frontend and
  backend checks, dependency audits, migration validation, Compose
  build/start/smoke, and Trivy image scans. Direct action references are pinned
  to immutable SHAs. The GitHub-maintained actions are MIT-licensed; Trivy
  Action is Apache-2.0. The approved workflow ran on pushes to the feature
  branch; the latest run is linked below.
- Updated the web-scan and smoke-step conditions to continue after an API scan
  failure when Compose startup succeeded. The API scan remains a failing gate;
  run 43050682639 confirmed that the web scan and smoke steps now complete.
- Updated the container architecture, viva notes, and
  [`docs/progress.md`](../progress.md).
- Added [`.gitattributes`](../../.gitattributes) to ensure shell scripts retain
  Unix LF line endings on Windows checkouts; this fixes the entrypoint failure
  found during the first real container startup.

## 3. Decisions

- Compose is a local-development stack; it does not implement production
  authentication or publish images.
- Local image tags are `ripple-effect-api:local` and
  `ripple-effect-web:local`. Release version/SHA tags and digest promotion are
  documented, but no registry was selected or contacted.
- The CI workflow has read-only repository permissions and runs on pull
  requests and pushes to `feature/delivery-build`. The branch-push trigger was
  added with the human's explicit approval.
- No ADR was added or changed. Phase 2 remains human-led and incomplete.

## 4. Verification performed

| Command/check | Result | Evidence |
|---|---|---|
| `docker compose --env-file .env.example config --quiet` | PASS | Compose config parsed; services are `db`, `api`, and `web`. |
| `python backend\scripts\smoke_compose.py` | PASS | API readiness, web response, and Vite-to-API proxy passed against the local SQLite API and Vite server. This did not test Compose, Nginx, or PostgreSQL. |
| `backend\.venv\Scripts\python.exe -m pytest` | PASS | 88 backend tests passed. |
| Backend Ruff check and format check for `app tests scripts` | PASS | Ruff clean; 20 files already formatted. |
| `npm test -- --run --pool=forks --maxWorkers=1` in `frontend` | PASS | 12 tests passed. |
| Frontend lint, format, type-check, and production build | PASS | ESLint, Prettier, TypeScript, and Vite build succeeded. |
| SQLite `alembic check` | PASS | No new upgrade operations detected. |
| `.\frontend\node_modules\.bin\prettier.cmd --check .github\workflows\ci.yml` | PASS | Workflow YAML parsed and matched formatting. |
| `git diff --check` | PASS | No whitespace errors. |
| `docker info --format '{{.ServerVersion}}'` | PASS | Docker Desktop Linux engine version `29.8.2`. |
| `docker compose --project-name ripple-phase8-check --env-file .env.example up --build --detach --wait --wait-timeout 240` | PASS | Both images built; PostgreSQL, API and Nginx all reached healthy state. |
| First isolated Compose startup | FAIL, resolved | CRLF in the new shell entrypoint caused `/bin/sh` to reject `set -eu`; normalized the file and added `.gitattributes`, then rebuilt successfully. |
| `python backend\scripts\smoke_compose.py` against Compose | PASS | API readiness, Nginx web page, and Nginx-to-API proxy passed. |
| Compose API event-to-analysis journey | PASS | Created event, attached trigger, opened event, ran analysis; 8 results returned. |
| Chrome browser journey through Compose | PASS | Connected via Nginx, created event, added trigger, opened it, and ran analysis without page errors. |
| Container user/health inspection | PASS | API ran as `appuser`, web as non-root UID 101; API, web and PostgreSQL were healthy. |
| `docker compose --project-name ripple-phase8-check --env-file .env.example down --volumes --remove-orphans` | PASS | Removed only the isolated test containers/network and its temporary database volume; Docker Desktop remains running. |
| Docker engine on 2026-11-11 | PASS | Docker Desktop Linux engine version `29.9.2`. |
| GitHub Actions run [42640812502](https://github.com/tejasr09/cdd_final_proj/actions/runs/42640812502), commit `3e6926d` | PARTIAL | Quality job passed. Compose build/start passed; `Scan API image` failed, so web scan and smoke step were skipped by the earlier conditions. |
| GitHub Actions run [43050682639](https://github.com/tejasr09/cdd_final_proj/actions/runs/43050682639), commit `5186ab7` | PARTIAL | Quality passed; API image scan failed; web image scan and Compose smoke both passed. |
| GitHub Actions run [43051236619](https://github.com/tejasr09/cdd_final_proj/actions/runs/43051236619), docs-only commit `6bc7306` | PARTIAL | Repeated the result: quality passed; API image scan failed; web image scan and Compose smoke both passed. |
| Latest CI `npm audit` and `uv audit --locked` | PASS | Both dependency audit steps passed in the quality job; npm reports zero findings after the `minimatch` 11.0.1 override. |
| Local API image Trivy 0.74.0 scan (`vuln,secret`, all severities) | FAIL | 201 Debian OS findings: 15 unknown, 65 low, 74 medium, 47 high, 0 critical; no secrets. Findings had no fixed versions; current apt candidates matched installed versions. |
| Local web image scan before remediation | FAIL | Trivy 0.74.0 reported 238 Alpine findings, including 1 critical and 55 high. `apk policy` showed patched versions available from Alpine v3.23. |
| Frontend image rebuild and Trivy 0.74.0 rescan | PASS | `apk update && apk upgrade` updated runtime packages; scan found zero vulnerabilities and zero secrets. |
| CI web image scan in run 43051236619 | PASS | Trivy action completed successfully on the updated web image. |
| Isolated Compose rebuild/start after frontend image update | PASS | `docker compose` with a temporary validation-only port override built the images and reached healthy PostgreSQL/API/web services. |
| Compose smoke against updated web image | PASS | `python backend\scripts\smoke_compose.py --api-url http://127.0.0.1:18000 --web-url http://127.0.0.1:15173` passed API readiness, web response and Nginx-to-API proxy checks. |
| CI Compose smoke in run 43051236619 | PASS | The smoke step ran after the API scan failed and passed, verifying the workflow continuation condition. |
| Post-validation cleanup | PASS | Removed only the isolated test stack, network and temporary database volume; retained local image tags. |
| CI workflow formatting (`prettier --check .github/workflows/ci.yml`) | PASS | YAML parses and formats cleanly; run 43050682639 confirmed the new continuation conditions. |

## 5. Test results

- Tests run: 88 backend tests, 12 frontend tests, Compose smoke checks, and
  real Compose API and browser journeys. Latest CI quality checks also passed.
- Passed: all listed backend/frontend tests and the local smoke checks.
- Failed: no application test suite failed. Docker engine availability was
  initially blocked; Docker Desktop was then started and the full local
  Compose verification passed. The first container attempt exposed the
  resolved CRLF issue.
- In run 43050682639, the web scan and Compose smoke ran and passed despite
  the preceding API scan failure. The API image remains unclean.
- Coverage: not measured.
- Known gaps: API Debian advisories have no current package fixes; local
  PostgreSQL verification is not production-scale evidence.

## 6. Security and data integrity

- Tenant-isolation and authorization code was not changed; the existing
  backend suite, including tenancy/API checks, passed.
- Trivy 0.74.0 local `vuln,secret` scans reported zero secrets in either
  image. Build contexts exclude environment files and local SQLite/database
  files.
- Dependency/container scan: CI configuration includes `npm audit`,
  `uv audit --locked`, and Trivy scans for vulnerabilities and secrets across
  all severities. The latest CI dependency audits passed. The updated web
  image scan passed locally.
- The API image scan remains a blocker: local Trivy reported 201 Debian OS
  findings, including 47 high and no critical findings. The flagged high
  findings had no fixed versions in the current Trivy data, and apt candidates
  were equal to the installed versions. The API Dockerfile already upgrades
  available packages and removes unused base pip/setuptools/wheel.
- No scan severity was reduced, and no vulnerability ignore list was added.
- Audit-log behavior and application authorization were not changed.

## 7. Evidence integrity

- Evidence produced: local test/check results above, Compose syntax validation,
  smoke results against local services, and the checked-in CI workflow.
- Evidence still TODO(human): successful API image scan after upstream fixes
  or a human-approved alternative image strategy, plus Phase 2 interviews,
  Figma, and usability results.
- Hypotheses about UX remain unvalidated.
- GitHub quality success is claimed for runs 42640812502, 43050682639, and
  43051236619. The latter two also passed web scan and smoke; the full workflow
  is not green because the API scan failed. No registry push, digest, or cloud
  deployment is claimed.
- The pre-existing untracked `backend/ripple_effect.sqlite3` demo database was
  not added to the changes.

## 8. Deviations and blockers

- A first container startup failed because Windows checkout line endings made
  the shell entrypoint invalid. LF normalization and a `.gitattributes` rule
  fixed the root cause; the subsequent image build, startup, health and smoke
  checks passed.
- GitHub run 43051236619 passed quality, web image scan, and smoke but failed
  the API Trivy scan. The local API image still has unpatched Debian OS
  advisories; a Debian 12 base comparison had more findings, including
  critical findings, so an older base is not a suitable workaround.
- The original web image had patched Alpine package versions available. Adding
  `apk update && apk upgrade` to its runtime stage resolved the local web scan;
  Compose health and smoke checks passed afterward.
- The npm audit issue was resolved with the `minimatch` override; npm and uv
  audits pass in the latest CI quality job.

## 9. Progress file

[`docs/progress.md`](../progress.md) records the current phase, branch
`feature/delivery-build`, base commit `4580fe9`, completed and pending work,
verification results, blockers, approvals, and the next actions.

## 10. Human review required

1. Review the remaining API Debian findings and decide whether to wait for
   upstream package fixes or approve investigation of a different supported
   runtime base. Do not waive findings or weaken thresholds.
2. Review the Phase 8 partial exit assessment. Do not start Phase 9 or merge
   until the API scan is resolved and the phase is explicitly reviewed.
3. Keep the untracked local demo database out of commits.

## 11. Phase exit assessment

- Exit criteria met: **PARTIAL**.
- Evidence-backed explanation: Compose configuration, local application
  checks, Docker image builds, PostgreSQL migrations/seeding, service health,
  Nginx proxy, smoke checks, and the event-to-analysis browser journey passed.
  GitHub quality, dependency audits, web scan, and smoke passed, but the API
  image scan failed. Current Debian apt repositories provide no fix for the
  API findings.
- Recommended next: remain in Phase 8 and obtain human review of the API image
  findings. Do not start Phase 9.
