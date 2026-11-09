# Phase 8 Report — Docker, Compose and CI

Date: 2026-11-09
Branch: `feature/delivery-build`
Base commit: `4580fe9`; Phase 8 delivery commit is recorded by `git log`.

## 1. Objective

Provide production-oriented local images, a reproducible PostgreSQL/API/web
Compose stack, smoke checks, and approved pull-request CI. Phase 8 was approved
by the human. Local Compose acceptance is verified; the exit criteria remain
partial because the workflow has not run on GitHub and scans have not run.

## 2. Work completed

- Replaced the backend image with a locked, non-root runtime; added startup
  migration and optional synthetic-seed handling in
  [`backend/Dockerfile`](../../backend/Dockerfile) and
  [`backend/docker-entrypoint.sh`](../../backend/docker-entrypoint.sh).
- Added a multi-stage frontend build served by unprivileged Nginx, including
  SPA routing, `/api/` proxying, and health checks in
  [`frontend/Dockerfile`](../../frontend/Dockerfile) and
  [`frontend/nginx.conf`](../../frontend/nginx.conf).
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
  Action is Apache-2.0. No workflow run or remote operation occurred.
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
| Container user/health inspection | PASS | API ran as `appuser`, web as `nginx`; API, web and PostgreSQL were healthy. |
| `docker compose --project-name ripple-phase8-check --env-file .env.example down --volumes --remove-orphans` | PASS | Removed only the isolated test containers/network and its temporary database volume; Docker Desktop remains running. |
| GitHub Actions execution | NOT RUN | The approved branch push has not yet been performed. |
| Full `npm audit` | KNOWN FAILURE | Existing audit evidence reports 10 moderate development-tool findings through `minimatch`; the workflow deliberately does not suppress them. |

## 5. Test results

- Tests run: 88 backend tests, 12 frontend tests, three Compose smoke checks,
  and real Compose API and browser journeys.
- Passed: all listed backend/frontend tests and the local smoke checks.
- Failed: no application test suite failed. Docker engine availability was
  initially blocked; Docker Desktop was then started and the full local
  Compose verification passed. The first container attempt exposed the
  resolved CRLF issue.
- Skipped: GitHub CI and automated dependency/container scans.
- Coverage: not measured.
- Known gaps: no remote CI/scan run; local PostgreSQL verification is not
  production-scale evidence.

## 6. Security and data integrity

- Tenant-isolation and authorization code was not changed; the existing
  backend suite, including tenancy/API checks, passed.
- Secret scan: not run. Build contexts exclude environment files and local
  SQLite/database files.
- Dependency/container scan: CI configuration includes `npm audit`,
  `uv audit --locked`, and Trivy scans for vulnerabilities and secrets across
  all severities. None of these scans has run yet.
- The pre-existing npm moderate findings remain visible and are expected to
  fail the full audit step until resolved or formally reviewed.
- Audit-log behavior and application authorization were not changed.

## 7. Evidence integrity

- Evidence produced: local test/check results above, Compose syntax validation,
  smoke results against local services, and the checked-in CI workflow.
- Evidence still TODO(human): a GitHub CI run and scan results, plus Phase 2
  interviews, Figma, and usability results.
- Hypotheses about UX remain unvalidated.
- No GitHub run, registry push, digest, cloud deployment, or CI success is
  claimed.
- The pre-existing untracked `backend/ripple_effect.sqlite3` demo database was
  not added to the changes.

## 8. Deviations and blockers

- A first container startup failed because Windows checkout line endings made
  the shell entrypoint invalid. LF normalization and a `.gitattributes` rule
  fixed the root cause; the subsequent image build, startup, health and smoke
  checks passed.
- GitHub CI has not run yet; the approved branch push will trigger it.
- The npm audit finding was not fixed or hidden; no compatible non-breaking
  resolution was available during prior investigation.

## 9. Progress file

[`docs/progress.md`](../progress.md) records the current phase, branch
`feature/delivery-build`, base commit `4580fe9`, completed and pending work,
verification results, blockers, approvals, and the next actions.

## 10. Human review required

1. Review the resulting GitHub Actions run and existing moderate npm
   development-dependency findings; do not
   merge with an unexplained audit failure.
3. Review the uncommitted changes on `feature/delivery-build`. The current
   worktree also contains the untracked local demo database noted above.

## 11. Phase exit assessment

- Exit criteria met: **PARTIAL**.
- Evidence-backed explanation: Compose configuration, local application
  checks, Docker image builds, PostgreSQL migrations/seeding, service health,
  Nginx proxy, smoke checks, and the event-to-analysis browser journey passed.
  Remote CI and clean dependency/image scan results remain unverified.
- Recommended next: remain in Phase 8. Review the approved GitHub Actions run,
  audit and image scan findings after the feature branch is pushed. Do not
  start Phase 9.
