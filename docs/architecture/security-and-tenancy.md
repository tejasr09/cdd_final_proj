# Security and tenancy

## Phase 1 status

Authentication, authorization, membership, tenant scoping, audit logging, and secret-backed configuration are not implemented. The current health endpoints are public and expose only process readiness/liveness. The local `.env` file is ignored by Git and examples contain placeholders only.

The approved design requires server-side membership checks and composite tenant foreign keys before tenant-owned resources are introduced.
