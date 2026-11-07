# Data model

## Status

The Phase 3 data foundation is implemented in SQLAlchemy models and an Alembic
initial migration. PostgreSQL is the authoritative store; SQLite is supported
for tests and local development. Deployed schemas must be created with Alembic,
not `Base.metadata.create_all()`.

## Organization-scoped records

`Organization` owns memberships, entities, dependencies, events, event triggers,
scenarios, impact runs/results/paths, scenario overlays, interventions, and
audit logs. Tenant-owned tables carry `organization_id`. References between
tenant-owned records use composite foreign keys that include the organization
ID, so a valid record ID from another organization is not sufficient.

The schema includes:

- `User` and `OrganizationMember`, with unique organization/user membership
  and constrained roles and membership states.
- `Entity`, `Dependency`, `OperationalEvent`, and `EventTrigger`, with
  validated ranges, lifecycle values, and indexes for organization-scoped
  access.
- `Scenario`, `ImpactRun`, `ImpactResult`, `ImpactPath`, and `ImpactPathStep`,
  including organization-scoped run snapshots and path provenance.
- Scenario event/entity/dependency overlays and `Intervention`, kept separate
  from live records.
- `AuditLog`, which records the actor, organization, action, resource and
  minimal change summary.

`Scenario.baseline_run_id` and `ImpactRun.scenario_id` create a deliberate
cyclic reference. SQLAlchemy defers the baseline foreign key for PostgreSQL.
The reviewed initial migration creates it inline for SQLite and adds it after
the dependent tables for PostgreSQL.

## Migrations and synthetic data

From `backend`, set `DATABASE_URL` to a local SQLite or PostgreSQL URL and run
`uv run --locked alembic upgrade head`. Then set `APP_ENV=development` and run
`uv run --locked python -m app.seed`. The seed is deterministic and idempotent
and contains synthetic records for two organizations. It refuses to run
outside development/test or against a non-local PostgreSQL host. Never use
these fixtures as real institutional data.

Migration integration tests build a fresh SQLite database, verify repeated
seeding, and reject cross-organization references. PostgreSQL migration SQL
was generated offline to check table/constraint ordering; a live PostgreSQL
server was not available for execution during Phase 3.

## Implementation boundaries

The schema includes scenario and analysis-result tables for later phases, but
the analysis engine, HTTP CRUD API, and scenario execution are not implemented
by the Phase 3 data foundation.
