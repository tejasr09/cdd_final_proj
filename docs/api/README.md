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
- `/events/{event_id}/analysis-runs`: synchronously analyze an open event and
  persist its immutable input snapshot, results, paths and audit record.
- `/analysis-runs`: list runs, optionally filtered by `event_id`; retrieve a
  run, its paginated results, an individual result, or the retained paths for
  that result. The collection also accepts `scenario_id`.
- `/scenarios`: create scenarios from completed live-run snapshots and list
  scenarios in the active organization.
- `/scenarios/{scenario_id}`: retrieve scenario overlays, update metadata with
  optimistic version checks, or archive scenario-owned history.
- `/scenarios/{scenario_id}/event`: update the scenario-only event overlay.
- `/scenarios/{scenario_id}/interventions`: add node mitigation, dependency
  weight override, dependency deactivation, or a hypothetical dependency
  marked `draft`.
- `/scenarios/{scenario_id}/analysis-runs`: execute against the immutable
  baseline snapshot plus the current overlay, saving a reproducible scenario
  run without changing live records.
- `/scenarios/{scenario_id}/comparison`: compare a scenario run with its
  baseline by entity, including estimated score deltas and assumptions.
- `/health/live` and `/health/ready`: process liveness and database readiness.

Scenario creation, updates, interventions, execution, and archival require
`analysis:run`; listing, retrieval, and comparison require `event:read`.
Mutation requests include `expected_version`, and each successful mutation
increments the version and writes an audit event. Archive preserves scenario
history; applying a scenario to live data is not supported.

To create a scenario, send `POST /api/v1/scenarios` with a completed live
`baseline_run_id`, then use `PATCH /api/v1/scenarios/{scenario_id}/event`,
`POST /api/v1/scenarios/{scenario_id}/interventions`, and
`POST /api/v1/scenarios/{scenario_id}/analysis-runs`. The run request includes
the current `expected_version`. Retrieve its comparison with
`GET /api/v1/scenarios/{scenario_id}/comparison?scenario_run_id=<run UUID>`.
Historical runs can also be listed using
`GET /api/v1/analysis-runs?scenario_id=<scenario UUID>`.

Scenario comparisons report heuristic estimates, not predictions,
recommendations, or guaranteed effects. The response includes baseline and
scenario run IDs, score deltas, changed/added/removed/unchanged entities,
assumptions, and result completeness. Scenario overlays remain separate from
live event, entity, and dependency records.

### Analysis request and responses

Create a run with `POST /api/v1/events/{event_id}/analysis-runs`. The caller
must be an active organization member with `analysis:run`; the event must be
open and have at least one trigger. The JSON body may be empty to use defaults,
or may contain:

```json
{
  "as_of": "2026-11-07T12:00:00Z",
  "max_depth": 4,
  "min_edge_weight": 0.0,
  "depth_attenuation": 0.8,
  "aggregation": "max",
  "max_paths_per_trigger": 10000,
  "max_nodes_per_run": 5000,
  "include_trigger_entities": true
}
```

The `201` response contains the run ID, status, effective configuration,
algorithm version, canonical input hash, UTC `as_of`, creation metadata and a
summary. `GET /api/v1/analysis-runs` accepts `event_id`, `limit`, and `offset`.
`GET /api/v1/analysis-runs/{run_id}` retrieves the run. The nested
`/results` collection returns paginated entity results ordered by descending
score, then minimum depth and entity UUID; an individual result includes the
impact score/level, minimum depth, confidence value/label/reason, explanation,
trigger IDs and primary-path ID. The nested `/paths` collection returns
retained paths ordered primary-first, then score, edge count and path UUID.
Path provenance includes ordered entity/dependency IDs, names, labels,
weights, review statuses and structured steps.

Run, result and path reads require `event:read`. A cross-organization run or
result returns 404. A run that reaches a configured ceiling is returned with
status `completed_with_limits`, a list of reached limits in its summary, and
`potentially_incomplete: true` on each result.

Every successful state change writes an audit record in the same database
transaction. Analysis execution requires `analysis:run`; reading runs and
results requires `event:read`. A non-member receives 404 for another
organization's run. A failed engine execution is saved with a safe diagnostic
ID and audited, then returned as HTTP 500 without exposing internal details.

Analysis accepts optional `as_of`, `max_depth` (1–10, default 4),
`min_edge_weight` (0–1, default 0), `depth_attenuation` (0–1, default 0.8),
`aggregation` (`max` or `capped_sum`), `max_paths_per_trigger` (1–10,000,
default 10,000), `max_nodes_per_run` (1–5,000, default 5,000), and
`include_trigger_entities` (default true). When omitted, `as_of` uses the
event's start time. A run that reaches either safety ceiling is saved as
`completed_with_limits`; its summary and each result flag the incomplete
analysis. Run responses include the canonical input hash, algorithm version,
configuration and summary. Results explain the primary path, minimum depth,
score, impact level and dependency-review confidence. The run snapshot can be
replayed by the engine without reading changed live records.

Run creation and execution are synchronous. Database row locks are applied
where supported, but SQLite does not provide equivalent row-lock behavior and
PostgreSQL concurrent-insert consistency has not yet been stress-tested.
Organization/member administration, audit-query and production
sign-in/session endpoints are not implemented.
