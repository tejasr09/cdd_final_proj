# Phase 5 Report — Ripple engine

## 1. Objective

Implement the approved deterministic and explainable graph-analysis engine,
including input validation, temporal eligibility, bounded paths, scoring,
aggregation, confidence, immutable snapshots, API persistence, audit records,
and visible safety-limit outcomes. Stop at the Phase 5 boundary.

## 2. Work completed

- Added the FastAPI/SQLAlchemy-independent engine in `backend/app/engine.py`.
  It validates graph inputs, applies time and edge-weight eligibility,
  calculates minimum depth with BFS, enumerates bounded simple paths, scores
  paths using D3, aggregates with D5/D12, derives confidence from dependency
  review quality, and produces deterministic explanations and safety warnings.
- Added canonical input snapshots, SHA-256 hashes, algorithm versioning, and
  `analysis_input_from_snapshot` for replaying prior runs without reading live
  entity or dependency records.
- Added `backend/app/analysis_service.py` for organization-scoped snapshot
  loading, synchronous execution, result/path persistence, audit logging,
  tenant-scoped run/result/path retrieval, and safe failed-run diagnostics.
- Added analysis run, result and path schemas and routes in
  `backend/app/schemas.py` and `backend/app/api.py`. Analysis reads require
  `event:read`; run creation requires `analysis:run`.
- Added `input_snapshot` and `running`/`completed_with_limits` status support
  to the ORM, plus Alembic revision
  `backend/migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py`.
- Added the Section 7.10 engine matrix and API/migration integration coverage.
  Engine tests assert the 32.256/32.3 synopsis example. API tests exercise the
  seeded campus and transport analyses, tenant boundaries, audited failures,
  historical results after live entity edits, and snapshot replay.
- Updated `docs/api/README.md`, `docs/api/openapi.json`, `README.md`,
  `docs/viva-notes.md`, and `docs/progress.md`.

No frontend integration, scenario execution, Docker/Compose change, or live
cloud/PostgreSQL operation was performed.

## 3. Decisions

- The human explicitly approved Phase 5 and the NetworkX runtime dependency.
  The lockfile resolves NetworkX 3.6.1; no new ADR was required.
- Existing ADRs govern implementation: ADR-003 scoring, ADR-004 depth/path
  limits, ADR-005 aggregation, ADR-006 confidence, ADR-011 deterministic
  limits, and ADR-017 immutable snapshots.
- Run creation remains synchronous and bounded. Node/path ceilings return
  `completed_with_limits`, never a successful-looking complete result.
- Analysis endpoints use the existing REST version, local/test authentication
  adapter, permission checks, tenant scoping, error envelope and pagination.
- PostgreSQL concurrent-insert snapshot behavior has not been stress-tested.
  Row locks are used where supported; SQLite does not provide equivalent row
  locking.
- The root `agent-brief.md` still refers to absent `docs/agent-brief.md`.
  Requirements were taken from the available root continuation brief; neither
  brief was rewritten.

## 4. Verification performed

The `uv` executable was invoked through
`$env:APPDATA\Python\Python311\Scripts\uv.exe` because its Scripts directory
is not on the tool-shell PATH.

| Command/check | Result | Evidence |
|---|---|---|
| Phase implementation commit | PASS | `5a5a6db` on `feature/engine-ripple`; the verified code and tests are committed |
| `uv run --locked pytest` (from `backend`) | PASS | 86 tests passed |
| `uv run --locked ruff check app tests scripts migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py` (from `backend`) | PASS | All checks passed |
| `uv run --locked ruff format --check app tests scripts migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py` (from `backend`) | PASS | 19 files already formatted |
| Initial `uv run --locked ruff check app tests scripts migrations` (from `backend`) | FAIL | Reported 12 pre-existing lint findings in `b4fceea3f1e2_initial_data_foundation.py`; the historical migration was left unchanged. The final targeted command above passes. |
| First transport-fixture test run | FAIL | The test's hand-calculated expected score was incorrect (`11.478528`); recomputed from D3 as `11.501568`, and the final full suite passes. |
| Pylance diagnostics for changed application, schema, engine, API, tests and migration files | PASS | No error-severity diagnostics in changed files |
| Fresh SQLite `alembic upgrade head`, `alembic downgrade b4fceea3f1e2`, `alembic upgrade head`, then `alembic check` | PASS | Round-trip succeeded; no schema drift detected |
| `uv run --locked python -m scripts.export_openapi` (from `backend`) | PASS | Regenerated the checked-in OpenAPI contract; exact snapshot comparison passes in the test suite |
| `uv audit --locked` (from `backend`) | PASS | No known vulnerabilities or adverse statuses in 33 packages |
| Synthetic benchmark, three measurements per fixture | PASS | 5,000-node/4,999-edge chain median: 0.302038 s; 120-node/7,140-edge DAG median: 1.131815 s and explicit 10,000-path limit |
| Live PostgreSQL migration/concurrency check | NOT RUN | No live PostgreSQL server was available |
| Docker/Compose build or startup | NOT RUN | Docker daemon unavailable; Compose integration is a later phase |
| Secret/container scan | NOT RUN | Not run during this phase |

