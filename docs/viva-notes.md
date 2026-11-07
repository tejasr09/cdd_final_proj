# Ripple Effect — Viva Notes

These notes describe the intended learning map. Do not describe planned behavior as implemented. Update each topic with file locations, a concrete example, tests, and limitations as implementation proceeds.

## Status key

- `PLANNED`: not implemented yet.
- `PARTIAL`: foundational pieces exist; the complete product behavior is not done.
- `IMPLEMENTED`: source and tests exist; cite exact paths.
- `VERIFIED`: relevant checks were run; cite actual evidence.

## Topics

1. `PLANNED` Directed graphs and source → target dependency semantics.
2. `PLANNED` BFS and minimum propagation depth.
3. `PLANNED` Bounded simple-path enumeration and cycle safety.
4. `PLANNED` Impact scoring, attenuation, and mitigation.
5. `PLANNED` Max versus capped-sum aggregation.
6. `PLANNED` Confidence as dependency-data quality.
7. `VERIFIED` Composite foreign keys and tenant isolation. Tenant-owned references include both the record ID and `organization_id`; SQLite foreign-key enforcement is enabled in [`backend/app/database.py`](../backend/app/database.py). Models and constraints are in [`backend/app/models.py`](../backend/app/models.py); repository methods scope reads by organization in [`backend/app/repositories.py`](../backend/app/repositories.py). Cross-tenant dependency, trigger, scenario and migration references are rejected in [`backend/tests/test_tenancy.py`](../backend/tests/test_tenancy.py) and [`backend/tests/test_migrations.py`](../backend/tests/test_migrations.py). This has not yet been exercised against a live PostgreSQL server.
8. `PARTIAL` Authentication versus authorization. [`backend/app/auth.py`](../backend/app/auth.py) gates local identity headers on development/test mode plus `ENABLE_LOCAL_AUTH=true`, resolves active membership, and centralizes role permissions. The database membership role—not a client-supplied role—controls service authorization. Production identity and HTTP endpoint integration remain future work; tests cover local-auth gating, membership, and permissions in [`backend/tests/test_tenancy.py`](../backend/tests/test_tenancy.py).
9. `PARTIAL` REST API and OpenAPI. FastAPI currently exposes liveness and database readiness in [`backend/app/main.py`](../backend/app/main.py). Tenant-aware service methods exist, but business HTTP routes, request/response schemas, pagination, and an OpenAPI snapshot are Phase 4 work.
10. `VERIFIED` Database migrations and seed data. [`backend/migrations/versions/b4fceea3f1e2_initial_data_foundation.py`](../backend/migrations/versions/b4fceea3f1e2_initial_data_foundation.py) builds a fresh schema; [`backend/app/seed.py`](../backend/app/seed.py) creates deterministic, idempotent development-only fixtures for two organizations. The 16-test backend suite verifies a fresh SQLite migration and seed plus the D13 event lifecycle constraint; `alembic check` reports no schema drift. PostgreSQL SQL was generated offline to verify cyclic-FK ordering, but a live PostgreSQL migration was not run.
11. `PARTIAL` Scenario overlays and immutable baseline data. The organization-scoped schema separates scenarios, overrides, interventions, impact runs, paths, and results in [`backend/app/models.py`](../backend/app/models.py). Scenario execution, immutable snapshots, and proof that live records remain unchanged are not implemented yet.
12. `IMPLEMENTED` Audit logging and transaction boundaries. Entity, event, dependency creation, entity update, and archive service methods add a minimal `AuditLog` row through the same SQLAlchemy session in [`backend/app/services.py`](../backend/app/services.py). Tests verify audit records for implemented changes. Callers must commit or roll back the session; HTTP transaction handling and database-level append-only enforcement are not implemented.
13. `PLANNED` React component architecture and React Flow.
14. `PLANNED` Docker images, layers, and Compose networking.
15. `PLANNED` Git branches, commits, pull requests, and review.
16. `PLANNED` CI stages and quality gates.
17. `PLANNED` Image tags versus immutable digests.
18. `PLANNED` ACR and ACI deployment.
19. `PLANNED` Infrastructure as Code and plan/apply separation.
20. `PLANNED` Security scanning and secret management.

For each topic, add: what it means here; why it was chosen; implementation paths; a short example; test/evidence references; and a limitation or trade-off.

## Current evidence

- Phase 3 backend evidence: 16 tests pass; Ruff checks pass; a fresh SQLite migration plus seed is idempotent; `alembic check` reports no schema drift; offline PostgreSQL DDL places the cyclic scenario-to-baseline foreign key after both tables exist.
- No live PostgreSQL or Docker execution, Phase 4 business API, impact engine, CI run, cloud deployment, human UX research, or benchmark has been verified.
- The architecture and design decisions are requirements from the project brief, not claims of implementation.
