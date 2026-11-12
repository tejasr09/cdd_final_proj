# Phase 9 Runbook — Azure Container Registry and Container Instances

Status: agent preparation in progress; the human selected Bicep for ADR-033.
No Azure account, subscription, resource, image, or deployment has been
verified or changed.

## Scope and safety gates

This runbook is for the human operator. The agent must not execute Azure
provisioning, deployment, registry login/push, resource deletion, or other
cloud-changing commands.

Before any cloud command, the human must:

1. Confirm Azure student/institutional account eligibility and policy.
2. Select the subscription, resource group, and region.
3. Review current cost estimates and configure budget alerts. The template uses
   ACR Premium because ACI managed-identity image pulls require Premium ACR;
   ACI also incurs charges while the container group runs.
4. Confirm the selected external PostgreSQL service is reachable from ACI and
   accepts TLS connections. The ACI template does not create or manage a
   database.
5. Keep `publicIngressEnabled=false`. The application has no production
   identity provider or TLS ingress configuration. Do not expose the HTTP
   endpoint publicly until both are designed, implemented, reviewed, and
   separately approved.
6. Confirm the exact code commit and image digests to deploy. Do not use
   `latest` or rebuild after recording the digest.

If any prerequisite is unresolved, stop before provisioning. In particular,
do not enable ACR's admin account to avoid the Premium cost without reviewing
and approving the change to the managed-identity plan.

## Architecture

- `provision.bicep` creates a Premium ACR, a user-assigned identity, and an
  `AcrPull` role assignment scoped only to that registry. ACR admin and
  anonymous pulls are disabled.
- `aci.bicep` deploys the API and web containers as one Linux ACI group using
  immutable ACR digest references and that pull identity. The group exposes
  no public IP unless the human explicitly sets the public-ingress parameter.
- Containers in one ACI group communicate over localhost. The web image
  substitutes `API_UPSTREAM=127.0.0.1:8000`; Docker Compose keeps its
  `api:8000` default.
- The database URL is a required secure Bicep parameter, injected as an ACI
  secure environment variable. It is not output by the template.
- Local authentication and demo seeding are explicitly disabled in ACI.

## Local validation

Use the official Bicep CLI and Azure CLI installed by the human from their
official Microsoft distribution channels. Do not sign in to Azure merely to
compile the templates.

From the repository root in PowerShell:

```powershell
bicep build infra\azure\provision.bicep --stdout | Out-Null
bicep build infra\azure\aci.bicep --stdout | Out-Null
docker compose --env-file .env.example config --quiet
```

To build and smoke-test the local images without disturbing other Compose
projects, use a unique project name and remove only that project's resources
afterward:

```powershell
$project = "ripple-phase9-local-check"
docker compose --project-name $project --env-file .env.example up --build --detach --wait --wait-timeout 240
python backend\scripts\smoke_compose.py
docker run --rm -e API_UPSTREAM=127.0.0.1:8000 ripple-effect-web:local nginx -T
docker compose --project-name $project --env-file .env.example down --volumes --remove-orphans
```

The Nginx config output should contain the selected upstream while preserving
Nginx variables such as `$host`. Run the Phase 8 CI-equivalent scans on both
images before publishing; do not lower severity or ignore findings:

```powershell
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.74.0 image --format table --vuln-type os,library --scanners vuln,secret --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL --exit-code 1 ripple-effect-api:local
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.74.0 image --format table --vuln-type os,library --scanners vuln,secret --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL --exit-code 1 ripple-effect-web:local
```

Run the approved GitHub CI workflow before publishing any images. Do not claim
validation until the commands are actually run.

## Identity and secret handling

The ACI pull identity receives only registry-scoped `AcrPull`. The human
publisher needs `AcrPush` at the ACR scope; the runbook does not assign that
role automatically. Use the organization's approved interactive Azure
authentication for manual publishing and deployment. The ACR admin account
stays disabled, and no credentials are needed in the repository for this
manual path.

There is no approved GitHub Actions publish/deploy workflow in this phase. Do
not add one, expand workflow permissions, configure GitHub secrets, or set up
federated GitHub identity without separate human approval. Keep the secure
database parameter file outside the repository and restrict access to it.

## Human deployment procedure

The commands below are examples only. Replace every placeholder after the
human has reviewed the safety gates. Provisioning, publishing, and deployment
are cloud-changing human actions.

### 1. Prepare and review

```powershell
$subscriptionId = "<human-selected-subscription-id>"
$resourceGroup = "<human-selected-resource-group>"
$region = "<human-selected-region>"
$acrName = "<globally-unique-lowercase-acr-name>"
$identityName = "ripple-effect-aci-pull"
$ownerTag = "<team-owner-tag>"

az account set --subscription $subscriptionId
az group create --name $resourceGroup --location $region
az deployment group what-if `
  --resource-group $resourceGroup `
  --template-file infra\azure\provision.bicep `
  --parameters location=$region registryName=$acrName imagePullIdentityName=$identityName owner=$ownerTag
```

The resource-group creation command changes Azure state. Run it only after
approval and cost review. Review the `what-if` output before executing the
provisioning deployment:

```powershell
az deployment group create `
  --name ripple-acr-bootstrap `
  --resource-group $resourceGroup `
  --template-file infra\azure\provision.bicep `
  --parameters location=$region registryName=$acrName imagePullIdentityName=$identityName owner=$ownerTag