The benchmark used deterministic synthetic inputs and local `perf_counter`
measurements only. It establishes no general performance guarantee or SLO.

## 5. Test results

- Tests run: complete backend suite.
- Passed: 86.
- Failed: 0.
- Skipped: 0.
- Coverage: not measured.
- During test development, an initial transport-fixture assertion failed due
  to an incorrect expected-value calculation; after correcting it, the full
  suite passed. The broad Ruff attempt also exposed pre-existing findings in
  the initial migration; no unrelated migration edits were made.
- Known gaps: no live PostgreSQL concurrency/locking test, no frontend-to-API
  journey, and no scenario execution/isolation test.

## 6. Security and data integrity

- Tenant isolation: analysis snapshots query only the active organization;
  run/result/path reads are organization-scoped. API tests assert a member of
  another organization receives 404 for a run.
- Authorization: `analysis:run` and `event:read` are enforced through the
  existing server-side membership/role helpers.
- Historical data: snapshots preserve input values; replay tests reproduce
  the analysis hash and results; an API test separately verifies historical
  results after a live entity is renamed.
- Audit logging: successful and failed analysis runs are audited in the same
  SQLAlchemy session; tests verify request-ID correlation and safe failure
  metadata.
- Failure responses expose only a diagnostic ID, not engine exceptions or
  stack traces.
- Dependency audit: `uv audit --locked` found no known vulnerabilities in 33
  locked packages. Secret and container scans were not run.
- Unresolved concern: PostgreSQL phantom/concurrent-insert behavior and
  production-scale synchronous workloads require follow-up verification.

## 7. Evidence integrity

- Evidence produced: 85 backend tests, Ruff checks, Pylance diagnostics,
  SQLite migration round-trip and schema check, OpenAPI snapshot, dependency
  audit, and two local synthetic benchmark measurements.
- Evidence still TODO(human): Phase 2 participant interviews, consented
  research, the human-owned Figma prototype and usability findings.
- UX hypotheses remain unvalidated.
- No live PostgreSQL, Docker, cloud deployment, frontend analysis workflow,
  production authentication, or CI result is claimed.

## 8. Deviations and blockers

- No material deviation from the approved engine/API scope.
- The approved NetworkX dependency is recorded in `backend/pyproject.toml`
  and `backend/uv.lock`.
- SQLite migration verification does not substitute for a live PostgreSQL
  migration or concurrency test.
- Synchronous API execution and concurrent-insert consistency need review
  before production workloads.
- Blockers: no Docker daemon or PostgreSQL server was available. Human-led
  Phase 2 work remains partial and can continue independently.
- Approval status: Phase 5 was explicitly approved and is complete. Phase 6
  has not been approved.

## 9. Progress file

`docs/progress.md` records Phase 5 as complete and awaiting human review,
lists verification and benchmark evidence, and sets Phase 6 as the next gated
phase.

## 10. Human review required

- Review the score formula, `max`/`capped_sum` path retention and tie-breaking,
  confidence semantics, configured limits, and API response contract.
- Review the synchronous execution and PostgreSQL concurrency limitation.
- Review `docs/api/openapi.json` and the migration before approving Phase 6.
- Explicitly approve Phase 6 before frontend integration begins.

## 11. Phase exit assessment

- Exit criteria met: **YES**.
- Evidence-backed explanation: required engine cases pass; the 32.256/32.3
  synopsis example is asserted; cycles, multiple paths, depth, thresholds,
  confidence, deterministic hashes, and both safety ceilings are covered.
  API persistence, tenant authorization, audit records, OpenAPI and snapshot
  replay are integration-tested. Incomplete runs are explicitly marked.
- Recommended next phase: Phase 6 — Frontend integration, only after explicit
  human approval.

**STOP HERE. Do not begin Phase 6 until the human explicitly approves.**
