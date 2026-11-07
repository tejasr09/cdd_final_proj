# ADR-015: Interventions are explicit hypothetical changes

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D15

## Context

Scenario changes should be understandable and must not be presented as guaranteed recommendations.

## Decision

Support node mitigation and dependency weight overrides in [0,1], dependency deactivation, and hypothetical dependencies marked draft. Record title, rationale, assumptions, author, and creation time. Derive estimated effect by comparing baseline and scenario results; do not accept a user-entered effectiveness score. Describe outcomes as lower estimated impact, never guaranteed mitigation.

## Alternatives considered

- An arbitrary manually entered effect score was rejected because it is not measured evidence.

## Consequences

Scenario changes require provenance and comparison logic. No automatic recommendation is implied.

## Evidence

D15 in the continuation brief. Human acceptance is pending.
