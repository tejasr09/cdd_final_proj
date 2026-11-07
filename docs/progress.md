# Ripple Effect — Project Progress

- Last updated: 2026-11-07
- Current phase: Phase 2 — agent-preparation deliverables complete; human-led work pending
- Current branch: `feature/ux-preparation`
- Current commit: Phase 1 base `87f525a`; Phase 2 handoff commit is recorded in `git log -1`
- Overall status: Phase 2 UX preparation is documentation-only and partial; no interviews or Figma prototype have been completed

## Done

- Phase 1 foundation is implemented and reported in `docs/reports/phase1-report.md`; its Docker-runtime and dependency-audit caveats remain open.
- Human approved Phase 2 agent-preparation scope on branch `feature/ux-preparation`; no Phase 3 work is authorized.
- Prepared Phase 2 UX documentation in `docs/ux/`: interview guide/consent reminder, anonymized notes template, hypothesis personas, journey-map template, proposed IA and task flows, low-fidelity screen requirements, Figma checklist, and usability-test script.
- Added `docs/reports/phase2-report.md`, which records scope, verification, limitations, and the partial exit assessment.

## In progress

- Human-led Phase 2 research: recruit participants, obtain appropriate consent, conduct interviews, and record actual evidence.
- Human-owned Figma prototype and task-based testing; provide screenshots/export and actual results for review and synthesis.

## Ambiguity register

| ID | Open question | Recommended default | Status |
|---|---|---|---|
| A-01 | Is this the intended repository root; what is the integration branch? | Treat this folder as a new project root; preserve files; confirm before Git initialization | Resolved: confirmed; initialized `feature/phase1-foundation` |
| A-02 | Team size and PR reviewers? | Feature branches and at least one human review per PR; avoid complex Gitflow for a small team | TODO(human) |
| A-03 | Production identity provider? | Local/test adapter first; production provider undecided | TODO(human) |
| A-04 | Frontend styling system? | Tailwind proposal, subject to approval | TODO(human) |
| A-05 | Python/Node lab constraints? | Verify maintained compatible releases; observed Python 3.11.9 and Node 24.14.1 are candidates only | Runtime observed; team constraints TODO(human) |
| A-06 | Package managers? | npm + uv proposal; uv is unavailable and has not been installed | Resolved: npm + uv approved; uv 0.13.7 installed, Scripts directory not on PATH by default |
| A-07 | Is Azure ACR/ACI available and budget-approved? | Local-first; human-operated cloud runbooks only | TODO(human) |
| A-08 | Is Docker Hub also required? | ACR remains target; use Docker Hub only if course requires | TODO(human) |
| A-09 | Which UX participants are available? | Voluntary students/coordinators with consent; hypotheses remain unvalidated | TODO(human) |
| A-10 | Is real institutional data needed? | Synthetic data only | Accepted default |
| A-11 | Should Jenkins/Kubernetes be pursued? | Defer until MUST criteria and ACI milestone are complete | Accepted default |
| A-12 | Course report/presentation format? | Follow official rubric if supplied; otherwise Section 15 | TODO(human) |

## Next — ordered backlog and acceptance criteria

| Order | Work item | Acceptance criteria |
|---|---|---|
| Next | Complete Phase 2 human-led research and prototype work | Clickable prototype covers event creation → analysis → impact inspection → scenario → comparison; genuine findings and design decisions documented; no fabricated evidence |
| Later, after Phase 2 review and explicit approval | Phase 3 data and tenancy | Migrations build a fresh database; membership and tenant constraints pass isolation tests; state changes are audited |
| Later | Phase 4 API | CRUD/lifecycle/trigger endpoints validate and authorize correctly; pagination, errors, audit and OpenAPI snapshot are tested |
| Later | Phase 5 engine | Required test matrix passes, 32.256 example reproduced, output deterministic, ceilings visibly mark incomplete runs |
| Later | Phase 6 frontend | Event-to-analysis journey works; graph direction and accessible list agree; impact explanations are inspectable |
| Later | Phase 7 scenarios | Scenario/baseline comparisons work and isolation tests prove live records unchanged |
| Later | Phase 8 delivery | Local Compose is reproducible and approved CI checks pass; image/build evidence is genuine |
| Later | Phase 9 cloud | Human-approved ACR/ACI deployment uses recorded immutable digest; health, rollback and cleanup are verified |
| Later | Phase 11 release hardening | Security, tests, accessibility, docs and evidence are reviewed; unmet criteria/limitations are explicit |
| Optional | Phase 10 Jenkins/Kubernetes | Only after baseline and explicit approval; optional work does not delay required delivery |

## Blockers

- Docker CLI is installed but the Docker daemon is unavailable, so Compose startup and image builds could not be verified.
- The npm audit reports 10 moderate findings for the development-tool dependency chain through `minimatch` (`>=7.0.0 <11.0.1`). A non-breaking audit fix was unavailable; npm proposed a breaking ESLint downgrade, which was not forced.
- Production authentication provider remains intentionally undecided; no auth/session behavior is implemented yet.
- Human interviews, consent, actual UX findings, Figma prototype, and usability results do not exist yet; Phase 2 is partial until supplied and reviewed.
- CI workflows, cloud resources, and database integration remain future-phase/human work.

## Verification

