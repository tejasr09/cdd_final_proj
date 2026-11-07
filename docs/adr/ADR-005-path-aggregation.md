# ADR-005: Path scoring and aggregation

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D5

## Context

The analysis must select a defensible impact score while retaining alternative path provenance and handling ties deterministically.

## Decision

The default aggregation is `max`: use the highest-scoring qualifying simple path. The optional `capped_sum` aggregation sums the best path per distinct final edge into the entity and caps the result at 100. Ties are resolved by fewer edges, then by the lexicographically smaller sequence of entity IDs. Alternative paths are retained for provenance, with no path counted twice. BFS may determine minimum depth, but scoring must enumerate bounded paths rather than retaining only one BFS path per node.

## Consequences

The engine must distinguish depth calculation from path scoring, enforce the path bound, and produce deterministic primary paths. The implementation and data representation remain open.

## Alternatives considered

- Retaining only a BFS path for scoring was rejected because it may not be the best-scoring path.
- Counting duplicate paths was rejected because it inflates aggregate impact.

## Evidence

D5 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
