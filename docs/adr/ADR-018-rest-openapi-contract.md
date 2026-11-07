# ADR-018: Versioned REST and OpenAPI contract

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D18

## Context

The frontend and backend need a stable, explicit API contract.

## Decision

Use REST JSON under `/api/v1`, UUID public resource paths, pagination, stable ordering, filters, and consistent error envelopes. Generate OpenAPI with FastAPI and keep a reviewed snapshot. Keep Pydantic request/response schemas separate from persistence and engine structures; never expose ORM objects. Breaking changes require an API versioning decision and ADR.

## Alternatives considered

- Exposing ORM objects directly was rejected because it couples the public contract to persistence internals.

## Consequences

Contract tests and deliberate OpenAPI snapshot updates are required. Pagination style and 400/422 distinction remain implementation choices to document.

## Evidence

D18 in the continuation brief. Human acceptance is pending.
