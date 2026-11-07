# ADR-008: Tenant isolation

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D8

## Context

Organizations must not be able to reference or access another organization's data.

## Decision

Every tenant-owned table carries `organization_id`. Referencing tables use composite foreign keys on `(id, organization_id)` to prevent cross-tenant references at the database level. The API also scopes every query to the caller's membership. Non-members receive 404 to avoid disclosing resource existence; members lacking permission receive 403.

## Consequences

The eventual schema and API must enforce both database-level reference integrity and request-level membership scoping. The database, authentication mechanism, and permission model are unspecified in the available brief and remain undecided.

## Alternatives considered

- Application-only checks were rejected because they cannot prevent invalid cross-tenant references at the database boundary.
- Returning 403 for non-members was rejected because it can disclose resource existence.

## Evidence

D8 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
