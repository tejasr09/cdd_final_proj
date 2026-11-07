# ADR-011: Deterministic bounded path enumeration

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D11

## Context

Simple-path enumeration can grow rapidly, and truncation must not be mistaken for a complete analysis.

## Decision

Enumerate simple paths only, bounded by `max_depth`, `max_paths_per_trigger` (default 10,000), and `max_nodes_per_run` (default 5,000). Validate documented safe ranges. Deterministically order outgoing edges and candidates. When a ceiling is reached, return `completed_with_limits`, record truncation details, and mark results potentially incomplete.

## Alternatives considered

- Silently truncating or returning a complete status was rejected because it misrepresents incomplete results.

## Consequences

Limits, counts, and incomplete status must be represented through engine, API, persistence and UI. Safe configurable ranges remain to be specified.

## Evidence

D11 in the continuation brief. Human acceptance is pending.
