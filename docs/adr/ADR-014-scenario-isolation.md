# ADR-014: Scenario overlays never mutate live data

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D14

## Context

What-if analysis must be safely repeatable without changing operational records.

## Decision

Model scenarios as versioned, organization-owned overlays on a baseline run. Store scenario events, entity/dependency overrides, and interventions separately. Run against a consistent baseline snapshot plus overlay and create a linked run. Do not apply scenarios to live data in v1. Discard/archive only scenario-owned records according to a retention policy that remains to be approved.

## Alternatives considered

- Editing live records and restoring them after a run was rejected because it risks operational corruption and non-reproducible state.

## Consequences

Overlay persistence and isolation tests are required. Retention details remain a human decision.

## Evidence

D14 in the continuation brief. Human acceptance is pending.
