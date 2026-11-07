# ADR-002: Severity and impact scales

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D2

## Context

Severity, persisted impact values, display precision, and impact labels need consistent scales.

## Decision

Severity is an integer from 0 to 100 and is normalized as severity / 100. Impact is computed internally on a 0-to-1 scale, represented on a 0-to-100 scale, rounded to six decimal places when persisted, and shown to one decimal place. Impact levels are low below 25, moderate from 25 to below 50, high from 50 to below 75, and critical from 75 onward. Each run stores its impact-level thresholds.

## Consequences

Validation, storage, display, and run configuration must use these scales and boundaries. This does not select a storage or API technology.

## Alternatives considered

- Using a probability scale or inconsistent display/persistence precision was rejected because scores are estimates with explicitly defined boundaries.

## Evidence

D2 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
