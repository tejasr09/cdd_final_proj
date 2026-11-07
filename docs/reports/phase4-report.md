# Phase 4 Report — API foundation

## 1. Objective

Implement the approved core event, entity, dependency and event-trigger API,
including validation, tenant authorization, lifecycle rules, pagination,
consistent errors, audit logging, an OpenAPI snapshot and integration tests.

## 2. Work completed

- Added typed request and response schemas in `backend/app/schemas.py`.
- Added tenant-scoped entity, dependency, event and trigger routes in
  `backend/app/api.py`, including list filters, bounded pagination and stable
  ordering.
- Added update concurrency checks using `expected_updated_at`; rows are locked
  where the database supports row locks.
- Added request-ID middleware and consistent validation, authorization,
  not-found, conflict and internal-error envelopes in `backend/app/main.py`.
  Database integrity conflicts return HTTP 409, including conflicts raised
  during service-layer flushes.
- Connected state changes to existing audit services and tested request-ID
  correlation.
- Added `backend/tests/test_api.py` and updated health route contract tests to
  inspect published OpenAPI paths rather than framework-internal route objects.
- Added the pinned `httpx==0.28.1` development dependency for ASGI integration
  tests; no runtime dependency was added.
- Generated `docs/api/openapi.json` and documented the API and local
  authentication contract in `docs/api/README.md` and `README.md`.
- Updated `docs/progress.md` for the Phase 4 boundary.

No database schema or migration changes were made in this phase.

## 3. Decisions

- The human explicitly approved Phase 4. Existing accepted ADRs remain in
  effect; no new ADR was added.
- Local identity headers remain limited to development/test and do not provide
  production authentication.
- Mutation requests require the latest `expected_updated_at` value and return
  409 on stale updates.
- The root `agent-brief.md` refers to `docs/agent-brief.md`, which is absent.
  The available continuation brief contains the Phase 4 requirements and was
  followed; neither brief was silently rewritten.

## 4. Verification performed

The `uv` executable was invoked through
`$env:APPDATA\Python\Python311\Scripts\uv.exe` because its Scripts directory is
not on the tool-shell PATH.

| Command/check | Result | Evidence |
|---|---|---|
| `uv run --locked python -m scripts.export_openapi` (from `backend`) | PASS | Regenerated `docs/api/openapi.json` |
| `uv run --locked pytest` (from `backend`) | PASS | 22 tests passed |
| `uv run --locked ruff check app tests scripts` (from `backend`) | PASS | All checks passed |
| `uv run --locked ruff format --check app tests scripts` (from `backend`) | PASS | 15 files already formatted |
| OpenAPI snapshot comparison | PASS | Included in the API test suite |
| Committed revision and worktree check | PASS | Tests ran against the final implementation committed as `c93eb32` on `feature/api-foundation`; worktree was clean |
| Live PostgreSQL migration/API check | NOT RUN | No live PostgreSQL server was available; this phase made no schema changes |
| Docker/Compose startup | NOT RUN | Docker daemon unavailable; Compose orchestration is a later phase |

## 5. Test results

- Tests run: complete backend suite.
- Passed: 22.
- Failed: 0.
- Skipped: 0.
- Coverage: not measured.
- Known gaps: no live PostgreSQL concurrency test; SQLite does not exercise
  database row locks. Integrity-error response mapping is tested with a
  simulated SQLAlchemy integrity exception, not a concurrent database race.

## 6. Security and data integrity

- Tenant isolation: a member of the other seeded organization receives 404 for
  an organization-owned entity; cross-organization dependency and trigger
  references are rejected.
- Authorization: tests cover denied analyst writes, denied coordinator
  reopening, and administrator reopening of resolved and archived events.
- Audit logging: tested for entity create/update/archive, dependency
  create/update/deactivate, event creation/status changes, and trigger
  creation/deletion. A supplied request ID is retained on the audit record.
- Conflict handling: stale updates and duplicate/conflicting operations
  return 409; request inputs are not included in validation error details.
- Secret scan, dependency scan and container scan: not run for this phase.
- Unresolved concern: production identity/authentication remains unconfigured;
  live PostgreSQL tenant and locking behavior remains unverified.

## 7. Evidence integrity

- Evidence produced: backend tests, lint/format results, the generated OpenAPI
  snapshot, API documentation and this report.
- Evidence still TODO(human): Phase 2 participant interviews, consented
  research, human-owned Figma prototype and usability findings.
- Hypotheses about UX remain unvalidated.
- No production authentication, live PostgreSQL, Docker, cloud deployment,
  performance benchmark or analysis-engine result is claimed.

## 8. Deviations and blockers

- The route introspection tests were changed to use OpenAPI because the pinned
  FastAPI version exposes an internal deferred router object without a `.path`
  attribute. This preserves the health route contract check against the
  published interface.
- `httpx` is a development-only dependency used by the ASGI integration tests.
- The root brief's reference to missing `docs/agent-brief.md` is recorded in
  `docs/progress.md`; the continuation brief supplied the Phase 4 scope.
- Blockers: production auth selection, live PostgreSQL verification and
  Docker-based startup remain outstanding.
- Approval status: Phase 4 was explicitly approved; Phase 5 has not been
  approved.

## 9. Progress file

`docs/progress.md` now records completed work, remaining Phase 2 human work,
Phase 5 as the next gated phase, blockers, verification results, decisions,
evidence links, the current branch and the phase boundary.

## 10. Human review required

- Review the API contract and OpenAPI snapshot, including permissions,
  lifecycle transitions, pagination, error shapes and optimistic concurrency.
- Confirm whether the documented local-auth workflow is appropriate for the
  intended development environment; select production authentication later.
- Review the report and explicitly approve Phase 5 before engine implementation
  begins.

## 11. Phase exit assessment

- Exit criteria met: **YES**.
- Evidence-backed explanation: entity, dependency, event and trigger workflows
  pass integration tests; validation rejects self-loops, duplicates and
  cross-tenant references; role restrictions, audit behavior, pagination,
  errors and the OpenAPI contract are tested.
- Recommended next phase: Phase 5 — Ripple engine, only after explicit human
  approval.

**STOP HERE. Do not begin Phase 5 until the human explicitly approves.**
