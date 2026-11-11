# ADR-032: Use the pinned Python Alpine API base

- Status: accepted
- Date: 2026-11-11
- Decision owners: TODO(human)
- Source: Phase 8 API image scan remediation

## Context

The Python 3.11 Debian slim API image had Debian OS advisories with no fixed
versions available from its configured repositories. A Debian 12 comparison
had more findings. Phase 8 requires an API image that passes full-severity
vulnerability and secret scans without suppressions or threshold changes.

## Decision

Use the official Python 3.11 Alpine image pinned to
`sha256:bb1d70c1df30d8ee1e05214dbe82d6cdfd29833c1f47ce917f20991aca93acaa`.
Upgrade available Alpine packages during the image build. Keep the existing
locked `uv` dependency installation, non-root runtime, entrypoint, migrations,
optional local seed, port, and health check.

## Alternatives considered

- Keep Debian and wait for upstream package fixes: does not satisfy the
  current Phase 8 scan gate.
- Use an older Debian 12 base: rejected because the comparison had more
  findings, including critical findings.
- Suppress findings or lower scan severity: rejected because it hides the
  reported risk and violates the Phase 8 acceptance criteria.

## Consequences

The pinned base makes the Python OS layer reproducible. `apk upgrade` still
applies available repository security updates at build time, so rebuilt image
contents may change as Alpine publishes fixes. Python 3.11 remains compatible
with the project's `>=3.11` requirement. The locked dependencies installed
successfully on musl, including `psycopg-binary`; PostgreSQL-backed API
verification and full image scans are recorded in the Phase 8 report.

## Evidence

The candidate image passed Trivy 0.74.0 vulnerability and secret scanning at
all severities and a fresh Compose health/smoke check. The production-image
rebuild and CI results remain to be recorded in the Phase 8 report.
