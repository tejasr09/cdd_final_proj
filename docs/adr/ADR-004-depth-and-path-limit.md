# ADR-004: Analysis depth

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D4

## Context

Analysis needs a finite path bound and a stable definition of an entity's depth when multiple triggers or paths exist.

## Decision

An entity's depth is the minimum number of edges from any trigger among its qualifying paths; triggers have depth zero. Paths are limited by `max_depth`, default 4, with an allowed range of 1 through 10. The primary (best-scoring) path may be longer than the minimum depth; explanations must state this when it occurs.

## Consequences

Depth and the primary path are distinct concepts and must not be conflated in results. The concrete path-search implementation is not selected here.

## Alternatives considered

- Defining depth from the primary scoring path was rejected because the primary path may be longer than the minimum qualifying path.

## Evidence

D4 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
