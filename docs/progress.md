# Ripple Effect — Project Progress

- Last updated: 2026-11-11
- Current phase: Phase 8 — Docker, Compose and CI in progress
- Current branch: `feature/delivery-build`
- Current commit: Phase 8 delivery commit (see `git log -1 --format=%h`)
- Overall status: Phase 8 is approved. Compose, the API journey, and the browser journey passed locally. GitHub run 43050682639 passed quality, the web Trivy scan, and Compose smoke; the API Trivy scan remains the only failing step. Debian API image advisories currently have no available package fixes. Phase 8 exit remains partial; Phase 2 remains partial.

## Done

- Phase 1 foundation is implemented and reported in `docs/reports/phase1-report.md`; its Docker-runtime and dependency-audit caveats remain open.
- Phase 3 data foundation is implemented and reported in `docs/reports/phase3-report.md`: tenant-aware SQLAlchemy schema, Alembic migration, membership/role helpers, scoped repositories, audited service operations, and deterministic two-organization seed.
- The Phase 3 migration creates a fresh SQLite database, is schema-drift clean, and its PostgreSQL offline DDL has the cyclic foreign key deferred until the referenced tables exist.
- Prepared Phase 2 UX documentation in `docs/ux/`: interview guide/consent reminder, anonymized notes template, hypothesis personas, journey-map template, proposed IA and task flows, low-fidelity screen requirements, Figma checklist, and usability-test script.
- Added an interactive frontend click-through flow for event → dependencies → impact inspection → scenario comparison, backed by two synthetic demo organizations and a deterministic scale sample of 10,018 entities and 30,017 relationships. All displayed analysis values are labeled mock placeholders.
- Added `docs/ux/prototype-readme.md` and updated `docs/reports/phase2-report.md`, recording scope, verification, limitations, and the partial exit assessment.
- Phase 4 API foundation is implemented and reported in `docs/reports/phase4-report.md`: tenant-authorized entity, dependency, event and trigger routes; request/response schemas; pagination; concurrency checks; audit logging; consistent error envelopes; and OpenAPI snapshot.
- Phase 4 API tests cover CRUD/lifecycle, tenant isolation, role permissions, conflicting writes, request/audit IDs, and the generated OpenAPI contract.
- Phase 5 implements the pure deterministic graph engine, bounded simple-path traversal, scoring/aggregation/confidence, safety-limit reporting, canonical snapshots and replay, tenant-scoped analysis endpoints, persistence, audit records, an Alembic migration, and updated API/OpenAPI documentation. Evidence is in `docs/reports/phase5-report.md`.
- Phase 6 replaces the synthetic-only frontend with a typed API-connected React workspace for event, trigger, entity and dependency management; analysis history, explanations, React Flow visualization and a keyboard-accessible path list. Evidence is in `docs/reports/phase6-report.md`.
- Phase 6 frontend unit/accessibility tests, lint, formatting, type-check, production build, Playwright journey and a local seeded-API browser journey passed; details and limitations are recorded in the Phase 6 report.
- Phase 7 implements tenant-scoped, versioned scenario overlays and D15 interventions; scenario runs replay immutable baseline snapshots, persist reproducible inputs, compare entity-level score changes, and never modify live records. Evidence is recorded in `docs/reports/phase7-report.md`.
- Phase 7 backend scenario isolation/authorization/audit tests, the full backend suite, frontend tests, lint/format/type-check/build, OpenAPI snapshot, and the existing Playwright journey passed. No database migration or runtime dependency was required.
- Follow-up UI refinement: applied a dark blue-purple ambient theme, a click-reactive canvas ripple that stops rendering when idle, and an expanded accessible workflow task deck. Native scrolling was retained; no animation dependency was added.
- Verified the visual refresh in-browser, including a painted click ripple that clears after its animation and a 390px mobile viewport with no page-level horizontal overflow.
- Phase 8 approved; work is isolated on `feature/delivery-build`.
- Replaced the development-server frontend image with a multi-stage static build served by unprivileged Nginx; added API proxying, SPA routing and health checks.
- Reworked the API image to install locked runtime dependencies as a non-root user and run migrations plus optional synthetic seeding before Uvicorn.
- Reworked Compose for PostgreSQL/API/web health ordering, a named database volume, loopback-only host ports, and local-only auth and seed configuration.
- Added a Compose smoke script, safe local example environment, seed output for both demo organizations, and local Compose/image-tag documentation.
- `docker compose --env-file .env.example config --quiet` passed. The live smoke script passed against the local SQLite API and Vite proxy; it did not exercise Compose or Nginx.
- After separate approval, added a workflow for frontend/backend checks, migration validation, dependency audits, Compose startup/smoke, and Trivy scans. It runs on pull requests and pushes to `feature/delivery-build`; all direct actions are pinned to commit SHAs.
- Started Docker Desktop Linux engine 29.8.2 and built both local images. PostgreSQL, API, and Nginx became healthy under isolated Compose project `ripple-phase8-check`.
- Resolved the first container startup failure: Windows CRLF line endings caused `set -eu` to fail in `/bin/sh`. Added `.gitattributes` to keep shell scripts LF-normalized and rebuilt successfully.
- The Compose smoke script, a live PostgreSQL-backed event → trigger → open → analysis API journey, and a real-browser event-to-analysis journey through Nginx all passed. API and web containers were verified non-root.
- Removed only the isolated test project's containers, network, and temporary PostgreSQL volume; Docker Desktop remains running and the two `:local` images remain built.
- Frontend runtime image now upgrades Alpine packages from the current v3.23 repositories; the rebuilt image scans clean with Trivy 0.74.0 for vulnerabilities and secrets.
- Local Trivy 0.74.0 scan of the API image still reports Debian OS advisories (47 high, 0 critical among 201 total findings); current Debian apt candidates match installed versions and Trivy reports no fixed versions.
- GitHub Actions run 43050682639 confirms frontend/backend quality and audits pass. The API scan remains failing, while the updated web scan and Compose smoke steps both passed.
- Updated CI conditions so the web scan and Compose smoke still run when Compose started successfully even if the API scan fails; the API scan remains a required failing gate. The updated behavior awaits the next branch run.

