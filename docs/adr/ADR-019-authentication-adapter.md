# ADR-019: Authentication provider boundary

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D19

## Context

Authorization and domain code should not be bound to an identity provider, while local development must be testable without inventing production identity settings.

## Decision

Use an authentication adapter. Provide a documented local/test implementation, disabled in deployed environments unless explicitly configured. Configure and validate production issuer, audience, allowed algorithms, and key discovery. Never accept unsigned tokens or trust browser-supplied organization/role claims. No production provider is selected in Phase 0.

## Alternatives considered

- Hard-coding a production identity provider now was rejected because provider and deployment requirements are unconfirmed.

## Consequences

Phase 3 must select and document local test authentication details. Production provider configuration remains open and requires human approval.

## Evidence

D19 in the continuation brief and Appendix F, question 3. Human acceptance/provider selection is pending.
