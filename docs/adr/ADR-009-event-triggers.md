# ADR-009: Explicit event trigger associations

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D9

## Context

Events can affect multiple entities, and each trigger may carry its own rationale and exposure.

## Decision

Represent event/entity links as explicit organization-scoped `event_triggers` records. Default trigger exposure to 1.0; use shared event severity in v1. Include trigger entities at depth zero by default, with effective severity after trigger exposure and mitigation. Propagate independently from each trigger and apply the configured run aggregation.

## Alternatives considered

- Embedding entity IDs in event JSON was rejected because associations require tenant constraints and independent validation.

## Consequences

The schema and engine input must preserve trigger provenance. A database-level organization constraint must cover each association.

## Evidence

D9 in the continuation brief. Human acceptance is pending.