## In progress

- Human-led Phase 2 research: recruit participants, obtain appropriate consent, conduct interviews, and record actual evidence.
- Human-owned Figma prototype and task-based testing; review/adapt the React concept, create the Figma artifact, and provide genuine findings/results.
- Resolve or obtain human review for the API image's currently unpatched Debian advisories without suppressing scan results or changing severity thresholds.
- Review the Phase 8 report and latest CI results before deciding whether Phase 8 can close; do not start Phase 9 until explicitly approved.

## Ambiguity register

| ID | Open question | Recommended default | Status |
|---|---|---|---|
| A-01 | Is this the intended repository root; what is the integration branch? | Treat this folder as a new project root; preserve files; confirm before Git initialization | Resolved: confirmed; initialized `feature/phase1-foundation` |
| A-02 | Team size and PR reviewers? | Feature branches and at least one human review per PR; avoid complex Gitflow for a small team | TODO(human) |
| A-03 | Production identity provider? | Local/test adapter first; production provider undecided | TODO(human) |
| A-04 | Frontend styling system? | Tailwind proposal, subject to approval | TODO(human) |
| A-05 | Python/Node lab constraints? | Verify maintained compatible releases; observed Python 3.11.9 and Node 24.14.1 are candidates only | Runtime observed; team constraints TODO(human) |
| A-06 | Package managers? | npm + uv proposal | Resolved: npm + uv approved; uv 0.13.7 installed, Scripts directory not on PATH by default |
| A-07 | Is Azure ACR/ACI available and budget-approved? | Local-first; human-operated cloud runbooks only | TODO(human) |
| A-08 | Is Docker Hub also required? | ACR remains target; use Docker Hub only if course requires | TODO(human) |
| A-09 | Which UX participants are available? | Voluntary students/coordinators with consent; hypotheses remain unvalidated | TODO(human) |
| A-10 | Is real institutional data needed? | Synthetic data only | Accepted default |
| A-11 | Should Jenkins/Kubernetes be pursued? | Defer until MUST criteria and ACI milestone are complete | Accepted default |
| A-12 | Course report/presentation format? | Follow official rubric if supplied; otherwise Section 15 | TODO(human) |

## Next — ordered backlog and acceptance criteria

