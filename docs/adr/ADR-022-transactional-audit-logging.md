# ADR-022: Transactional append-only audit logging

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D22

## Context

State changes and analysis runs need an auditable record without exposing secrets or unnecessary personal data.

## Decision

Write an audit record for each successful state-changing API operation in the same transaction where practical. Include actor, organization, action, resource reference, timestamp, request/correlation ID, and minimal change summary. Keep application audit records append-only. Never log credentials, tokens, secrets, or unnecessary personal data.

## Alternatives considered

- Logging only after the transaction was rejected as the primary approach because it can leave an un-audited committed change.

## Consequences

Audit writes and domain changes need coordinated transaction handling. Failure behavior where atomicity is not practical must be documented.

## Evidence

D22 in the continuation brief. Human acceptance is pending.
