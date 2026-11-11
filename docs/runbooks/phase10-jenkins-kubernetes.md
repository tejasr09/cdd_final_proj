# Phase 10 Runbook — Local Jenkins and Kubernetes

Status: optional Phase 10 work is in progress. This runbook is for local/test
use only; no Azure resources, registry publishing, or deployment are included.

## Safety and scope

- Kubernetes API and web services use local `:local` images, have no public
  ingress, and are exposed only with `kubectl port-forward`.
- The Kubernetes API uses a seeded ephemeral SQLite database and local auth.
  Do not use real or production data.
- Jenkins listens only on `127.0.0.1:8081`, has a persistent named home
  volume, and does not receive the Docker socket or Azure credentials.
- Complete Jenkins' setup wizard yourself. Do not share the initial admin
  password. Configure jobs only for trusted code; this single-node demo is not
  suitable for untrusted pull requests.
- The Jenkins pipeline runs dependency audits and quality checks. It does not
  build, publish, or deploy container images.

## Local Kubernetes

Docker Desktop Kubernetes should use the `docker-desktop` context. Build the
project images using the established local Compose workflow, import the local
tags into the single-node cluster, then apply the manifests:

```powershell
docker image inspect ripple-effect-api:local
docker image inspect ripple-effect-web:local
kubectl config use-context docker-desktop
.\infra\phase10\load-local-images.ps1
kubectl apply -f infra\phase10\kubernetes.yaml
kubectl rollout status deployment/ripple-api -n ripple-effect --timeout=180s
kubectl rollout status deployment/ripple-web -n ripple-effect --timeout=180s
kubectl get pods,services -n ripple-effect
```

The manifests use `imagePullPolicy: Never` so Kubernetes cannot silently pull
an unrelated image. Docker Desktop's kind node has a separate containerd image
store from the host image list; the helper transfers the two local images into
the node's `k8s.io` namespace. It checks the context, requires exactly one
node, and removes its temporary archive. It is intentionally limited to the
local Docker Desktop demo.

In a second PowerShell window, forward the web Service to loopback:

```powershell
kubectl port-forward --address 127.0.0.1 -n ripple-effect service/ripple-web 5173:8080
```

In the first window, check the web health endpoint and the proxied API
readiness endpoint:

```powershell
(Invoke-WebRequest http://127.0.0.1:5173/health).StatusCode
(Invoke-WebRequest http://127.0.0.1:5173/api/v1/health/ready).StatusCode
```

Stop only the port-forward process with Ctrl+C. To remove the named local demo
workload when finished:

```powershell
kubectl delete -f infra\phase10\kubernetes.yaml
```

Deleting the namespace removes only the Phase 10 Kubernetes demo objects; the
Docker Desktop cluster itself is managed separately.

## Local Jenkins

Build and start the secured local controller:

```powershell
docker compose --project-name ripple-phase10-jenkins -f infra\phase10\jenkins\compose.yml up --build --detach
```

Open `http://127.0.0.1:8081` and complete the initial Jenkins setup wizard
locally. The controller's home is retained in the named
`ripple-phase10-jenkins_jenkins-home` volume. Do not mount the Docker socket,
add cloud credentials, or enable remote triggers for this test instance.

Create a Pipeline job that uses the repository `Jenkinsfile`, then run it
against trusted source. The build executor has Node.js, Python 3.11, uv, Git,
and the pinned Pipeline/Git plugins. `DATABASE_URL` points to a per-build
SQLite file; the post-build cleanup removes the Jenkins workspace.

The human may stop the controller without removing its data:

```powershell
docker compose --project-name ripple-phase10-jenkins -f infra\phase10\jenkins\compose.yml stop
```

Do not delete the Jenkins home volume unless you have explicitly decided to
discard the local Jenkins configuration and build history.

## Architecture distinction

The Phase 9 ACR/ACI design is the human-operated cloud path using immutable ACR
digests and an existing PostgreSQL service. Phase 10 Kubernetes is a separate
local demonstration using local image tags, a single replica, SQLite, and
loopback port forwarding. Jenkins does not publish to ACR or deploy to ACI or
Kubernetes.
