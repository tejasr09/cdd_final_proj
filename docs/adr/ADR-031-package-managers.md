# ADR-031: Frontend and backend package managers

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)

## Context

This workspace has no application manifests or lockfiles. Appendix F recommends preserving existing lockfiles, or using npm and uv for a new repository when compatible.

## Decision

Propose npm for the frontend and uv for the Python backend, subject to confirmation of team-machine compatibility and approval before any installation. The observed environment has Node 24.14.1 and npm 11.11.0, but no `uv` executable. No package manager was installed and no dependency manifest was created in Phase 0.

## Alternatives considered

- Preserving existing project managers is inapplicable to the currently observed folder because no project manifests exist.
- Installing a missing tool before the team confirms the workflow was deferred.

## Consequences

Phase 1 cannot create backend lockfiles until the toolchain choice and `uv` availability are resolved.

## Evidence

Appendix F, question 6, and read-only toolchain inspection on 2026-11-07. Human acceptance is pending.
