# Phase 6 Report — Frontend integration

## 1. Objective

Complete the primary product workflow with a tenant-aware React/TypeScript
application connected to the existing API. Deliver event-to-analysis, entity
and dependency management, explainable impact inspection, an accessible graph
alternative, frontend validation states and automated coverage. Stop at the
Phase 6 boundary.

## 2. Work completed

- Replaced the synthetic-only application in `frontend/src/App.tsx` with the
  API-connected workspace. Users can connect with local development identity
  headers, create and edit events, manage triggers, create/edit/archive
  entities, create/edit/activate/deactivate directed dependencies, open events,
  run analyses, browse run history, page through results, and inspect
  explanations and provenance.
- Added the typed API client in `frontend/src/api.ts`, including explicit API
  error details/request IDs and organization-scoped local identity headers.
- Added `frontend/src/ImpactGraph.tsx` for React Flow source → target path
  visualization and an ordered-list alternative for keyboard and assistive
  technology users.
- Added unit/component/accessibility coverage in
  `frontend/src/App.test.tsx`, `frontend/src/ImpactGraph.test.tsx` and
  `frontend/src/api.test.ts`; added the principal Playwright journey in
  `frontend/e2e/workflow.spec.ts`.
- Added Vitest and Playwright configuration, test setup, Vite's same-origin
  `/api` proxy, responsive workspace styling, and ignored generated Playwright
  output in `.gitignore` and `frontend/.prettierignore`.
- Updated `README.md`, `docs/ux/prototype-readme.md`, `docs/viva-notes.md` and
  `docs/progress.md`. The previous synthetic prototype is explicitly
  historical rather than presented as the active product.
- No backend endpoints, database schema, authentication/authorization policy
  or scoring logic were changed. No scoring algorithm is duplicated in the
  frontend.

## 3. Decisions

- The human approved Phase 6 and selected React Flow, approving the
  `@xyflow/react` runtime dependency. It is pinned at `12.12.1`; test tooling
  is development-only. No new ADR was required.
- The frontend uses the existing API contract and Vite's same-origin proxy.
  Local identity headers are explicitly described as development-only; the
  server remains responsible for membership and permission enforcement.
- Event/dependency updates include `expected_updated_at`, matching the API's
  optimistic concurrency contract.
- No new human approval is requested for Phase 6. Phase 7 remains gated on
  review and explicit human approval.

## 4. Verification performed

| Command/check | Result | Evidence |
|---|---|---|
| `npm test` (from `frontend`) | PASS | 11 tests passed across 3 files |
| `npm run lint` (from `frontend`) | PASS | ESLint clean |
| `npm run format:check` (from `frontend`) | PASS | Prettier clean |
| `npm run typecheck` (from `frontend`) | PASS | TypeScript project check passed |
| `npm run build` (from `frontend`) | PASS | TypeScript build and Vite production bundle succeeded |
| `$env:PLAYWRIGHT_USE_CHROME='1'; npm run test:e2e` (from `frontend`) | PASS | 1 Playwright principal-workflow test passed in installed Google Chrome |
| Local seeded-API browser journey using installed Chrome | PASS | Connected through the Vite proxy, created an event, added a trigger, opened it, ran analysis and inspected a source-to-target path; no page errors |
| Initial frontend test iteration | FAIL, resolved | Expectations were updated for the event's refreshed concurrency token and for the independent relationship label field; final suite passes |
| Initial format check with generated Playwright output | FAIL, resolved | Added Playwright outputs to ignore lists; final `npm run format:check` passes |
| Backend full suite, live PostgreSQL, Docker/Compose, production auth, secret scan | NOT RUN | No backend implementation changed; those live/security checks are outside the verified Phase 6 frontend run |

The local browser journey used a temporary seeded SQLite database and
development-only local identity. The API and Vite processes were stopped and
the generated database and Playwright results were removed after verification.

## 5. Test results

