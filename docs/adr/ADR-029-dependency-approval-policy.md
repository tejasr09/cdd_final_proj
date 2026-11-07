# ADR-029: Runtime dependency approval and evidence

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D29 and Section 2.1 of `agent-brief.md`

## Context

Dependencies affect maintenance, licensing, security, reproducibility, and project approval gates.

## Decision

Prefer a small maintained dependency set and lock direct dependencies. Before adding a runtime package, report purpose, current stable version, license, maintenance evidence, security posture, alternatives, and why existing tools are insufficient. Obtain explicit human approval. Do not add a graph database, broker, cache, ML framework, or microservice without a justified requirement.

## Alternatives considered

- Adding packages without a verified need or approval was rejected by the project operating rules.

## Consequences

No package installation or runtime manifest change is authorized by this ADR. Package choices require per-dependency approval.

## Evidence

D29 in the continuation brief and Section 2.1 in `agent-brief.md`. Human acceptance is pending.
