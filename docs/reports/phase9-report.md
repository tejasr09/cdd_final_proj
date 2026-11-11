# Phase 9 Report — Azure ACR and ACI deployment preparation

Date: 2026-11-12
Branch: `feature/phase9-acr-aci`
Base commit: `c5d4715` (Phase 8 closure)

## 1. Objective

Prepare Bicep infrastructure/deployment templates, a human-operated runbook,
and local validation for the required Azure Container Registry (ACR) and
Azure Container Instances (ACI) workflow. The human selected an existing
PostgreSQL service. No Azure account setup, resource creation, image
publishing, or deployment is within agent execution scope.

## 2. Work completed

- Added draft `infra/azure/provision.bicep` for Premium ACR, a
  user-assigned managed identity, and registry-scoped `AcrPull`.
- Added draft `infra/azure/aci.bicep` for digest-pinned API/web images, a
  secure PostgreSQL URL parameter, health probes, and public ingress disabled
  by default.
- Added placeholder-only `infra/azure/aci.parameters.example.json` and
  `.gitignore` exclusions for local parameter files.
- Updated `frontend/Dockerfile` and `frontend/nginx.conf` to render the
  Nginx config from a template with a filtered `API_UPSTREAM`; the Compose
  default remains `api:8000`, while the ACI template supplies
  `127.0.0.1:8000`.
- Added the human-only
  [`phase9-acr-aci.md`](../runbooks/phase9-acr-aci.md) runbook covering
  account/cost checks, identity, image digest capture, secure parameter
  handling, what-if, deployment, health verification, rollback, cleanup and
  troubleshooting.
- Added [`ADR-033`](../adr/ADR-033-azure-container-deployment.md), which
  records the human's Bicep selection and the proposed resource design; updated
  [`deployment.md`](../architecture/deployment.md), `README.md`,
  [`viva-notes.md`](../viva-notes.md), and [`progress.md`](../progress.md).
- The IaC selection is Bicep, confirmed by the human on 2026-11-11.
  Public ingress remains disabled because production authentication and TLS
  ingress are not implemented.

## 3. Decisions

- Existing PostgreSQL is the selected database target; no database resource is
  provisioned by this work.
- Bicep is the human-selected IaC tool, recorded in ADR-033. Resource design
  and provisioning still need human review.
- The templates use Premium ACR to support the proposed ACI managed-identity
  pull design. Current cost and institutional eligibility must be reviewed by
  the human before provisioning.
- No ACR admin credentials are enabled. ACI uses a registry-scoped pull
  identity. No GitHub deployment workflow or repository secret was added.
- Public ingress defaults to false. Enabling it requires production
  authentication and TLS ingress to be implemented and separately reviewed.
- No remote push, registry login/push, Azure sign-in, `what-if`, resource
  creation/deletion, or deployment was performed.

## 4. Verification performed

| Command/check | Result | Evidence |
|---|---|---|
| Bicep CLI (`0.49.2`) `bicep build .\infra\azure\provision.bicep --stdout` | PASS | Template compiled successfully; output was not written to the repository. |
| Bicep CLI (`0.49.2`) `bicep build .\infra\azure\aci.bicep --stdout` | PASS | Template compiled successfully; output was not written to the repository. |
| Azure CLI availability probe (`Get-Command az`) | NOT AVAILABLE | Azure CLI is not installed; no Azure validation or sign-in was performed. |
| `docker info --format '{{.ServerVersion}}'` | PASS | Started Docker Desktop Linux engine per prior user authorization; server version `29.9.3`. |
| `docker compose --env-file .env.example config --quiet` | PASS | Compose configuration parsed successfully. |
| Parse `infra\azure\aci.parameters.example.json` with PowerShell `ConvertFrom-Json` | PASS | Placeholder parameter example is valid JSON. |
| `git diff --check` | PASS | No whitespace errors in tracked changes. |
| `docker compose --project-name ripple-phase9-agent-check --env-file .env.example up --build --detach --wait --wait-timeout 240` | PASS | API and web images built; PostgreSQL, API and web reached healthy state in the isolated project. |
| `python backend\scripts\smoke_compose.py` | PASS | API readiness, web response, and web-to-API proxy passed. |
| `docker run --rm -e API_UPSTREAM=127.0.0.1:8000 ripple-effect-web:local nginx -T` | PASS | ACI upstream rendered correctly, Nginx config parsed, and `$host` remained unsubstituted. |
| Trivy 0.74.0 `image --vuln-type os,library --scanners vuln,secret --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL --exit-code 1` | PASS | Ran from `aquasec/trivy:0.74.0` against `ripple-effect-api:local` and `ripple-effect-web:local`; each reported 0 vulnerabilities and 0 secrets. |
| Frontend `npm run lint`, `npm run format:check`, `npm run typecheck`, `npm test -- --pool=forks --maxWorkers=1`, `npm run build` | PASS | 12 tests passed; all quality commands succeeded. |
| Backend `.\.venv\Scripts\python.exe -m pytest` (from `backend`) | PASS | 88 tests passed. |
| Backend `.\.venv\Scripts\ruff.exe check app tests scripts` and `.\.venv\Scripts\ruff.exe format --check app tests scripts` (from `backend`) | PASS | All checks passed; 20 files already formatted. |
| Isolated Compose cleanup (`docker compose --project-name ripple-phase9-agent-check --env-file .env.example down --volumes --remove-orphans`) | PASS | Removed only this test stack, network, and temporary PostgreSQL volume. |
| Azure `what-if` | NOT RUN | Azure CLI/account is absent and cloud operations are human-only. Both Bicep templates compiled locally. |
| Phase 9 GitHub CI | NOT RUN | No push, pull request, or CI run was initiated; the edited Nginx image change still needs approved-branch CI. |