- Tests run: frontend Vitest suite and Playwright principal journey.
- Passed: 11 unit/component/API/accessibility tests; 1 Playwright test.
- Failed: 0 in final runs. Two test expectations failed during development
  before being corrected; final runs passed.
- Skipped: 0.
- Coverage: not measured.
- Known gaps: no automated browser matrix beyond installed Chrome; no
screen-reader study or human usability testing; no backend suite rerun during
this frontend-only phase.

## 6. Security and data integrity

- Tenant isolation: the UI sends the selected local user and organization
  identifiers to the existing API. The server continues to validate active
  membership and scopes records; no client-side organization switch or
  authorization decision was added. Tenant-isolation tests were not rerun
  during this frontend-only phase.
- Authorization: existing API permissions remain authoritative. The
  connection screen states local headers are not production sign-in.
- Secret scan: NOT RUN. No secrets or credentials were added.
- Dependency/container scan: NOT RUN for Phase 6. The existing project risk
  register records 10 moderate development-tool dependency findings through
  `minimatch`; no forced dependency downgrade was made. No container was
  introduced or built.
- Audit-log checks: no backend mutations were introduced. Existing event,
  entity, dependency and analysis APIs remain responsible for auditing.
- Unresolved concern: production identity remains undecided. The UI has not
  been reviewed with real users; Phase 2's human-owned research and Figma
  deliverables remain outstanding.

## 7. Evidence integrity

- Evidence produced: final frontend checks listed above; an actual local
  browser/API workflow; source, tests and report in the repository.
- Evidence still TODO(human): Phase 2 interviews, consented research,
  human-owned Figma prototype and task-based usability findings.
- The local browser test used deterministic synthetic seed data only.
- No claim is made about production authentication, live PostgreSQL behavior,
  production accessibility conformance, CI, Docker, cloud deployment,
  performance benchmarks or validated UX.

## 8. Deviations and blockers

- No material deviation from the approved Phase 6 scope.
- React Flow was added only after the human explicitly selected it. Vitest and
  Playwright were added as development dependencies to satisfy the phase's
  component/accessibility and principal-journey test requirements.
- The local end-to-end integration used SQLite and development identity;
  PostgreSQL and production authentication remain unverified.
- Blockers: Phase 2 human evidence and Figma work; development dependency
  audit findings remain as recorded in `docs/progress.md`.

## 9. Progress file

`docs/progress.md` records:

- Done: Phase 6 implementation and verification summary.
- In progress: human-owned Phase 2 research/Figma and Phase 6 review.
- Next: Phase 7, only after explicit approval.
- Blockers: Phase 2 evidence, known development dependency findings, and
  outstanding live infrastructure verification.
- Verification commands/results: frontend test, lint, formatting, type-check,
  build, Playwright and local browser journey.
- Decisions/ADRs: React Flow selection approval and existing API/auth boundary.
- Current branch: `feature/frontend-integration`; see `git log -1` for the
  local Phase 6 commit.

## 10. Human review required

- Review `docs/reports/phase6-report.md` and the event → trigger → analysis
  flow, including optimistic-concurrency handling for event/dependency edits.
- Inspect the React Flow view and keyboard-accessible ordered-list alternative.
- Confirm the local-auth messaging and existing server-owned organization
  boundary are clear.
- Supply and review Phase 2 interviews, Figma and usability evidence when
  available.
- Explicitly approve Phase 7 before scenario implementation begins.

## 11. Phase exit assessment

- Exit criteria met: YES.
- Evidence-backed explanation: a user completed the event-to-analysis journey
  through the real local API; the graph and list derive from source → target
  API provenance; result explanations are rendered from API output; final
  component/API/accessibility tests, Playwright test, lint, formatting,
  type-check and production build passed. Scoring remains exclusively in the
  backend. Phase 2 human validation and production infrastructure are explicit
  limitations, not Phase 6 claims.
- Recommended next phase: Phase 7 — Scenario simulation and comparison, after
  human review and explicit approval.

STOP HERE. Do not begin Phase 7 until the human explicitly approves.