| Order | Work item | Acceptance criteria |
|---|---|---|
| In progress | Phase 8 delivery | Local Compose is reproducible and approved CI checks pass; image/build evidence is genuine |
| Parallel human work | Complete Phase 2 research and Figma work | Human-owned clickable prototype covers event creation → analysis → impact inspection → scenario → comparison; genuine findings and design decisions documented; no fabricated evidence |
| Later | Phase 9 cloud | Human-approved ACR/ACI deployment uses recorded immutable digest; health, rollback and cleanup are verified |
| Later | Phase 11 release hardening | Security, tests, accessibility, docs and evidence are reviewed; unmet criteria/limitations are explicit |
| Optional | Phase 10 Jenkins/Kubernetes | Only after baseline and explicit approval; optional work does not delay required delivery |

## Blockers

- The latest CI run is [43050682639](https://github.com/tejasr09/cdd_final_proj/actions/runs/43050682639) on commit `5186ab7`: quality, web image scan, and Compose smoke passed; the API image scan failed.
- `npm audit` now passes with zero findings after the `minimatch` override to 11.0.1; backend `uv audit --locked` also passed in the latest CI quality job.
- The current Debian 13 API image scan still reports 201 OS findings (15 unknown, 65 low, 74 medium, 47 high, 0 critical) and no secrets. The high findings have no fixed versions in the current Trivy database; `apt-cache policy` showed installed versions equal to repository candidates.
- A comparison against the unupgraded Debian 12 base had more findings, including critical findings; do not change to that older base to evade the current advisories.
- Production authentication provider remains intentionally undecided. The local/test membership and role adapter exists; production authentication is not implemented.
- Human interviews, consent, actual UX findings, Figma prototype, and usability results do not exist yet; Phase 2 is partial until supplied and reviewed.
- The former synthetic click-through remains documented as historical; the active frontend uses API data. Phase 2 interview, Figma and usability evidence remains absent.
- A fresh PostgreSQL Compose database was migrated and seeded during Phase 8 startup. Production PostgreSQL and concurrent tenant/scenario behavior remain unverified.
- Analysis execution is synchronous; PostgreSQL concurrent-insert snapshot consistency has not been stress-tested.
- Scenario behavior is verified with SQLite API tests; live PostgreSQL concurrent scenario updates remain unverified.
- Cloud resources remain future-phase/human work. Remote CI has run, but Phase 8 exit criteria are not met until the API scan is resolved or reviewed.
- The root `agent-brief.md` points to `docs/agent-brief.md`, which is absent. Phase 4 requirements were taken from the available root continuation brief; neither brief was rewritten.

## Verification

| Date | Command/check | Result | Notes |
|---|---|---|---|
| 2026-11-07 | Read both briefs and existing docs | PASS | Combined specification reviewed |
| 2026-11-07 | Workspace inventory | PASS | No application source/manifests found |
| 2026-11-07 | Git status/branch/log | NOT RUN | Git reported not a repository |
| 2026-11-07 | Toolchain version inspection | PASS | Python 3.11.9; Node 24.14.1; npm 11.11.0; Docker 29.8.2; Git 2.53.0.windows.2; uv unavailable |
| 2026-11-07 | ADR structure validation | PASS | ADR-001 through ADR-031 present with required sections |
| 2026-11-07 | Frontend lint/typecheck/format/build | PASS | Vite production build succeeded |
| 2026-11-07 | Backend tests/lint/format | PASS | 2 pytest cases passed; Ruff clean |
| 2026-11-07 | API live health/OpenAPI smoke | PASS | Liveness, readiness, and OpenAPI responded |
| 2026-11-07 | Browser UI smoke | PASS | Integrated browser loaded page and exposed semantic headings/notice |
| 2026-11-07 | Docker Compose config | PASS | Config parsed; daemon not available for actual startup |
| 2026-11-07 | npm audit, production dependencies | PASS | 0 vulnerabilities |
| 2026-11-07 | npm audit, all frontend dependencies | FAIL | 10 moderate development dependency findings via minimatch; see report |
| 2026-11-07 | `uv audit --locked` | PASS | OSV lookup: no known vulnerabilities/adverse statuses in 21 packages |
| 2026-11-07 | Docker daemon and image startup | NOT RUN | Docker Desktop Linux engine pipe unavailable |
| 2026-11-07 | Phase 2 UX documentation review | PASS | Confirmed requested agent-preparation deliverables are present; docs-only review, no UX validation claimed |
| 2026-11-07 | `npm run build` in `frontend` | PASS | TypeScript project build and Vite production build succeeded with the UX prototype |
| 2026-11-07 | `npm run lint` in `frontend` | PASS | ESLint clean |
| 2026-11-07 | `npx prettier --check src\App.tsx src\demoData.ts src\styles.css` in `frontend` | PASS | Changed frontend files formatted |
| 2026-11-07 | Browser flow: event save → dependency search → impact detail → mitigation comparison | PASS | Verified synthetic campus example, 3 dependency matches, and temporary mock comparison update |
| 2026-11-07 | Browser flow: transport organization switch | PASS | Verified separate synthetic example, 7 fixture dependencies plus generated data, and local scenario state reset |
| 2026-11-07 | Browser viewport check at 390px | PASS | Main heading visible; body had no horizontal overflow |
| 2026-11-07 | UX interviews, human-owned Figma prototype, task-based usability testing | NOT RUN | Human-led Phase 2 work; no participants, Figma file, or results supplied |
| 2026-11-07 | `uv run --locked pytest` in `backend` | PASS | 16 tests passed, including migrated-schema tenant references and D13 event lifecycle statuses |
| 2026-11-07 | `uv run --locked ruff check app tests` in `backend` | PASS | All checks passed |
| 2026-11-07 | `uv run --locked ruff format --check app tests migrations/versions/b4fceea3f1e2_initial_data_foundation.py` | PASS | All 12 checked Python files already formatted |
| 2026-11-07 | Fresh SQLite `alembic upgrade head`, then `alembic check` | PASS | Migration applied; no new schema operations detected |
| 2026-11-07 | PostgreSQL offline `alembic upgrade --sql head` | PASS | Generated DDL places `fk_scenarios_baseline_run_tenant` after `impact_runs` creation; no live server was contacted |
| 2026-11-07 | `uv run --locked python -m scripts.export_openapi` in `backend` | PASS | Regenerated `docs/api/openapi.json` from the application |
| 2026-11-07 | `uv run --locked pytest` in `backend` | PASS | 22 tests passed, including API, health, tenancy, migration, audit, role and OpenAPI snapshot checks |
| 2026-11-07 | `uv run --locked ruff check app tests scripts` in `backend` | PASS | All checks passed |
| 2026-11-07 | `uv run --locked ruff format --check app tests scripts` in `backend` | PASS | All 15 checked Python files already formatted |
| 2026-11-07 | Commit and worktree check | PASS | Phase 4 implementation committed as `c93eb32` on `feature/api-foundation`; worktree clean |
| 2026-11-07 | Live PostgreSQL, Docker/Compose, production authentication, secret scan | NOT RUN | Not available or not authorized/in scope for Phase 4; no live/cloud evidence claimed |
| 2026-11-07 | `uv run --locked pytest` in `backend` | PASS | 86 tests passed, including engine, seeded laboratory/transport API analysis, snapshot replay, migration, tenancy and OpenAPI contract checks |
| 2026-11-07 | `uv run --locked ruff check app tests scripts migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py` | PASS | All checks passed |
| 2026-11-07 | `uv run --locked ruff format --check app tests scripts migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py` | PASS | 19 files already formatted |
| 2026-11-07 | Broad Ruff check including all migrations | FAIL | 12 pre-existing findings in `b4fceea3f1e2_initial_data_foundation.py`; historical migration left unchanged; targeted final check passes |
| 2026-11-07 | Pylance diagnostics for changed application, schema, engine, API and migration files | PASS | No errors in the changed files |
| 2026-11-07 | Fresh SQLite Alembic upgrade, downgrade to Phase 3 revision, re-upgrade and `alembic check` | PASS | Round-trip succeeded; no schema drift detected |
| 2026-11-07 | `uv run --locked python -m scripts.export_openapi` in `backend` | PASS | Regenerated the checked-in API contract; snapshot comparison passes in tests |
| 2026-11-07 | `uv audit --locked` in `backend` | PASS | No known vulnerabilities or adverse statuses in 33 packages |
| 2026-11-07 | Synthetic engine benchmark, three runs per fixture | PASS | Median 0.302038 s for a 5,000-node/4,999-edge chain; 1.131815 s for a 120-node/7,140-edge DAG, which reached the 10,000-path ceiling. Local measurements only; no performance SLO was asserted. |
| 2026-11-07 | Live PostgreSQL, Docker/Compose, production authentication, secret scan | NOT RUN | Not available or outside Phase 5 scope; no live/cloud evidence claimed |
| 2026-11-07 | `npm test` in `frontend` | PASS | 11 tests passed across 3 files, including API, component, workflow and accessibility coverage |
| 2026-11-07 | `npm run lint` in `frontend` | PASS | ESLint clean |
| 2026-11-07 | `npm run format:check` in `frontend` | PASS | Prettier clean; generated Playwright results are excluded and ignored |
| 2026-11-07 | `npm run typecheck` in `frontend` | PASS | TypeScript project check passed |
| 2026-11-07 | `npm run build` in `frontend` | PASS | TypeScript build and Vite production bundle succeeded |
| 2026-11-07 | `$env:PLAYWRIGHT_USE_CHROME='1'; npm run test:e2e` in `frontend` | PASS | 1 Playwright event-to-analysis journey passed using installed Chrome |
| 2026-11-07 | Local seeded-API browser journey | PASS | Chrome connected through Vite proxy, created an event, added a trigger, opened it, ran analysis and inspected a source-to-target path; no page errors |
| 2026-11-07 | Initial frontend test/format iterations | FAIL, resolved | New test expectations were aligned to updated event timestamps and independent relationship labels; formatter initially inspected generated Playwright output, now excluded |
| 2026-11-07 | Frontend dependency/container/secret scan | NOT RUN | No Phase 6 scan run; inherited development-dependency audit finding remains open. No containers or secrets were introduced |
| 2026-11-07 | `uv run --locked pytest tests\test_api.py -k scenario -q` in `backend` | PASS | 3 scenario tests passed, 9 deselected |
| 2026-11-07 | `uv run --locked pytest` in `backend` | PASS | 88 tests passed |
| 2026-11-07 | `uv run --locked ruff check app tests scripts` and `uv run --locked ruff format --check app tests scripts` in `backend` | PASS | Ruff clean; 19 files already formatted |
| 2026-11-07 | `uv run --locked python -m scripts.export_openapi` in `backend` | PASS | Regenerated scenario endpoints and schemas in the reviewed OpenAPI snapshot; snapshot equality is tested |
| 2026-11-07 | `npm test -- --run --pool=forks --maxWorkers=1` in `frontend` | PASS | 12 tests passed across 3 files |
| 2026-11-07 | `npm run lint`, `npm run format:check`, `npm run typecheck`, `npm run build` in `frontend` | PASS | ESLint, Prettier, TypeScript, and Vite production build succeeded |
| 2026-11-07 | `$env:PLAYWRIGHT_USE_CHROME='1'; npm run test:e2e` in `frontend` | PASS | 1 event-to-analysis browser journey passed |
| 2026-11-07 | Initial frontend suite under default per-test timeout | FAIL, resolved | Multi-step UI tests exceeded 5 seconds; extended two tests to 10 seconds, and the final full frontend suite passed |
| 2026-11-07 | Live PostgreSQL, Docker/Compose, dependency scan, secret scan | NOT RUN | Not performed in Phase 7; no migration or runtime dependency was added |
| 2026-11-08 | `npm test -- --run --pool=forks --maxWorkers=1` in `frontend` | PASS | 12 tests passed across 3 files after task-deck assertions were added |
| 2026-11-08 | Frontend lint, format, typecheck, production build | PASS | ESLint, Prettier, TypeScript, and Vite production build succeeded after the visual refresh |
| 2026-11-08 | `$env:PLAYWRIGHT_USE_CHROME='1'; npm run test:e2e` in `frontend` | PASS | 1 browser journey passed |
| 2026-11-08 | Canvas ripple and mobile layout browser check | PASS | Click rendered 2,156 canvas pixels at 140 ms; canvas cleared after 1.2 s. 390px viewport had no page-level horizontal overflow |
| 2026-11-08 | `docker compose --env-file .env.example config --quiet` | PASS | Compose configuration parsed; service list was db, api, web |
| 2026-11-08 | `python backend\scripts\smoke_compose.py` | PASS | API readiness, Vite-served app and Vite-to-API proxy passed with local SQLite; Compose/Nginx/PostgreSQL were not exercised |
| 2026-11-08 | `backend\.venv\Scripts\python.exe -m pytest` | PASS | 88 backend tests passed |
| 2026-11-08 | Backend Ruff check and format check | PASS | `app`, `tests`, and `scripts` clean; 20 files formatted |
| 2026-11-08 | Frontend tests, lint, format, type-check and production build | PASS | 12 tests passed; all other listed checks succeeded |
| 2026-11-08 | Local SQLite `alembic check` | PASS | No new upgrade operations detected |
| 2026-11-08 | Docker image build and Compose container startup | NOT RUN | Docker Desktop Linux engine unavailable at that time |
| 2026-11-08 | Docker engine retry after availability confirmation | FAIL | Context is `desktop-linux`, but the Docker API pipe is absent; no engine process was detected |
| 2026-11-08 | `.github/workflows/ci.yml` | ADDED | Approved locally with SHA-pinned actions, least-privilege permissions, checks, audits, Compose build/smoke and Trivy scans |
| 2026-11-08 | GitHub Actions CI run | NOT RUN | No remote push/PR had been approved yet; the full npm audit is expected to expose the existing moderate findings |
| 2026-11-09 | Docker Desktop engine | PASS | Started Docker Desktop; Linux engine version 29.8.2 became available |
| 2026-11-09 | `docker compose --project-name ripple-phase8-check --env-file .env.example up --build --detach --wait --wait-timeout 240` | PASS | Built both images; PostgreSQL, API, and Nginx all reached healthy state |
| 2026-11-09 | First isolated Compose startup | FAIL, resolved | CRLF line endings in `backend/docker-entrypoint.sh` made `/bin/sh` reject `set -eu`; normalized to LF and added `.gitattributes` rule |
| 2026-11-09 | `python backend\scripts\smoke_compose.py` against Compose | PASS | API readiness, Nginx web response, and Nginx-to-API proxy passed |
| 2026-11-09 | Compose API event-to-analysis journey | PASS | Created synthetic event, attached trigger, opened event, completed analysis; 8 results returned |
| 2026-11-09 | Chrome browser journey through Compose | PASS | Connected via Nginx, created event, added trigger, opened it, ran analysis; no page errors |
| 2026-11-09 | Container user/health inspection | PASS | API `appuser` and web `nginx` users; API, web and PostgreSQL healthy |
| 2026-11-09 | Isolated Compose cleanup | PASS | Removed test containers/network and only its temporary PostgreSQL volume; local image tags retained |
| 2026-11-09 | Workflow branch-push trigger | ADDED | User approved CI on pushes to `feature/delivery-build` as well as pull requests |
| 2026-11-09 | GitHub Actions run 42583121491 | FAIL | Initial run failed frontend audit and API image scan; audit finding was later fixed |
| 2026-11-09 | GitHub Actions run 42640812502 on `3e6926d` | PARTIAL | Quality job passed. Compose build/start passed; API Trivy scan failed, so web scan and smoke step were skipped |
| 2026-11-11 | `npm audit` and `uv audit --locked` in latest CI quality job | PASS | Frontend audit reports zero findings after the `minimatch` 11.0.1 override; backend audit passed |
| 2026-11-11 | Trivy 0.74.0 API image scan (`vuln,secret`, all severities) | FAIL | 201 Debian OS findings: 15 unknown, 65 low, 74 medium, 47 high, 0 critical; no secrets or fixed versions reported |
| 2026-11-11 | Debian package candidate check in API image | BLOCKED | Current repository candidates equal installed versions for flagged packages; no security update is currently available |
| 2026-11-11 | Trivy 0.74.0 web image scan before Alpine update | FAIL | 238 Alpine findings, including 1 critical and 55 high; Alpine repositories offered patched versions |
| 2026-11-11 | Frontend image rebuild with `apk update && apk upgrade` and Trivy rescan | PASS | Updated to current Alpine packages; zero vulnerability and secret findings |
| 2026-11-11 | Isolated Compose rebuild/start and smoke with validation-only port overrides | PASS | PostgreSQL, API and web healthy; API readiness, served app and Nginx-to-API proxy passed; API remained `appuser`, web UID 101 |
| 2026-11-11 | Docker engine | PASS | Docker Desktop Linux engine 29.9.2 |
| 2026-11-11 | `prettier --check .github/workflows/ci.yml` | PASS | Workflow YAML formatting and parsing passed after making web scan and smoke independent of API scan failure |
| 2026-11-11 | GitHub Actions run [43050682639](https://github.com/tejasr09/cdd_final_proj/actions/runs/43050682639) on `5186ab7` | PARTIAL | Quality passed; API Trivy scan failed; web scan and Compose smoke passed, confirming the updated step conditions |

## Decisions and ADRs

- Accepted: ADR-001 through ADR-031; user approved proposed ADRs for Phase 1.
- Runtime identity provider remains unselected, as specified by the auth adapter decision.
- npm + uv package manager selection accepted; uv 0.13.7 installed in the user Python tool directory.
- Detailed phase findings: `docs/reports/phase-0-report.md`.
- Phase 1 evidence: `docs/reports/phase1-report.md`.
- Phase 2 agent-preparation scope approved; human-led research and Figma ownership remain with the human.
- Human selected generated synthetic data and explicitly approved Phase 3. The continuation brief permits Phase 2 to run in parallel with Phases 3–5; the human later asked to defer Figma/research and continue functionality. Phase 2 remains partial but did not block the approved Phase 3 work.
- The human explicitly approved Phase 4. Phase 4 changes are isolated on `feature/api-foundation`; stop after this report until Phase 5 is explicitly approved.
- The human explicitly approved Phase 5 and NetworkX. Phase 5 changes are isolated on `feature/engine-ripple`; stop after this report until Phase 6 is explicitly approved.
- The human explicitly approved Phase 6 and selected React Flow, approving `@xyflow/react` as the UI runtime dependency. Phase 6 changes are isolated on `feature/frontend-integration`; stop after this report until Phase 7 is explicitly approved.
- The human explicitly approved Phase 7 and subsequently approved Phase 8. Phase 7 changes remain on `feature/scenario-simulation`; Phase 8 work is isolated on `feature/delivery-build`. Stop after the Phase 8 report.
- API updates and lifecycle changes require `expected_updated_at`; supported databases use row locks where available. Database integrity conflicts return the standard 409 error envelope.
- `httpx==0.28.1` was added to the backend development dependency group for ASGI integration tests; it is not a runtime dependency.
- PostgreSQL remains the authoritative store; SQLite is used for local development/tests. Phase 8 verified migration and seed startup against a local Compose PostgreSQL service, not a production deployment.
- Phase 2 evidence and limitations: `docs/reports/phase2-report.md`.
- Phase 3 implementation evidence and limitations: `docs/reports/phase3-report.md`.
- Phase 4 implementation evidence and limitations: `docs/reports/phase4-report.md`.
- Phase 5 implementation evidence and limitations: `docs/reports/phase5-report.md`.
- Phase 6 implementation evidence and limitations: `docs/reports/phase6-report.md`.
- Phase 7 implementation evidence and limitations: `docs/reports/phase7-report.md`.

## Risk register

| Risk | Impact | Mitigation | Owner/status |
|---|---|---|---|
| API image OS advisories | CI cannot pass the full-severity API image scan | Keep all severities enabled; Debian 13 repository currently offers no patched candidate for flagged packages; re-scan when fixes land or obtain review for a vetted base-image change | Engineering, open |
| Development dependency audit | npm/uv dependency advisories | `npm audit` and `uv audit --locked` pass in latest CI; retain checks | Engineering, verified |
| Docker verification | Local Compose build/start acceptance | Docker Desktop 29.9.2; images, health, proxy, smoke and primary journey verified locally | Engineering, verified |
| Production auth provider undecided | Cannot configure production identity safely | Keep adapter boundary; select provider and deployment config with human approval | TODO(human), planned |
| Azure subscription/cost/registry needs unknown | Deployment plan may be unusable or incur cost | Human confirms availability and budget; no cloud actions by agent | TODO(human), open |
| UX evidence unavailable | Design could be mistaken for validated research | Keep personas as hypotheses and mark research TODO(human) | Team, open |
| Dependency path explosion | Resource exhaustion or incomplete analysis | Deterministic node/path ceilings and visible incomplete status are implemented and tested; synchronous execution and concurrency still need production-scale review | Engineering, active |
| Tenant leakage or scenario mutation | Cross-organization disclosure or live-data corruption | Scoped access and API isolation/live-record tests pass; live PostgreSQL verification remains open | Engineering, monitoring |

## Human actions pending

- Conduct and document Phase 2 interviews with suitable participants, appropriate consent, anonymized notes, and evidence-backed findings.
- Create/own the clickable Figma prototype, conduct task-based tests, and provide actual frames/results for review.
- Complete Phase 2 human research/Figma/usability deliverables when ready; Phase 2 remains partial.
- Review the remaining API image advisories and approve any future base-image or runtime change if needed.

## Evidence index

- `docs/reports/phase-0-report.md`
- `docs/reports/phase3-report.md`
- `docs/reports/phase4-report.md`, `docs/reports/phase5-report.md`, and `docs/reports/phase6-report.md`
- `docs/reports/phase7-report.md`
- `docs/reports/phase8-report.md` (partial exit assessment; latest CI and local image scan results recorded)
- `docs/api/README.md` and `docs/api/openapi.json`
- `docs/adr/`
- `.github/workflows/ci.yml` (approved workflow; run 43050682639 quality, web scan and smoke passed; API scan failed)
- `docs/viva-notes.md` (implementation status and evidence updated through Phase 8 work)
- `docs/ux/` contains Phase 2 preparation documents and the historical synthetic React concept; no interview, human-owned Figma, or usability-test evidence exists.
- Phase 1 code/test/API evidence is recorded in `docs/reports/phase1-report.md`; no CI, cloud, or benchmark evidence is claimed.

## Session handoff

- Last completed task: reviewed GitHub CI and Trivy findings; updated the frontend image and verified local Compose and scans on `feature/delivery-build`.
- Exact next task: human review of the unresolved API OS advisories and the Phase 8 partial exit report. Do not start Phase 9 without explicit approval.
- Files to read first: both root-level briefs, this file, `README.md`, and `docs/architecture/container-view.md`.
- Latest reviewed CI run: [43050682639](https://github.com/tejasr09/cdd_final_proj/actions/runs/43050682639). Quality, web scan and smoke passed; the API Trivy scan remains unclean.
- Approval needed: review and disposition of remaining API image findings. The branch push and CI trigger are already approved; do not merge or deploy.

## CI follow-up — 2026-11-11

- GitHub CI found 10 moderate `minimatch` issues. `npm audit fix` could not resolve them; the forced ESLint downgrade was discarded because it introduced incompatible tooling peers.
- Added an npm override for patched `minimatch` 11.0.1. `npm audit` passes with zero findings, and `npm ls minimatch --all` confirms ESLint and TypeScript ESLint resolve to 11.0.1.
- The first Trivy setup failed downloading v0.70.0 before scanning. Both image steps now explicitly request v0.74.0.
- Frontend lint, format, type-check, 12 tests, production build and audit pass with the updated lockfile. Backend sources are unchanged.
- GitHub run 42640812502 on commit `3e6926d` passed quality and Compose startup but failed the API Trivy step, skipping web scan and smoke.
- Follow-up run 43050682639 on commit `5186ab7` passed quality, web scan, and Compose smoke; only the API scan failed. This verified the workflow continuation conditions.
- Reproduced the configured Trivy 0.74.0 scan locally. The API image has 201 Debian OS advisories (47 high, 0 critical); no secrets or fixed versions were reported. Current Debian apt candidates match the installed packages, so another apt upgrade cannot resolve them today.
- The original web image had 238 Alpine findings (1 critical, 55 high). Alpine v3.23 repositories offered patched packages; the frontend Dockerfile now updates packages during the final image stage. The rebuilt web image scans with zero vulnerability and secret findings.
- Verified the updated web image with an isolated Compose rebuild/start and smoke checks on temporary host ports because a local Vite demo already occupies port 5173. All services became healthy; API readiness, web response and Nginx-to-API proxy passed; the stack and temporary database volume were removed.
- The API Dockerfile continues to upgrade available Debian packages and remove unused base pip/setuptools/wheel. This reduced the previously reported exposure but did not clear the remaining unpatched Debian findings. Do not suppress advisories or lower scan thresholds.
- Updated CI step conditions preserve the API failure gate but let the web scan and Compose smoke run when Compose startup succeeded; GitHub has not run this workflow revision yet.
- The npm audit issue is resolved by the 11.0.1 override; do not retain the older progress note that it remains open.
