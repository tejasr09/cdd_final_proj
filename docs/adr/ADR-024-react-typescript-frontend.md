# ADR-024: React and TypeScript frontend baseline

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D24

## Context

The application requires a typed interactive UI, accessible graph visualization, and separated API access.

## Decision

Use React, TypeScript, and Vite. Use React Flow for graph visualization, Vitest and React Testing Library for component/unit tests, and Playwright for end-to-end tests. Put API calls in a typed service/client layer and do not duplicate impact calculations in React. Tailwind is proposed, subject to human confirmation and dependency review.

## Alternatives considered

- Business logic in React components was rejected because it duplicates domain behavior and impairs independent testing.

## Consequences

The component system and styling choice need approval and compatibility checks before dependencies are added.

## Evidence

D24 in the continuation brief and Appendix F, question 4. Human acceptance is pending.
