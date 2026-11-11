# Phase 10 Report — Advanced DevOps (local Jenkins and Kubernetes)

Date: 2026-11-12
Branch: `feature/phase10-advanced-devops`
Implementation commit: `874ef74`
Base commit: `b469fd4` (Phase 9 preparation)

This is an implementation checkpoint, not a Phase 10 closure report. Phase 10
remains in progress pending the human Jenkins setup and pipeline run.

## 1. Objective

Demonstrate the approved optional DevOps path using Docker Desktop Kubernetes
and a local Jenkins container. Keep the work separate from the human-operated
Phase 9 ACR/ACI deployment, avoid public ingress and cloud credentials, and
preserve the core application's authentication and tenant behavior.

## 2. Work completed

- Added [`Jenkinsfile`](../../Jenkinsfile) for frontend/backend quality checks,
  dependency audits, migrations, and cleanup. It does not publish images or
  deploy to any environment.
- Added the digest-pinned Jenkins image and locked plugins in
  [`infra/phase10/jenkins/`](../../infra/phase10/jenkins/), with Compose bound
  to `127.0.0.1:8081`, a persistent home volume, no Docker socket, and no cloud
  credentials.
- Added [`kubernetes.yaml`](../../infra/phase10/kubernetes.yaml) for local API
  and web Deployments and ClusterIP Services. It uses local demo auth,
  ephemeral SQLite, `imagePullPolicy: Never`, and no Ingress.
- Added [`load-local-images.ps1`](../../infra/phase10/load-local-images.ps1)
  after confirming Docker Desktop's kind node did not automatically see the
  host image tags. The helper is limited to the `docker-desktop` context and a
  single node; it streams and imports the local images into containerd's
  `k8s.io` namespace, verifies both references, and removes its temporary
  archive.
- Added [`ADR-034`](../adr/ADR-034-local-jenkins-kubernetes.md), the
  [Phase 10 runbook](../runbooks/phase10-jenkins-kubernetes.md), and updated
  [`progress.md`](../progress.md) and [`viva-notes.md`](../viva-notes.md).
- Built and started the Jenkins container. It serves `/login` on loopback;
  its setup wizard is intentionally left for the human.
- Applied the Kubernetes manifests, imported both app images, and verified
  that API and web each reached Ready. Web health and the Nginx-proxied API
  readiness check both passed through a loopback port-forward.

## 3. Decisions

- The human selected Docker Desktop Kubernetes and local Jenkins on
  2026-11-12. ADR-034 records the local-only design and security boundaries.
- Kubernetes uses ClusterIP Services, no Ingress, one replica per workload,
  ephemeral SQLite, and local/test authentication. These are demo-only
  settings, not production guidance.
- Jenkins runs trusted local code only. Its initial setup, credentials, and
  job configuration remain human-owned. No Jenkins bootstrap password or
  logs were inspected.
- No remote push, pull request, GitHub CI run, Azure operation, registry
  publication, or cloud deployment was performed.

## 4. Verification performed

| Command/check | Result | Evidence |
|---|---|---|
| `docker compose --project-name ripple-phase10-jenkins -f infra\phase10\jenkins\compose.yml up --build --detach` | PASS | Custom Jenkins image built and container started; Compose reports loopback port `127.0.0.1:8081` and persistent home volume. |
| `Invoke-WebRequest http://127.0.0.1:8081/login` | PASS | Jenkins `/login` returned HTTP 200 after startup. No response body, password, or logs were read. |
| `docker compose --project-name ripple-phase10-jenkins -f infra\phase10\jenkins\compose.yml config --quiet` | PASS | Jenkins Compose configuration parsed successfully. |
| `kubectl apply --dry-run=client -f infra\phase10\kubernetes.yaml` | PASS | Namespace, ConfigMap, Deployments, and Services validated. |
| `.\infra\phase10\load-local-images.ps1` | PASS | Imported `ripple-effect-api:local` and `ripple-effect-web:local` into the `k8s.io` namespace on `desktop-control-plane`; verified both references and removed temporary archives from the host and node. |
| `kubectl rollout status deployment/ripple-api -n ripple-effect --timeout=180s` and web equivalent | PASS | Both deployments rolled out with one Ready replica each. |
| `kubectl port-forward --address 127.0.0.1 -n ripple-effect service/ripple-web 5173:8080`; requests to `/health` and `/api/v1/health/ready` | PASS | Both endpoints returned HTTP 200. The port-forward was stopped after testing. |
| `kubectl exec -n ripple-effect deployment/ripple-web -- printenv API_UPSTREAM`; `kubectl get ingress -n ripple-effect` | PASS | API upstream is `ripple-api:8000`; no Ingress resource exists. |
| Frontend `npm ci`; `npm run lint`, `npm run format:check`, `npm run typecheck`, `npm test -- --run --pool=forks --maxWorkers=1`, `npm audit`, `npm run build` | PASS | 12 tests passed; all quality checks passed; npm audit reported 0 vulnerabilities; production build succeeded. |
| Backend `python -m uv sync --locked`; `python -m uv run --locked ruff check app tests scripts`; `python -m uv run --locked ruff format --check app tests scripts`; `python -m uv run --locked pytest`; `python -m uv run --locked alembic upgrade head`; `python -m uv run --locked alembic check`; `python -m uv audit --locked` | PASS | 88 tests passed; Ruff clean; migration applied and no schema drift detected; audit found no known vulnerabilities in 33 packages. A temporary SQLite database was removed. |
| `git diff --check` | PASS | No whitespace errors in the current changes. |
| Jenkins Pipeline job execution | NOT RUN | The human has not completed Jenkins setup or created the trusted local job. |
| Jenkins image Trivy scan / Phase 10 secret scan | NOT RUN | No Phase 10-specific image or secret scan was run; no credentials were added to the workspace. |
| GitHub CI | NOT RUN | Would require a remote push or pull request; no remote action was authorized. |

