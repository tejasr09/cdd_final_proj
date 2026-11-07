# ADR-006: Confidence represents data quality

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D6

## Context

The synopsis calls for confidence but does not define its meaning.

## Decision

Confidence measures dependency data quality, not likelihood. Dependency review statuses map to values as follows: draft 0.5, reviewed 0.8, validated 1.0. A result's confidence is the weakest edge confidence on its primary path; triggers have confidence 1.0 and hypothetical scenario edges count as draft. Display confidence as low, medium, or high with its reason.

## Consequences

Confidence must not be presented as probability. The numeric-to-display category boundaries are not specified in the available brief and must not be invented here.

## Alternatives considered

- Interpreting confidence as outcome likelihood or averaging path-edge statuses was rejected by D6.

## Evidence

D6 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
