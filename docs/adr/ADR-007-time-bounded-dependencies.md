# ADR-007: Time-bounded dependency eligibility

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D7

## Context

Dependencies can change over time, and runs need a reproducible point in time for selecting active relationships.

## Decision

A dependency participates in a run only when it is active, its validity window contains `as_of`, and neither endpoint is archived. `as_of` defaults to the event start time and is stored in the run configuration. Event duration is informational in version 1 and does not affect the score.

## Consequences

Runs must retain their effective `as_of` value and apply the same temporal eligibility rule. Ignoring event duration is a known limitation that must be documented.

## Alternatives considered

- Evaluating each dependency against a separately sampled current time was rejected because it would make one run internally inconsistent.
- Including event duration in v1 scoring was rejected by D7.

## Evidence

D7 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
