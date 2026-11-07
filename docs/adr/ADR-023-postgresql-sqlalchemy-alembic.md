# ADR-023: PostgreSQL persistence and reviewed migrations

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D23

## Context

The data model requires relational constraints, tenant-safe composite references, and reproducible schema evolution.

## Decision

Use PostgreSQL, SQLAlchemy 2.x (or a comparably explicit supported ORM), and Alembic. Use UUID keys, timezone-aware timestamps, checks, unique constraints, indexes, and organization-scoped composite foreign keys. Build deployed schemas from reviewed migrations; do not rely on `create_all()`.

## Alternatives considered

- A non-relational store was not selected because the specification requires composite foreign keys and relational integrity.

## Consequences

Migrations and tests must validate empty-database setup and tenant constraints. ORM selection within the specified compatibility remains to be confirmed if environment constraints arise.

## Evidence

D23 in the continuation brief. Human acceptance is pending.
