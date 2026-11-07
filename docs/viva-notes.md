# Ripple Effect — Viva Notes

These notes describe the intended learning map. Do not describe planned behavior as implemented. Update each topic with file locations, a concrete example, tests, and limitations as implementation proceeds.

## Status key

- `PLANNED`: not implemented yet.
- `PARTIAL`: foundational pieces exist; the complete product behavior is not done.
- `IMPLEMENTED`: source and tests exist; cite exact paths.
- `VERIFIED`: relevant checks were run; cite actual evidence.

## Topics

1. `VERIFIED` Directed graphs and source → target dependency semantics. The pure engine constructs a NetworkX `DiGraph` in [`backend/app/engine.py`](../backend/app/engine.py); edge direction and reverse non-propagation are asserted in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py).
2. `VERIFIED` BFS and minimum propagation depth. A separate breadth-first traversal computes minimum depth; tests cover ties and a minimum depth that differs from the primary scoring path in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py).
3. `VERIFIED` Bounded simple-path enumeration and cycle safety. Per-path entity membership prevents revisiting nodes, while deterministic depth/path ceilings mark truncated results; cycle and ceiling cases are in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py).
4. `VERIFIED` Impact scoring, attenuation, and mitigation. D3 scoring applies trigger exposure/mitigation and entered-node mitigation; the synopsis example is tested at 32.256 (32.3 displayed) in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py).
5. `VERIFIED` Max versus capped-sum aggregation. D5/D12 aggregation retains the primary and contributing paths, selects one best path per distinct final edge for capped sum, and caps at 100; explicit aggregation and deduplication tests are in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py).
6. `VERIFIED` Confidence as dependency-data quality. Confidence uses the weakest primary-path review status and is returned separately from impact; draft/reviewed/validated mappings and explanatory wording are tested in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py).
7. `VERIFIED` Composite foreign keys and tenant isolation. Tenant-owned references include both the record ID and `organization_id`; SQLite foreign-key enforcement is enabled in [`backend/app/database.py`](../backend/app/database.py). Models and constraints are in [`backend/app/models.py`](../backend/app/models.py); repository methods scope reads by organization in [`backend/app/repositories.py`](../backend/app/repositories.py). Cross-tenant dependency, trigger, scenario and migration references are rejected in [`backend/tests/test_tenancy.py`](../backend/tests/test_tenancy.py) and [`backend/tests/test_migrations.py`](../backend/tests/test_migrations.py). This has not yet been exercised against a live PostgreSQL server.
8. `PARTIAL` Authentication versus authorization. [`backend/app/auth.py`](../backend/app/auth.py) gates local identity headers on development/test mode plus `ENABLE_LOCAL_AUTH=true`, resolves active membership, and centralizes role permissions. The database membership role—not a client-supplied role—controls service authorization. Production identity and HTTP endpoint integration remain future work; tests cover local-auth gating, membership, and permissions in [`backend/tests/test_tenancy.py`](../backend/tests/test_tenancy.py).
9. `VERIFIED` REST API and OpenAPI. FastAPI exposes tenant-scoped entity, dependency, event, trigger and analysis endpoints in [`backend/app/api.py`](../backend/app/api.py); request/response schemas are in [`backend/app/schemas.py`](../backend/app/schemas.py), route behavior is exercised in [`backend/tests/test_api.py`](../backend/tests/test_api.py), and the reviewed contract is [`docs/api/openapi.json`](./api/openapi.json). Scenario and production sign-in/session endpoints remain future work.
10. `VERIFIED` Database migrations and seed data. [`backend/migrations/versions/b4fceea3f1e2_initial_data_foundation.py`](../backend/migrations/versions/b4fceea3f1e2_initial_data_foundation.py) and [`backend/migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py`](../backend/migrations/versions/c13a4f8d2b71_add_analysis_run_snapshot.py) build and extend a fresh schema; [`backend/app/seed.py`](../backend/app/seed.py) creates deterministic, idempotent development-only fixtures for two organizations. Fresh migration, snapshot-column and run-status checks are in [`backend/tests/test_migrations.py`](../backend/tests/test_migrations.py). No live PostgreSQL migration was run.
11. `PARTIAL` Scenario overlays and immutable baseline data. The organization-scoped schema separates scenarios, overrides, interventions, impact runs, paths, and results in [`backend/app/models.py`](../backend/app/models.py). Baseline run inputs are snapshotted and replay-tested by [`backend/app/engine.py`](../backend/app/engine.py) and [`backend/tests/test_api.py`](../backend/tests/test_api.py); scenario execution and scenario-to-live isolation remain future work.
12. `VERIFIED` Audit logging and transaction boundaries. Entity, event, dependency and trigger operations plus analysis-run completion/failure add organization-scoped `AuditLog` rows through the same SQLAlchemy session in [`backend/app/services.py`](../backend/app/services.py) and [`backend/app/analysis_service.py`](../backend/app/analysis_service.py). API tests assert analysis audit status and request correlation. Database-level append-only enforcement is not implemented.
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

- Phase 5 evidence: engine and analysis API tests exercise deterministic scoring, path aggregation, safety limits, tenant authorization, audit records and snapshot replay. Record the exact final test and lint counts in `docs/reports/phase5-report.md`.
- No live PostgreSQL or Docker execution, CI run, cloud deployment, human UX research, or graph performance benchmark has been verified.
- The architecture and design decisions are requirements from the project brief, not claims of implementation.