| Date | Command/check | Result | Notes |
|---|---|---|---|
| 2026-11-07 | Read both briefs and existing docs | PASS | Combined specification reviewed |
| 2026-11-07 | Workspace inventory | PASS | No application source/manifests found |
| 2026-11-07 | Git status/branch/log | NOT RUN | Git reported not a repository |
| 2026-11-07 | Toolchain version inspection | PASS | Python 3.11.9; Node 24.14.1; npm 11.11.0; Docker 29.8.2; Git 2.53.0.windows.2; uv unavailable |
| 2026-11-07 | ADR structure validation | PASS | ADR-001 through ADR-031 present with required sections |
| 2026-11-07 | Frontend lint/typecheck/format/build | PASS | Vite production build succeeded |
| 2026-11-07 | Backend tests/lint/format | PASS | 2 pytest cases passed; Ruff clean |
| 2026-11-07 | API live health/OpenAPI smoke | PASS | Liveness, readiness, and OpenAPI responded |
| 2026-11-07 | Browser UI smoke | PASS | Integrated browser loaded page and exposed semantic headings/notice |
| 2026-11-07 | Docker Compose config | PASS | Config parsed; daemon not available for actual startup |
| 2026-11-07 | npm audit, production dependencies | PASS | 0 vulnerabilities |
| 2026-11-07 | npm audit, all frontend dependencies | FAIL | 10 moderate development dependency findings via minimatch; see report |
| 2026-11-07 | `uv audit --locked` | PASS | OSV lookup: no known vulnerabilities/adverse statuses in 21 packages |
| 2026-11-07 | Docker daemon and image startup | NOT RUN | Docker Desktop Linux engine pipe unavailable |
| 2026-11-07 | Phase 2 UX documentation review | PASS | Confirmed requested agent-preparation deliverables are present; docs-only review, no UX validation claimed |
| 2026-11-07 | UX interviews, Figma prototype, task-based usability testing | NOT RUN | Human-led Phase 2 work; no participants, prototype, or results supplied |

## Decisions and ADRs

- Accepted: ADR-001 through ADR-031; user approved proposed ADRs for Phase 1.
- Runtime identity provider remains unselected, as specified by the auth adapter decision.
- npm + uv package manager selection accepted; uv 0.13.7 installed in the user Python tool directory.
- Detailed phase findings: `docs/reports/phase-0-report.md`.
- Phase 1 evidence: `docs/reports/phase1-report.md`.
- Phase 2 agent-preparation scope approved; human-led research and Figma ownership remain with the human.
- Phase 2 evidence and limitations: `docs/reports/phase2-report.md`.

## Risk register

| Risk | Impact | Mitigation | Owner/status |
|---|---|---|---|
| Development dependency audit finding | Moderate glob-matching DoS advisory in tooling chain | No semver-compatible fix currently available; retain visible finding, re-audit before release, do not force downgrade | Engineering, open |
| Docker daemon unavailable | Container build/start acceptance cannot be verified locally | Start Docker Desktop and run documented Compose commands before approving delivery phase | TODO(human), open |
| Production auth provider undecided | Cannot configure production identity safely | Keep adapter boundary; select provider and deployment config with human approval | TODO(human), planned |
| Azure subscription/cost/registry needs unknown | Deployment plan may be unusable or incur cost | Human confirms availability and budget; no cloud actions by agent | TODO(human), open |
| UX evidence unavailable | Design could be mistaken for validated research | Keep personas as hypotheses and mark research TODO(human) | Team, open |
| Dependency path explosion | Resource exhaustion or incomplete analysis | Enforce deterministic node/path ceilings and visible incomplete status | Engineering, planned |
| Tenant leakage or scenario mutation | Cross-organization disclosure or live-data corruption | Composite constraints, scoped access, isolation tests | Engineering, planned |

## Human actions pending

- Conduct and document Phase 2 interviews with suitable participants, appropriate consent, anonymized notes, and evidence-backed findings.
- Create/own the clickable Figma prototype, conduct task-based tests, and provide actual frames/results for review.
- Review `docs/reports/phase2-report.md` and complete the Phase 2 human deliverables before requesting a phase-exit review.
- Start Docker Desktop and verify Compose startup when available.
- Revisit the minimatch development-tool advisory before release.
- Do not begin Phase 3 until Phase 2 exit is reviewed and explicitly approved.

## Evidence index

- `docs/reports/phase-0-report.md`
- `docs/adr/`
- `docs/viva-notes.md` (all topics currently planned)
- `docs/ux/` contains preparation templates only; no interview, Figma, or usability-test evidence exists.
- Phase 1 code/test/API evidence is recorded in `docs/reports/phase1-report.md`; no CI, cloud, or benchmark evidence is claimed.

## Session handoff

- Last completed task: Phase 2 agent-preparation documentation on `feature/ux-preparation`.
- Exact next task: human-led Phase 2 interviews and clickable-prototype/testing work; then provide the actual materials for review.
- Files to read first: both root-level briefs, this file, `docs/reports/phase2-report.md`, and the relevant `docs/ux/` templates.
- Commands to verify: documented frontend/backend checks; `docker compose up --build` after Docker daemon starts.
- Approval needed: Phase 2 human evidence and explicit approval before Phase 3; GitHub Actions, remote operations, and cloud changes retain separate approval gates.
