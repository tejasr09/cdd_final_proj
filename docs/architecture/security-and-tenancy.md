# Security and tenancy

## Status

Phase 3 implements persistence-level tenant boundaries, membership resolution,
role checks, and audited service operations. These are service foundations, not
a complete HTTP authentication or authorization integration. Production
identity remains undecided.

## Request identity and authorization

`app.auth` provides the approved development/test adapter. The local user ID
header is accepted only when `APP_ENV` is `development` or `test` and
`ENABLE_LOCAL_AUTH=true`. It resolves an active membership for the explicitly
selected organization; the client cannot choose a role or establish membership
by sending a header. Organization non-members receive 404, while members
lacking the required permission receive 403.

Role permissions are centralized in `ROLE_PERMISSIONS`. Service operations
authorize the membership before reading or changing tenant-owned resources.
Repository functions require an organization ID in tenant-owned queries.
Production authentication, HTTP endpoint wiring, and complete API-level
authorization tests remain later work.

## Database boundary and audit

Every tenant-owned table includes `organization_id`. Composite foreign keys
include tenant IDs for tenant-owned references, and SQLite foreign-key
enforcement is enabled for tests. This prevents cross-organization references
even if application-level validation is bypassed.

State-changing service methods add an `AuditLog` row to the same SQLAlchemy
session and transaction as the change. The audit summary is limited to the
actor, organization, action, resource and relevant changed fields. A future
HTTP layer must commit or roll back both together and pass through the request
correlation ID.

## Verification and limitations

Backend tests cover active membership, role permissions, local-auth gating,
tenant-scoped repository results, cross-tenant composite foreign-key
rejections, and audit records for implemented service changes. PostgreSQL DDL
ordering was checked through offline SQL generation; live PostgreSQL execution
and a dedicated database secret scan were not performed.

No production identity provider is configured. Local authentication is
disabled by default and is not suitable for production. HTTP CRUD endpoints,
request-level security logging, and the complete production auth flow are not
implemented in this phase.
