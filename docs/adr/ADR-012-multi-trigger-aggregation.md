# ADR-012: Multi-trigger result aggregation

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D12

## Context

An entity can be reached from multiple triggers, and duplicate traversal must not inflate its impact.

## Decision

First compute the best path per trigger using the D5 rules. Under `max`, select the highest-scoring path across triggers. Under `capped_sum`, sum the best path per distinct final dependency edge across the run and cap at 100. Identify paths by ordered entity and dependency IDs, retain primary and contributing paths separately, and record each originating trigger. Do not count the same path twice.

## Alternatives considered

- Summing independently per trigger was rejected because the same path could be counted more than once.

## Consequences

Aggregation requires cross-trigger path identity and provenance. D5 tie-break rules remain authoritative.

## Evidence

D12 in the continuation brief. Human acceptance is pending.
