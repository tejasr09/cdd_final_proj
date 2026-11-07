# ADR-013: Event lifecycle and UTC time handling

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D13

## Context

Event eligibility and timestamps must have consistent lifecycle and time-zone semantics.

## Decision

Use `draft`, `open`, `resolved`, and `archived` event states. Only open events are live-run eligible by default; draft preview is optional and must not change status. Resolved/archived events remain historical and cannot be newly run unless an administrator reopens them. Require `start_at`; keep optional duration informational. Persist timezone-aware timestamps in UTC and display in the user's local zone. Default `as_of` to `start_at`.

## Alternatives considered

- Using duration in v1 scoring was rejected by the existing D7 decision.

## Consequences

Lifecycle transitions and timestamps require validation and tests. Preview behavior remains optional.

## Evidence

D13 in the continuation brief and D7 in `agent-brief.md`. Human acceptance is pending.
