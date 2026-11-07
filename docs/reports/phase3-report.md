# Phase 3 Report — Data foundation and tenancy

## 1. Objective

Implement the Phase 3 persistence and tenant-safety foundation under the
human-approved Phase 3 scope: relational models, migrations, memberships,
authorization helpers, scoped repositories, audit persistence, and
development-only synthetic fixtures. Phase 2 remains partial and may proceed
in parallel with Phases 3–5 as the continuation brief specifies.

## 2. Work completed

- Added SQLAlchemy models for organizations, users, memberships, entities,
  dependencies, events, triggers, scenarios, impact runs/results/paths/path
  steps, scenario overlays, interventions, and audit logs in
  [`backend/app/models.py`](../../backend/app/models.py).
- Added database engine/session setup, mandatory `DATABASE_URL`, SQLite
  foreign-key enforcement, and database readiness checks in
  [`backend/app/database.py`](../../backend/app/database.py).
- Added tenant-scoped repositories, membership and role authorization helpers,
  and authorized/audited service operations in
  [`backend/app/repositories.py`](../../backend/app/repositories.py),
  [`backend/app/auth.py`](../../backend/app/auth.py), and
  [`backend/app/services.py`](../../backend/app/services.py).
- Added an initial Alembic migration and configuration. The migration keeps
  SQLite tenant-FK enforcement and defers the cyclic scenario-to-baseline-run
  FK until after table creation for PostgreSQL. Event lifecycle values match
  D13 (`draft`, `open`, `resolved`, `archived`) in both the model and migration.
- Added deterministic, idempotent synthetic fixtures for two organizations in
  [`backend/app/seed.py`](../../backend/app/seed.py). Seeding is restricted to
  development/test and local database targets.
- Added migration, seed, tenancy, authorization, audit, and database readiness
  tests.
- Updated the README, data-model and security/tenancy architecture notes,
  viva notes, progress file, and Phase 2 status note. Added this report.

## 3. Decisions

- Followed the approved PostgreSQL / SQLAlchemy / Alembic baseline and existing
  tenancy, role, audit, and authentication ADRs. No new ADR was required.
- SQLite is supported for local development and tests; PostgreSQL remains the
  authoritative persistence target.
- Kept HTTP CRUD endpoints, production identity-provider configuration,
  Compose migration orchestration, and analysis behavior for their later
  phases. No GitHub Actions, remote operations, or cloud changes were made.
- The explicitly approved Phase 3 work proceeded while Phase 2 remains
  partial, consistent with the continuation brief and the user's request to
  defer human-led Figma/research for now.

## 4. Verification performed

| Command/check | Result | Evidence |
|---|---|---|
| `Set-Location backend; & "$env:APPDATA\Python\Python311\Scripts\uv.exe" run --locked pytest` | PASS | 16 tests passed |
| `Set-Location backend; & "$env:APPDATA\Python\Python311\Scripts\uv.exe" run --locked ruff check app tests` | PASS | Ruff: all checks passed |
| `Set-Location backend; & "$env:APPDATA\Python\Python311\Scripts\uv.exe" run --locked ruff format --check app tests migrations/versions/b4fceea3f1e2_initial_data_foundation.py` | PASS | All 12 checked Python files already formatted |
| Fresh temporary SQLite DB: `alembic upgrade head`, then `alembic check` | PASS | Migration applied; `No new upgrade operations detected.` |
| PostgreSQL offline `alembic upgrade --sql head` using a placeholder URL | PASS | Generated SQL places `ALTER TABLE scenarios ADD CONSTRAINT fk_scenarios_baseline_run_tenant` after `CREATE TABLE impact_runs`; no server was contacted |
| Live PostgreSQL migration, Docker startup, Compose startup | NOT RUN | Docker daemon/live PostgreSQL unavailable; offline PostgreSQL DDL ordering was checked instead |
| Dependency/container vulnerability scan | NOT RUN | No new network-based scan was run for this phase |

## 5. Test results

- Tests run: complete backend `pytest` suite.
- Passed: 16.
- Failed: 0.
- Skipped: 0.
- Coverage: not measured.
- Known gaps: no live PostgreSQL integration execution; HTTP CRUD and end-to-end
  authentication are not implemented. Service-level create/update/archive
  foundations are tested for the operations implemented.

## 6. Security and data integrity

- Tenant-isolation checks: repositories scope by organization; migrated SQLite
  tests reject cross-organization dependency and scenario baseline references;
  test coverage also checks event-trigger and scenario-overlay references.
- Authorization checks: role permissions, active membership, non-member 404
  behavior, denied writes, and local-auth opt-in are tested.
- Secret scan: not run.
- Dependency/container scan: not run in this phase.
- Audit-log checks: tests verify audit rows are written for implemented
  authorized state changes in the same SQLAlchemy session.
- Unresolved concern: live PostgreSQL FK enforcement and transaction behavior
  still require execution against a local PostgreSQL service. The local auth
  adapter is not production authentication and is not yet wired to business
  HTTP endpoints.

## 7. Evidence integrity

- Evidence produced: 15 passing backend tests, clean Ruff checks, a fresh
  SQLite migration and idempotent seed, no Alembic schema drift, and offline
  PostgreSQL DDL ordering evidence.
- Evidence still TODO(human): live PostgreSQL/Docker startup, participant
  research, consented findings, human-owned Figma prototype, and usability
  results.
- Hypotheses still unvalidated: all Phase 2 personas, journeys, IA, and
  proposed flows.
- Claims intentionally not made: no live PostgreSQL execution, Docker/Compose
  success, production auth, business HTTP CRUD, analysis-engine behavior,
  performance benchmark, or UX validation is claimed.

## 8. Deviations and blockers

- Deviations from the brief: no product-scope deviation. The initial migration
  has dialect-specific creation handling for the cyclic composite FK.
- Why it was necessary: PostgreSQL must create both referenced tables before
  adding the cycle; SQLite requires the composite FK inline to test
  cross-tenant enforcement without `ALTER TABLE`.
- Approval status: migration and model behavior follow the existing approved
  database and tenancy decisions. No live database or cloud resources were
  changed.
- Blockers: live PostgreSQL and Docker are unavailable; production identity
  remains undecided. HTTP API behavior belongs to Phase 4.

## 9. Progress file

[`docs/progress.md`](../progress.md) records current phase/branch, completed
work, parallel Phase 2 TODOs, blockers, verification, decisions, risks, and the
next approval gate. Phase 3 changes are on `feature/data-tenancy`; see
`git log -1` for the latest local revision.

## 10. Human review required

1. Review the schema and the dialect-specific cyclic-FK migration.
2. Run the migration and seed against a local PostgreSQL instance when
   available; Docker/Compose startup remains unverified.
3. Explicitly approve Phase 4 before API implementation begins.
4. Select a production identity provider before production authentication is
   designed or configured.
5. Complete Phase 2 research/Figma/usability deliverables when ready; Phase 2
   remains partial but does not block approved work in Phases 3–5.

## 11. Phase exit assessment

- Exit criteria met: PARTIAL.
- Evidence-backed explanation: fresh SQLite migration and seed, tenant
  constraints, service-level authorization/audit checks, and repository
  isolation tests pass. PostgreSQL DDL ordering is checked offline, but live
  PostgreSQL execution is outstanding. CRUD foundations exist at the service
  layer; HTTP CRUD belongs to Phase 4.
- Recommended next phase: Phase 4 — API foundation, only after explicit human
  approval.

STOP HERE. Do not begin Phase 4 until the human explicitly approves.