## 5. Test results

- Tests run: 12 frontend tests and 88 backend tests.
- Passed: all unit tests, frontend/backend quality checks, dependency audits,
  database migration checks, Kubernetes rollouts, and HTTP smoke checks listed
  above.
- Failed, resolved: the first Kubernetes rollout could not find host-local
  images (`ErrImageNeverPull`). The image-import helper was added and verified;
  both deployments then became Ready. An initial `uv` invocation was not on
  `PATH`; using the installed `python -m uv` succeeded. An initial JSONPath
  node-list expression in the helper was corrected to use `kubectl get nodes
  -o name`.
- Failed, unresolved: none in the completed checks.
- Skipped: Jenkins pipeline execution and Phase 10 image/secret scan.
- Coverage: not measured.
- Known gaps: the actual pipeline job has not run; Jenkins setup and the
  wizard remain human-owned; no browser UI journey was run against Kubernetes.

## 6. Security and data integrity

- No application authentication, authorization, tenant-isolation, or
  audit-log code was changed.
- Kubernetes is explicitly local-only: demo auth, seeded ephemeral SQLite,
  non-public ClusterIP Services, no Ingress, and no persistent application
  database.
- Jenkins is loopback-only, uses a persistent home volume, drops Linux
  capabilities, has no Docker socket or cloud credentials, and is documented
  for trusted local code only.
- `npm audit` and `uv audit --locked` passed. A Trivy scan of the new Jenkins
  image and a Phase 10 secret scan were not run. Phase 9 API/web scan evidence
  is recorded separately and is not represented as a new Phase 10 scan.
- No Jenkins password, secret, token, or database URL was read, logged, or
  committed.

## 7. Evidence integrity

- Evidence produced: local manifest validation, image import, healthy
  Kubernetes rollouts, HTTP 200 health/readiness responses, Jenkins HTTP
  readiness, and local frontend/backend test and audit results.
- Evidence still TODO(human): Jenkins wizard completion, trusted Pipeline job
  configuration and a successful Jenkins run; human Phase 2 UX research; and
  the remaining Phase 9 CI/cloud evidence.
- The Jenkins pipeline is not claimed to have run. No Azure deployment,
  remote CI, cloud health, or Phase 10 security scan is claimed.

## 8. Deviations and blockers

- Docker Desktop Kubernetes did not automatically expose host-local image
  tags to its kind node. A narrowly scoped helper imports the two local tags
  into the node's containerd namespace. This remains a local Docker Desktop
  workflow and does not publish images.
- Jenkins cannot be configured or run through its authenticated UI until the
  human completes the setup wizard and creates a Pipeline job. Do not retrieve
  or share its bootstrap password.
- Phase 9 remains paused as PARTIAL; its CI and human Azure tasks are separate
  and are not represented as completed by Phase 10.
- No deviation from the approved local-only security boundaries.

## 9. Progress file

[`docs/progress.md`](../progress.md) records the current branch/base, completed
Phase 10 work, in-progress and next actions, blockers, decisions, and exact
verification results. Phase 9 is still marked PARTIAL; Phase 10 is still in
progress.

## 10. Human review required

1. Complete Jenkins setup locally at `http://127.0.0.1:8081`; do not share the
   bootstrap password.
2. Create a Pipeline job using the trusted local repository's `Jenkinsfile`
   and run it. Report the observed result so it can be recorded accurately.
3. Review the runbook and decide when to stop the local Jenkins controller and
   remove the local Kubernetes demo objects. The named Jenkins home volume
   contains setup/build state and is not deleted automatically.
4. Keep Phase 9 paused until its separate PR CI, ACR/ACI, database, cost,
   rollback, and cleanup evidence is approved and supplied.

## 11. Phase exit assessment

- Exit criteria met: **PARTIAL**.
- Evidence-backed explanation: the local Kubernetes demo is reproducible and
  healthy, the local Jenkins controller is HTTP-ready, and project quality
  checks pass. The Jenkins setup/job/pipeline demonstration has not been
  completed, so Phase 10 is not closed.
- Recommended next step: human completes Jenkins setup and runs the trusted
  Pipeline job. Stop here; do not start Phase 11 or mark Phase 10 complete
  until the human reviews the remaining evidence and explicitly approves
  closure.
