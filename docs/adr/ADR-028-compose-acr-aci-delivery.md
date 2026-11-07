# ADR-028: Compose locally and ACR/ACI as cloud target

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D28

## Context

The project needs reproducible local containers and a syllabus-aligned cloud demonstration while preserving human control of cloud changes.

## Decision

Use Docker Compose locally with web, API, and database services. Target ACR image publishing and ACI deployment for the cloud demonstration; AKS remains optional and does not replace ACI. Promote the same immutable image digest. Cloud resource creation and deployment remain human-executed and require explicit approval.

## Alternatives considered

- AKS as the sole target was rejected because ACI is required by the brief and AKS is optional.

## Consequences

Local container behavior can be validated independently. No cloud account, budget, or deployment is assumed.

## Evidence

D28 in the continuation brief and Appendix E. Human acceptance/account availability is pending.
