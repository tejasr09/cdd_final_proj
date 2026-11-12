# ADR-034: Local Jenkins and Kubernetes demonstrations

- Status: accepted for local Phase 10 demonstration
- Date: 2026-11-12
- Decision owners: human and agent

## Context

Phase 10 is optional and must not weaken the required application or cloud
deployment path. The human approved Docker Desktop Kubernetes and a local
Jenkins container. No Azure operations or automated image publishing are
authorized.

## Decision

- Use the one-node Docker Desktop Kubernetes cluster and plain Kubernetes YAML,
  not Helm, for the local demonstration.
- Deploy the API and web as ClusterIP services. Use port forwarding for local
  access; do not add an Ingress or public endpoint.
- Use a seeded, ephemeral SQLite database and local authentication in the
  Kubernetes demo only. It is not a production or multi-replica configuration.
- Run Jenkins with a digest-pinned official base image, a locked set of
  Pipeline/Git plugins, and a loopback-only web port.
- Do not mount the Docker socket or provide cloud credentials to Jenkins. The
  Jenkinsfile runs quality checks only; image publishing and cloud deployment
  remain outside the pipeline.
- Restrict the single-node Jenkins demonstration to trusted local repository
  code. A production Jenkins deployment must use isolated agents and separately
  reviewed identity and credential handling.

## Consequences

The local Kubernetes deployment is easy to reproduce but SQLite state is
ephemeral and local authentication is enabled. The Jenkins controller is not
configured for untrusted pull requests or privileged Docker builds. Its setup
wizard must be completed manually by the human; the agent does not read or
handle Jenkins bootstrap credentials.

## References

- [Jenkins in Docker](https://www.jenkins.io/doc/book/installing/docker/)
- [Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/features/kubernetes/)