```

Wait for the identity's `AcrPull` assignment to propagate before deploying ACI.
For publishing, the human operator needs `AcrPush` at the ACR scope; assign it
through the approved Azure interface. Do not enable ACR admin credentials.

### 2. Build once, publish, and record digests

Use a reviewed release/version and the full source commit SHA for tags. The
push below is performed by the human after the source commit passes CI:

```powershell
$loginServer = az acr show --name $acrName --resource-group $resourceGroup --query loginServer --output tsv
$commit = git rev-parse --short=12 HEAD
$release = "<human-approved-version>"
$apiTag = "${loginServer}/ripple-effect-api:${release}-${commit}"
$webTag = "${loginServer}/ripple-effect-web:${release}-${commit}"

az acr login --name $acrName
docker buildx build --platform linux/amd64 --file backend\Dockerfile --tag $apiTag --push backend
docker buildx build --platform linux/amd64 --file frontend\Dockerfile --tag $webTag --push frontend
docker buildx imagetools inspect $apiTag
docker buildx imagetools inspect $webTag
```

Record each registry-reported `sha256` digest and associate it with the source
commit, version tag, and CI run. Use `loginServer/repository@sha256:<digest>`
for ACI. Do not put credentials in Docker build arguments or image layers.

### 3. Prepare the secure ACI parameters

Copy
[`infra/azure/aci.parameters.example.json`](../../infra/azure/aci.parameters.example.json)
to a protected local path outside the repository, replace the placeholders,
and set `databaseUrl` to the approved TLS-enabled PostgreSQL URL. The example
file is not deployable as-is. Keep the local file access-restricted, never
commit it, and remove it after deployment. The template marks this value
secure; do not paste it into chat, shell history, CI logs, or command-line
arguments.

Keep `publicIngressEnabled` false. In this configuration the group is not
internet-accessible; validation is through ACI provisioning/health status and
container logs. A public URL is not safe or functional for authenticated
product use until production auth and TLS ingress are ready.

### 4. Review and deploy the container group

```powershell
$localParameters = "<protected-local-path-to-aci.parameters.json>"
az deployment group what-if `
  --resource-group $resourceGroup `
  --template-file infra\azure\aci.bicep `
  --parameters "@$localParameters"
```

Review that the template uses only the intended resource group, the two
digest-pinned images, the existing pull identity, the approved region, disabled
public ingress, and the external database. If any value is unexpected, stop.
After human approval of the preview, the human may execute:

```powershell
az deployment group create `
  --name ripple-aci-demo `
  --resource-group $resourceGroup `
  --template-file infra\azure\aci.bicep `
  --parameters "@$localParameters"
```

Never run these deployment commands from the agent.

## Verification and evidence capture

The human should capture actual command output (with secrets redacted):

```powershell
az container show --resource-group $resourceGroup --name ripple-effect-demo --output json
az container logs --resource-group $resourceGroup --name ripple-effect-demo --container-name api
az container logs --resource-group $resourceGroup --name ripple-effect-demo --container-name web
```

Confirm both containers report running, the API readiness probe succeeds
against the external database, the web health probe succeeds, and the reported
images are the approved digest references. Do not invent health results or
include the database URL in evidence. Once production auth and an approved TLS
ingress are available, separately verify the browser-to-API workflow and
record the actual endpoint and test evidence.

## Rollback

Keep the last known-good API and web image digests in the release evidence.
To roll back, change only `apiImage` and `webImage` in the protected parameter
file to the previous digest pair, review the ACI deployment `what-if`, then
have the human redeploy `aci.bicep`. Verify health and retain both image
versions until the rollback is accepted. Do not rebuild an older source tag
and call it the same image.

## Cleanup

Stop and remove only the named demo container group when no longer needed:

```powershell
az container delete --resource-group $resourceGroup --name ripple-effect-demo
```

ACR continues to incur cost while it exists. Before removing the registry,
confirm the exact resource group contents, retained image/evidence requirements,
and approval to delete. Never use a broad resource-group deletion command
without independently reviewing every resource it would remove.

## Troubleshooting

- **ACI image pull denied:** check ACR Premium, the identity attached to the
  container group, the registry-scoped `AcrPull` assignment, and role
  propagation. Do not turn on the registry admin user as a shortcut.
- **API stays unready:** inspect API logs, confirm the database URL is TLS
  enabled, and ask the database owner to verify network/firewall access from
  the ACI environment. Do not print the URL.
- **Web proxy returns 502:** confirm the ACI web container has
  `API_UPSTREAM=127.0.0.1:8000`, the API container listens on port 8000, and
  the deployed web image includes the template-based Nginx config.
- **No browser endpoint:** expected while public ingress is false. Do not
  enable HTTP ingress until production auth and TLS are implemented and
  approved.
- **Premium tier not permitted or affordable:** stop and ask for review of
  registry/pull identity alternatives. Do not silently weaken registry
  security or incur unapproved costs.

## Human evidence checklist

- [ ] Azure eligibility, policy, subscription, region, resource group, budget
      alerts, and current ACR Premium/ACI costs reviewed.
- [ ] Existing PostgreSQL owner confirms TLS, reachability, and firewall plan.
- [ ] Production identity and TLS ingress decision approved before any public
      exposure.
- [ ] ACR and identity resource outputs recorded; no secret values included.
- [ ] Source commit, CI run, version tags, and registry-reported image digests
      recorded.
- [ ] ACI health, image references, and smoke/browser results backed by actual
      human-executed evidence.
- [ ] Rollback and cleanup reviewed and executed or explicitly left pending.
