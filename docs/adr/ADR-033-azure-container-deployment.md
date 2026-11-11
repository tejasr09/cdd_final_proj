# ADR-033: Prepare Azure deployment with Bicep, ACR, and ACI

- Status: accepted for Bicep selection; resource design and human review required before cloud provisioning
- Date: 2026-11-11
- Decision owners: TODO(human)
- Source: Phase 9 kickoff and `agent-brief-continuation.md`, D28

## Context

Phase 9 requires an ACR/ACI demonstration, immutable image promotion, and
human-controlled cloud changes. The human selected an existing PostgreSQL
service as the deployment database. The repository has no production identity
provider or TLS ingress configuration, and Azure account, region, and budget
are not yet confirmed.

## Decision

Use Bicep as the single IaC format. Split ACR/identity provisioning from
ACI deployment so the images can be published before ACI references them.
Use a Premium ACR with its admin and anonymous pull settings disabled, a
user-assigned managed identity with registry-scoped `AcrPull`, and immutable
API/web digest references. The human provides the existing TLS-enabled
PostgreSQL URL as a secure deployment parameter. Disable public ACI ingress by
default; public HTTP access is blocked until production authentication and TLS
ingress are implemented and separately approved.

## Alternatives considered

- Terraform: not selected for this phase because Bicep is native to Azure and
  avoids introducing a second infrastructure toolchain.
- ACR admin-user credentials: rejected in favor of a scoped managed identity.
- Provision Azure Database for PostgreSQL: not selected; the human chose an
  existing PostgreSQL service, avoiding an unapproved database resource/cost.
- Public ACI HTTP ingress now: rejected because the application has no
  production authentication or TLS ingress.

## Consequences

The selected managed-identity ACR pull path requires the Premium registry tier
according to the current Microsoft ACI guidance; the cost must be reviewed
before deployment. The external database owner must confirm network reachability
and TLS. With public ingress disabled, the application is not browser-accessible
outside the ACI environment. The phase cannot satisfy the live product-demo
exit criteria until authentication and safe ingress are resolved and actual
human deployment evidence is provided.

## Evidence

Official references:

- [ACI ACR pulls with a managed identity](https://learn.microsoft.com/en-us/azure/container-instances/using-azure-container-registry-mi)
- [ACI multi-container groups](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-multi-container-group)
- [ACR Bicep reference](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerregistry/registries)
- [ACI container-group Bicep reference](https://learn.microsoft.com/en-us/azure/templates/microsoft.containerinstance/containergroups)

The human selected Bicep on 2026-11-11. Templates and the human runbook are
prepared, and both templates compiled successfully with Bicep CLI 0.49.2 on
2026-11-12. The resource design still needs human review. No Azure `what-if`,
Azure resource creation, image push, or ACI deployment has been performed.
