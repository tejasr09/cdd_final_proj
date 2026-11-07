# ADR-020: Membership-scoped server-side authorization

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D20

## Context

Users may belong to multiple organizations, and tenant data must not be disclosed across memberships.

## Decision

Require an explicit active organization derived from validated membership. Never treat a client-provided organization ID as authorization. Return 404 for non-members accessing organization-owned resources and 403 for members without permission. Enforce authorization on the server for every resource and endpoint.

## Alternatives considered

- UI-only access control or UUID unpredictability was rejected by the brief's security requirements.

## Consequences

Repositories and authorization dependencies must receive validated tenant context. Tests must cover cross-tenant access.

## Evidence

D20 in the continuation brief and D8 in `agent-brief.md`. Human acceptance is pending.
