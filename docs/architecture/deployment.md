# Deployment

## Local development

Docker Compose provides the local PostgreSQL, API and web stack. It enables
local authentication and synthetic seed data only for development. It is not a
production identity or deployment configuration; see the root
[`README.md`](../../README.md) for setup and verification commands.

## Phase 9 preparation — partial

The required cloud demonstration target is Azure Container Registry (ACR) and
Azure Container Instances (ACI), using an existing PostgreSQL service and
Bicep as the selected IaC tool. The prepared infrastructure is split into
[`provision.bicep`](../../infra/azure/provision.bicep) (Premium ACR and
registry-scoped managed-identity pull access) and
[`aci.bicep`](../../infra/azure/aci.bicep) (digest-pinned API/web containers
and health probes). The selected PostgreSQL URL is supplied as a secure
parameter and is not provisioned by this project.

ACI public ingress defaults to disabled. The application does not yet have a
production identity provider or TLS ingress design; do not enable public
access until both are implemented, reviewed and approved. Premium ACR and ACI
costs, account eligibility, region and database network reachability require
human review.

The human-operated preparation, deployment, verification, rollback and cleanup
steps are in
[`phase9-acr-aci.md`](../runbooks/phase9-acr-aci.md). Local Compose build,
health, proxy smoke, Nginx upstream rendering, and full-severity Trivy scans
passed on 2026-11-12, and both Bicep templates compile with CLI 0.49.2. No
Azure `what-if`, resource creation, image push or deployment has been
performed. Phase 9 therefore remains partial pending approved-branch CI and
human-provided cloud evidence; see
[`phase9-report.md`](../reports/phase9-report.md).