## 5. Test results

- Tests run: 12 frontend tests, 88 backend tests, frontend quality/build
  checks, backend Ruff checks, Compose startup/smoke, Nginx config rendering,
  and Trivy image scans.
- Passed: all checks listed above; both scanned images had zero findings at
  all configured severities and zero secrets.
- Failed, resolved: an initial backend test invocation from the repository
  root failed collection because `app` was not on the import path; rerunning
  from `backend` passed. An initial Trivy container name typo was corrected
  from `aquasecurity/trivy` to the cached `aquasec/trivy`; the corrected scans
  passed.
- Passed: both Bicep templates compiled with Bicep CLI 0.49.2.
- Skipped: Azure validation/deployment, registry publishing, and branch CI.
- Coverage: not measured.
- Known gaps: actual ACI probes, external PostgreSQL TLS/reachability, registry
  image digests, cloud costs, and
  GitHub CI on this branch remain unverified.

## 6. Security and data integrity

- Tenant-isolation and authorization code were not changed.
- No actual credential, token, or database URL was added; the parameter
  example contains placeholders only and local parameter files are ignored.
- The ACI template marks `DATABASE_URL` secure, disables local auth and demo
  seeding, and defaults public ingress off.
- The locally rebuilt API and web images passed the Phase 8 CI-equivalent
  Trivy 0.74.0 scan configuration: OS/library vulnerabilities and secrets at
  UNKNOWN through CRITICAL severities, with no ignore list or lowered
  threshold. Each image reported zero vulnerabilities and zero secrets.
- Local container health, proxy, config rendering and image scans were
  verified. No Azure deployment or runtime security check was performed.
  Production authentication and TLS ingress remain blockers to public access.
- Audit logging and application authorization behavior were not modified.

## 7. Evidence integrity

- Evidence produced: source templates, example parameters, documentation, and
  a human-operated deployment runbook. Phase 8 evidence remains linked in its
  own report.
- Evidence still TODO(human): Azure eligibility, budget alerts, region,
  provisioning, ACR image digests, ACI health, database connectivity, rollback,
  cleanup, and a live smoke/browser journey after authentication and TLS exist.
- Phase 2 interview/Figma/usability evidence remains TODO(human).
- No claim is made that images were published, CI passed for this branch, or
  Azure deployment succeeded.

## 8. Deviations and blockers

- Phase 9 is partial because Azure CLI and cloud access are unavailable, so no
  Azure validation/deployment could be performed. Both Bicep templates now
  compile successfully with Bicep CLI 0.49.2. The Docker Linux engine was
  started and the changed image was locally built, smoke-tested and scanned.
- GitHub CI on the Phase 9 branch was not run because it would require an
  authorized remote push or pull request.
- Account eligibility, region, Premium ACR/ACI cost, publisher permissions,
  and external database TLS/network reachability require human decisions.
- The project has no production identity provider or TLS ingress. Public
  ingress must remain disabled until a separately reviewed solution exists.
- The deployment and cloud-changing commands are documented for human use
  only, as required by the brief.

## 9. Progress file

[`docs/progress.md`](../progress.md) records Phase 9 as in progress, the branch
and base commit, completed work, Azure CLI limitation, verification
status, human decisions, blockers, and the next actions.

## 10. Human review required

1. Review the resource design and confirm Azure eligibility, region, cost,
   budget alerts, and resource ownership before provisioning.
2. Confirm the approved publisher identity and permissions.
3. Confirm external PostgreSQL TLS settings, firewall/network path, and ACI
   reachability without sharing credentials.
4. Keep public ingress disabled until production authentication and TLS
   ingress have been implemented and approved.
5. After local validation and CI, execute the human-only runbook and provide
   actual cloud verification evidence.

## 11. Phase exit assessment

- Exit criteria met: **NO — PARTIAL**.
- Evidence-backed explanation: both templates compile and the human runbook is
  drafted. Container images were built and locally tested, but the required
  approved ACR images/digests, ACI deployment, cloud health checks, and human
  cloud evidence do not exist yet.
- Human direction on 2026-11-12: pause/close Phase 9 as **PARTIAL** for now and
  begin optional Phase 10. This is an administrative pause, not evidence that
  Phase 9's exit criteria have been met.
- Remaining Phase 9 work: approved-branch CI, ACR publication of versioned
  images with recorded immutable digests, human ACI deployment and health
  evidence, plus cost, rollback, and cleanup review. Resume these when the
  human is ready; no remote or cloud action was taken for this transition.
- Phase 10 kickoff is explicitly approved. Follow the optional scope in the
  build brief; select local Kubernetes and Jenkins runtime approaches before
  implementation.
