# Ripple Effect — Agent Operating Instructions

## Source of truth
- Read `agent-brief.md` and `agent-brief-continuation.md` together; they form the complete build brief.
- Follow approved decisions and phase gates in those files.
- Read `docs/progress.md` and the current phase before resuming.
- If the brief and repository disagree, report the conflict; do not silently rewrite either.

## Autonomy
- Work only inside the project workspace.
- Read-only inspection is allowed before kickoff approval.
- After approval, local edits, tests, formatters, local branches and local commits are allowed.
- Ask before adding runtime dependencies or GitHub Actions, changing auth/authorization/tenant isolation, using network access beyond approved registries/docs, or performing remote Git operations.
- Never deploy, create/change/delete cloud resources, change GitHub settings/secrets, use sudo, force-push shared branches, disable checks, or expose secrets.
- Never commit directly to `main` or `develop`.

## Engineering workflow
- Restate task and acceptance criteria.
- Write tests first for graph/authorization logic.
- Make small, reviewable changes.
- Run relevant format, lint, type-check, test and build commands.
- Fix root causes; do not suppress failures.
- Update docs, migrations, OpenAPI and `docs/progress.md`.
- Use Conventional Commits on `feature/<area>-<slug>` branches.

## Product invariants
- A dependency source -> target means a change in source may affect target.
- Scores are heuristic estimates, never probabilities.
- Preserve path provenance, deterministic aggregation and bounded cycle-safe traversal.
- Confidence measures dependency review quality, not likelihood.
- Scenarios must not mutate live records.
- Every tenant-owned record and reference is organization-scoped.
- Non-members receive 404 for tenant-owned resources; unauthorized members receive 403.
- Every state-changing endpoint is audited.

## Evidence integrity
- Never fabricate interviews, personas as validated facts, usability scores, tests, benchmarks, screenshots, CI or cloud results.
- Mark missing human evidence as TODO(human).
- Record copied material and its licence.
- Include AI-assistance disclosure in PR descriptions according to course policy.

## Phase discipline
- Work one approved phase at a time.
- Stop at the end of each phase and submit Appendix H's phase report.
- Do not proceed until the human explicitly approves.
