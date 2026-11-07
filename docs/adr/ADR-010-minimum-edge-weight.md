# ADR-010: Minimum eligible edge weight

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D10

## Context

Runs need a reproducible way to exclude dependencies below a user-selected relevance threshold.

## Decision

Support `min_edge_weight` from 0.0 through 1.0, default 0.0. Filter edges before path enumeration and persist/display the threshold in run configuration. Keep zero-weight dependencies in the model; they contribute zero impact.

## Alternatives considered

- Deleting zero-weight edges was rejected because weight is run eligibility/scoring data, not a deletion instruction.

## Consequences

The engine and API must validate the range and apply the inclusive boundary.

## Evidence

D10 in the continuation brief. Human acceptance is pending.
