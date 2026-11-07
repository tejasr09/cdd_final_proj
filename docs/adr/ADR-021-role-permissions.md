# ADR-021: Default organization role permissions

- Status: accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief-continuation.md`, D21

## Context

The application needs a consistent server-enforced permission baseline for four user roles.

## Decision

Use the D21 defaults: administrators manage organization/members/reference data and operational records; operations coordinators manage operational records and live/scenario analysis; department coordinators read the model/events/results and may propose dependency edits if supported; analysts read and run/compare scenarios but do not modify live operational data by default. Enforce these permissions server-side.

## Alternatives considered

- UI-only hiding was rejected because it does not enforce access.

## Consequences

Create an endpoint-to-role permission matrix and tests. Human confirmation of the role model is pending; finer permissions require documentation and tests.

## Evidence

D21 in the continuation brief and Appendix F role-model approval requirement. Human acceptance is pending.
