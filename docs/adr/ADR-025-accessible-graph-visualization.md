# ADR-025: Graph is a directional visualization, not source of truth

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D25

## Context

The graph must communicate dependency direction and impact while remaining accessible.

## Decision

Render arrows source-to-target with relationship metadata and rationale. Distinguish entity types and impact levels without color alone; identify trigger, affected, context, and scenario-added nodes. Provide a keyboard/screen-reader-friendly list or table alternative and focused views for larger graphs.

## Alternatives considered

- A canvas-only graph was rejected because it excludes users who cannot effectively use the canvas.

## Consequences

Graph interactions must have accessible names and a synchronized non-canvas representation.

## Evidence

D25 in the continuation brief. Human acceptance is pending.
