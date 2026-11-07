# Phase 7 Report — Scenario simulation and comparison

## 1. Objective

Implement organization-scoped, versioned what-if scenarios based on immutable
live-analysis snapshots. Provide event and intervention overlays, reproducible
scenario runs and entity-level comparisons without mutating live operational
records.

## 2. Work completed

- Added scenario request/response schemas and REST endpoints for listing,
  creation, retrieval, metadata/event-overlay updates, D15 interventions,
  scenario execution, comparison, and archive.
- Added `scenario_id` filtering to analysis-run history.
- Implemented tenant-scoped scenario service logic, optimistic version checks,
  audit events, immutable baseline replay, intervention overlays, persisted
  scenario snapshots, and baseline-versus-scenario comparisons.
- Supported node mitigation, dependency weight override, dependency
  deactivation, and hypothetical dependencies marked `draft`.
- Persisted hypothetical path provenance without assigning a hypothetical
  dependency ID to the live-dependency foreign key.
- Integrated a Scenarios section into the frontend with creation, event
  overlays, all four intervention forms, run history, comparisons, assumptions,
  error/loading feedback, and archival.
- Added backend tests for tenant and role boundaries, overlays, all D15 action
  types, reproducibility, comparison, audit events, archive, and live-record
  isolation; added a frontend scenario-workspace smoke test and updated run
  fixtures.
- Regenerated the OpenAPI snapshot and updated API, README, viva, ADR-014, and
  progress documentation.
- No migration was required: the scenario and overlay tables and the scenario
  run foreign key already existed in the schema.

## 3. Decisions

- Followed accepted ADR-014 / D14: scenarios are isolated overlays; no apply-to-live
  operation was added. Archival retains scenario history.
- Followed D15: interventions are explicit assumptions; comparison effects are
  derived from results, not entered by users.
- Reused the existing `analysis:run` and `event:read` permissions; role or
  tenant-isolation policy was not changed.
- No new ADR was needed. Retention details and final human acceptance of
  ADR-014 remain for human review.

## 4. Verification performed

| Command/check | Result | Evidence |
|---|---|---|
| `uv run --locked pytest tests\test_api.py -k scenario -q` (from `backend`) | PASS | 3 passed, 9 deselected |
| `uv run --locked pytest` (from `backend`) | PASS | 88 tests passed |
| `uv run --locked ruff check app tests scripts` (from `backend`) | PASS | All checks passed |
| `uv run --locked ruff format --check app tests scripts` (from `backend`) | PASS | 19 files already formatted |
| `uv run --locked python -m scripts.export_openapi` (from `backend`) | PASS | Updated `docs/api/openapi.json`; exact snapshot comparison is included in the passing backend suite |
| `npm test -- --run --pool=forks --maxWorkers=1` (from `frontend`) | PASS | 12 tests passed across 3 files |
| `npm run lint`, `npm run format:check`, `npm run typecheck`, `npm run build` (from `frontend`) | PASS | ESLint, Prettier, TypeScript, and Vite production build succeeded |
| `$env:PLAYWRIGHT_USE_CHROME='1'; npm run test:e2e` (from `frontend`) | PASS | 1 event-to-analysis browser journey passed |
| `git diff --check` | PASS | No whitespace errors before final report/progress updates |
| Live PostgreSQL, Docker/Compose, dependency scan, secret scan | NOT RUN | Not performed in Phase 7; no migration or runtime dependency was added |

## 5. Test results

- Tests run: focused scenario API tests, full backend suite, full frontend
  Vitest suite, and the existing Playwright event-to-analysis journey.
- Passed: 3 focused scenario tests; 88 backend tests; 12 frontend tests; 1
  Playwright test.
- Failed: an early full frontend run hit the default five-second timeout in
  multi-step UI tests under load. Two long-running interaction tests now use a
  10-second test timeout; the final suite passed.
- Skipped: none reported by the final test runs.
- Coverage: not measured.
- Known gaps: the browser journey does not yet execute the complete scenario
  flow; live PostgreSQL concurrency and deployment behavior are unverified.

## 6. Security and data integrity

- Tenant-isolation checks: scenario reads and writes are organization-scoped;
  cross-organization access is covered by API tests.
- Authorization checks: tests cover read and analysis permissions; production
  identity remains outside scope.
- Secret scan: NOT RUN.
- Dependency/container scan: NOT RUN; no runtime dependency or container
  configuration changed.
- Audit-log checks: tests verify scenario creation, event updates,
  interventions, and archival are audited.
- Unresolved concern: live PostgreSQL row-lock and concurrent scenario
  consistency behavior has not been tested. Scenario-to-live mutation is not
  supported.

## 7. Evidence integrity

- Evidence produced: passing automated tests, lint/format/type/build checks,
  Playwright result, generated OpenAPI snapshot, and this report.
- Evidence still TODO(human): production PostgreSQL verification, Docker/CI
  checks, human UX interviews, Figma prototype, and usability testing.
- Hypotheses remain unvalidated: all product personas and UX assumptions.
- No probability, guaranteed effect, human research, cloud, benchmark, or
  security-scan claims are made.

## 8. Deviations and blockers

- No material deviation from the Phase 7 brief.
- No migration was added because the required scenario schema was already
  present.
- No runtime dependency, GitHub Action, remote operation, cloud resource, or
  authentication/authorization policy change was introduced.
- Blockers: live PostgreSQL and Docker are unavailable/unverified; human-led
  Phase 2 work remains incomplete.

## 9. Progress file

`docs/progress.md` records Phase 7 completion, verification results, the
scenario branch, outstanding limitations, decisions, and the human review gate.

## 10. Human review required

- Review scenario overlay/version behavior, audit records, D15 payload semantics,
  comparison output and tenant-isolation tests.
- Review the regenerated OpenAPI contract and frontend scenario workspace.
- Decide/confirm scenario-history retention policy and acknowledge that
  applying scenarios to live records is out of scope.
- Explicitly approve Phase 8 before work begins.

## 11. Phase exit assessment

- Exit criteria met: YES.
- Evidence-backed explanation: scenario runs replay the saved baseline plus
  versioned overlays; the comparison API reports entity-level changes and
  estimated deltas; the full backend suite includes tenant/authorization,
  reproducibility, audit, hypothetical-dependency and live-record-isolation
  checks. Frontend, build, and browser checks passed.
- Recommended next phase: Phase 8 — Docker, Compose and CI, after human review
  and explicit approval.

STOP HERE. Do not begin Phase 8 until the human explicitly approves.
