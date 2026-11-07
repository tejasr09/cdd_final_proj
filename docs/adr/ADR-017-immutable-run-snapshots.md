# ADR-017: Immutable run inputs and reproducibility

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D17

## Context

Historical results must remain explainable after live inputs change.

## Decision

Each run stores an immutable snapshot of all result-affecting event, trigger, entity, dependency, review, scenario, configuration, `as_of`, aggregation, and algorithm-version inputs. Store a canonical input hash and algorithm version. Never silently recalculate old runs; reruns create new runs.

## Alternatives considered

- Recomputing historical results from current records was rejected because it changes the basis of the original result.

## Consequences

Snapshot content, canonicalization, and hash versioning must be defined and tested. Storage impact must be monitored.

## Evidence

D17 in the continuation brief. Human acceptance is pending.
