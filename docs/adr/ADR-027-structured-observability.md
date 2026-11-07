# ADR-027: Structured logs and health semantics

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D27

## Context

Local and deployed services need actionable diagnostics without leaking graph payloads or personal data.

## Decision

Use structured logs with severity, timestamp, service, request/correlation ID, and event type. Separate liveness from readiness; readiness checks required dependencies such as the database. Do not log full graph payloads or personal data. Treat operational metrics as service indicators, not evidence of analysis accuracy.

## Alternatives considered

- A single health response conflating process liveness and dependency readiness was rejected because it obscures failure causes.

## Consequences

Health endpoints and logging fields must be documented and tested. Metrics scope should remain basic unless justified.

## Evidence

D27 in the continuation brief. Human acceptance is pending.
