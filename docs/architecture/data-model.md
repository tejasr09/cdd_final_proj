# Data model

## Phase 1 status

No persistence models, database connection, or migrations exist yet. PostgreSQL is defined as the intended authoritative store in [ADR-023](../adr/ADR-023-postgresql-sqlalchemy-alembic.md). Organization-scoped tables and composite tenant foreign keys are specified in Section 6 of the combined brief and remain planned for Phase 3.

The Compose database is an empty local service; the API currently has no database adapter.
