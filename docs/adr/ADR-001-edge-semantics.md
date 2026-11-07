# ADR-001: Directed dependency semantics

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D1

## Context

The graph needs a consistent interpretation of dependency direction and labels, including cycles and duplicate relationships.

## Decision

An edge from source to target means a change, outage, or failure in the source may affect the target. Forward labels describe the source-to-target relationship; inbound views use the corresponding reverse phrasing. Direction is consistent in code, API, and UI. There is at most one edge per ordered entity pair, self-loops are disallowed, and cycles are allowed and must be handled.

## Consequences

Implementations and explanations must preserve this direction. Cycle handling is required; the specific algorithm is not chosen by this ADR.

## Alternatives considered

- Reversing direction for inbound views was rejected because it would make API, graph, and explanation semantics inconsistent.
- Disallowing cycles was rejected; the graph must handle them safely.

## Evidence

D1 in `agent-brief.md`. The decision was included in the previously approved bounded Phase 0.
