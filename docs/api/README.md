# API foundation

The versioned JSON API is rooted at `/api/v1`. FastAPI publishes the live
contract at `/openapi.json` and `/docs`; the reviewed snapshot is
[`openapi.json`](./openapi.json). After an intentional contract change, update
it from `backend` with `uv run --locked python -m scripts.export_openapi`.
The backend tests compare generated OpenAPI to the committed snapshot.

## Local authentication

Business routes require an active membership selected explicitly by the
caller. For local development only, enable the adapter with
`APP_ENV=development` and `ENABLE_LOCAL_AUTH=true`; send the seed user's ID in
`X-Local-User-ID` and the selected organization ID in
`X-Active-Organization-ID`. The seed command prints both demo user IDs. Local
identity headers are disabled by default and are not production
authentication. A client cannot supply a role or create a membership through
these headers.

The server checks membership and role permissions on every route. A
non-member receives 404 for organization-owned records; an active member
without the required permission receives 403. The permission matrix is
documented in [`ADR-021`](../adr/ADR-021-role-permissions.md).

## Collections, errors and concurrency

Collections accept `limit` (1–100, default 50) and `offset` (default 0) and
return `items`, `limit`, `offset`, and `total`. Ordering is stable and includes
a UUID tie-breaker. Entity filters are `entity_type`, `status`, and `name`;
dependency filters are `source_entity_id`, `target_entity_id`, `is_active`,
and `review_status`; event filters are `status`, `title`, `start_from`, and
`start_to`.

Errors use this envelope and carry an `X-Request-ID` response header:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request could not be validated.",
    "details": [
      {
        "field": "body.weight",
        "message": "Input should be less than or equal to 1",
        "code": "less_than_equal"
      }
    ],
    "request_id": "..."
  }
}
```

Schema-validation failures return 422, invalid state transitions and
duplicate records return 409, missing or cross-organization records return
404, and permission failures return 403. Edit and lifecycle requests must
include the resource's `expected_updated_at` value from its latest response;
stale updates are rejected with 409. Database rows are locked for update where
the database supports row locks.

## Implemented route groups

- `/entities`: list/filter, retrieve, create, update and soft-archive.
- `/dependencies`: list/filter, retrieve, create, update, activate and
  deactivate. Source-to-target orientation is retained; self-loops,
  duplicates, and cross-organization endpoints are rejected.
- `/events`: list/filter, retrieve, create, update and lifecycle transitions.
  New events start as draft unless explicitly created open. Only an
  administrator may reopen a resolved or archived event.
- `/events/{event_id}/triggers`: add, list and remove trigger associations.
- `/health/live` and `/health/ready`: process liveness and database readiness.

Every successful state change writes an audit record in the same database
transaction. Analysis, scenario, organization/member administration, and
production sign-in/session endpoints are not implemented in this phase.
