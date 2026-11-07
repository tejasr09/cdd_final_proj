# ADR-026: Scope and caveats for result exports

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D26

## Context

Users may need to take analysis results outside the application without losing context or tenant boundaries.

## Decision

In-app run viewing is required. CSV export is a SHOULD; printable reports are a COULD unless course/final criteria require them. Any export must be tenant-scoped, audited, and include run ID, timestamp, algorithm version, configuration, limitations, and an estimate-not-probability statement. Avoid unnecessary internal IDs.

## Alternatives considered

- Uncontextualized score-only exports were rejected because they could misrepresent estimates.

## Consequences

Exports remain lower priority than required run viewing and need audit/tenant tests if implemented.

## Evidence

D26 in the continuation brief. Human acceptance is pending.
