# Ripple Effect — Appendix G Evidence Index

Updated: 2026-11-14
Revision under review: `feature/phase11-release-hardening`, based on `95b3f22`

Statuses follow Appendix G: `PASS`, `FAIL`, `NOT RUN`, or `NOT APPLICABLE`.
“PASS” means the stated requirement has evidence; it does not imply production
readiness or human release approval. Local evidence is not cloud evidence.

| ID | Status | Evidence and scope |
|---|---|---|
| G-01 | PASS | Local setup commands and safety notes are in [`README.md`](../README.md). Compose startup was verified from this workspace; a fresh clone on a separate PC was not tested. |
| G-02 | PASS | Compose API and web containers became healthy; smoke checks passed. See [`docs/progress.md`](./progress.md), 2026-11-14 verification entries. |
| G-03 | PASS | Fresh SQLite Alembic upgrade and schema check passed; Compose PostgreSQL also migrated during startup. |
| G-04 | PASS | The seeded PostgreSQL instance returned North Campus and City Transport data; current live analysis used the seeded North Campus event. |
| G-05 | PASS | Composite tenant constraints are covered by [`backend/tests/test_tenancy.py`](../backend/tests/test_tenancy.py) and [`backend/tests/test_migrations.py`](../backend/tests/test_migrations.py). |
| G-06 | PASS | Role and membership authorization tests are in [`backend/tests/test_tenancy.py`](../backend/tests/test_tenancy.py) and [`backend/tests/test_api.py`](../backend/tests/test_api.py); the complete backend suite passed. |
| G-07 | PASS | Event lifecycle and trigger association API/UI tests passed; the main browser workflow passed in [`frontend/e2e/workflow.spec.ts`](../frontend/e2e/workflow.spec.ts). |
| G-08 | PASS | Entity lifecycle/archive behavior is covered in [`backend/tests/test_api.py`](../backend/tests/test_api.py) and [`frontend/src/App.test.tsx`](../frontend/src/App.test.tsx). |
| G-09 | PASS | Directed dependency validation and source-to-target behavior are covered by [`backend/tests/test_api.py`](../backend/tests/test_api.py) and [`backend/tests/test_engine.py`](../backend/tests/test_engine.py). |
| G-10 | PASS | The 32.256 (32.3 displayed) engine example is asserted in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py). |
| G-11 | PASS | Cycle safety and multiple paths are covered in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py). |
| G-12 | PASS | Depth, edge, and path bounds are tested in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py). |
| G-13 | PASS | Confidence semantics and explanatory output are tested in [`backend/tests/test_engine.py`](../backend/tests/test_engine.py) and [`frontend/src/App.test.tsx`](../frontend/src/App.test.tsx). |
| G-14 | PASS | Incomplete-run limit status is covered by engine/API/UI tests, including [`backend/tests/test_engine.py`](../backend/tests/test_engine.py) and [`frontend/src/App.test.tsx`](../frontend/src/App.test.tsx). |
| G-15 | PASS | Snapshot and algorithm-version persistence are covered in [`backend/tests/test_api.py`](../backend/tests/test_api.py) and [`backend/tests/test_migrations.py`](../backend/tests/test_migrations.py). |
| G-16 | PASS | Scenario isolation and live-record immutability are asserted in [`backend/tests/test_api.py`](../backend/tests/test_api.py). |
| G-17 | PASS | Scenario/baseline comparisons are covered by backend scenario tests and the primary UI workflow tests; no production scenario application is claimed. |
| G-18 | PASS | Audit creation is covered by API tests and the live PostgreSQL analysis check; the audit count increased from 0 to 1. |
| G-19 | PASS | The impact graph provides a keyboard-accessible ordered-list alternative in [`frontend/src/ImpactGraph.tsx`](../frontend/src/ImpactGraph.tsx), tested in [`frontend/src/ImpactGraph.test.tsx`](../frontend/src/ImpactGraph.test.tsx). A human screen-reader/usability review has not been performed. |
| G-20 | PASS | Playwright primary workflow: 1 test passed using installed Chrome. See [`docs/progress.md`](./progress.md), 2026-11-14 verification entries. |
| G-21 | PASS | Compose build/start, three healthy services, HTTP health checks, and smoke script passed locally; only loopback ports are published. |
| G-22 | NOT RUN | No pull request or remote CI run was triggered for this branch. Remote Git operations were not authorized. |
| G-23 | PASS | Local tags and version/SHA tagging plus registry digest inspection guidance are in [`README.md`](../README.md). No registry image or digest is claimed. |
| G-24 | NOT RUN | No ACR publication, ACI deployment, or cloud health check was performed. See [`docs/reports/phase9-report.md`](./reports/phase9-report.md). |
| G-25 | PASS | npm audit reported 0 findings; uv audit found no known vulnerabilities/adverse statuses in 33 packages; Trivy reported 0 image vulnerabilities. The current Trivy secret summaries rendered `-`, so no definitive zero-secret claim is made. |
| G-26 | NOT RUN | Human interviews and validated UX findings remain TODO(human); no research was fabricated. |
| G-27 | NOT RUN | A human-owned Figma prototype and evidence have not been supplied. |
| G-28 | PASS | Core concepts, examples, implementation links, test evidence, and limitations are summarized in [`docs/viva-notes.md`](./viva-notes.md). |
| G-29 | PASS | Limitations and future work are documented in [`docs/limitations.md`](./limitations.md). |
| G-30 | NOT RUN | AI assistance is disclosed in the Phase 11 report. No PR was created, and course-specific PR disclosure requirements were not available to verify. |

## Security and operations notes

- The local Compose stack was tested using synthetic fixtures. One live
  cross-organization lookup returned HTTP 404; this does not replace a
  production authorization review or concurrency stress test.
- Scores are heuristic estimates, not probabilities. The measured graph
  performance numbers are local observations, not service-level objectives.
- Public ingress remains disabled. Production identity, TLS ingress, Azure
  deployment, remote CI for this branch, and human release approval remain
  outstanding.
- Secret-scanner output was treated conservatively: a `-` summary is not
  evidence of a clean scan.
