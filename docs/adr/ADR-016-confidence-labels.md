# ADR-016: Confidence labels describe dependency review quality

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D16

## Context

Confidence must be distinct from impact and must communicate the quality of dependency data.

## Decision

Follow D6: use the weakest review status on the primary path, with draft 0.5, reviewed 0.8, validated 1.0. Map those values respectively to low, medium, high. Trigger-only paths are high; hypothetical edges are draft. Explain the underlying status and that confidence is not outcome likelihood.

## Alternatives considered

- Averaging confidence or multiplying it into impact was rejected by the specified semantics.

## Consequences

Confidence labels and rationale must be persisted or reproducible from the immutable path snapshot.

## Evidence

D16 in the continuation brief and D6 in `agent-brief.md`. Human acceptance is pending.
