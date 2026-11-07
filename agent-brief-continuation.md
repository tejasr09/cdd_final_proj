# Ripple Effect — Master Build Prompt
## Continuation: Section 4, D9 onward

> **Continuation note:** This document continues the existing `docs/agent-brief.md` immediately after D8 — Multi-tenancy. Preserve the existing Sections 1–4 and D1–D8 exactly as approved. Append this material; do not replace or silently rewrite earlier decisions. The existing master brief and this continuation together form the complete build specification.

---

## 4. Resolved design decisions (continued)

The following decisions complete the binding design baseline. Record each as an Architecture Decision Record (ADR) during Phase 0. If the existing repository or a genuine technical constraint makes a decision impossible, stop, explain the evidence and ask for approval before changing it.

**D9 — Event-to-entity association.** An event may affect one or more trigger entities. Store these associations explicitly in an `event_triggers` table rather than hiding entity IDs inside event JSON. Each association belongs to the same organization as its event and entity. A trigger has an optional rationale and an optional trigger-specific exposure value in the range 0.0–1.0; default exposure is 1.0. Event severity is shared across its triggers in v1. The engine starts propagation independently from each trigger and combines results using the run's aggregation rule. A trigger entity itself is included in results at depth 0 with its effective severity score, unless the run configuration explicitly excludes trigger display; the default is to include it.

**D10 — Minimum edge weight.** A run may specify `min_edge_weight` in the inclusive range 0.0–1.0; default 0.0. An edge is eligible only when its weight is greater than or equal to this threshold. This filter is applied before path enumeration. The threshold is stored in the run configuration and displayed in the run details. A zero-weight edge may be retained in the model but contributes zero impact; it is not silently deleted.

**D11 — Path limits and deterministic safety.** Enumerate simple paths only: a path may not visit the same entity more than once. Do not enumerate paths beyond `max_depth`. Add a configurable `max_paths_per_trigger` safety ceiling (default 10,000) and a `max_nodes_per_run` ceiling (default 5,000). If a ceiling is reached, the run must finish with an explicit `completed_with_limits` status, record the limit and truncation details, and mark results as potentially incomplete. Never silently present a truncated run as complete. The values are configurable within documented safe ranges and must be validated. A deterministic ordering of outgoing edges and path candidates is required so identical inputs produce identical results.

**D12 — Multi-trigger aggregation.** For a given entity reached from multiple triggers, first calculate the best path per trigger using D5. Under `max`, retain the highest-scoring path across all triggers. Under `capped_sum`, sum the best path per distinct final edge across the entire run, not once per trigger, and cap at 100. Store the primary path and all retained contributing paths separately. A path is identified by its ordered entity IDs and dependency IDs. Do not count the same path twice merely because it can be reached from more than one traversal entry. Ties use D5. Record the originating trigger for every path.

**D13 — Event lifecycle and time semantics.** Event status values are `draft`, `open`, `resolved` and `archived`. Only `open` events can be run as live analyses by default. A user may run a draft event only through an explicitly labelled preview action if that feature is implemented; it must not change the event's status. Resolved and archived events remain available for history but cannot be run as new live analyses unless an administrator deliberately reopens them. `start_at` is required. `duration_minutes` is optional and informational in v1. All persisted timestamps are timezone-aware and stored in UTC; the UI displays them in the user's local timezone. The event's `start_at` is the default `as_of` value.

**D14 — Scenario isolation.** A scenario is a versioned, organization-owned overlay on a baseline run. Scenario events, dependency overrides, entity overrides and interventions are stored separately from live records. Running a scenario reads a consistent snapshot of baseline inputs plus the scenario overlay and writes a new run linked to the scenario. It must never update live entities, dependencies or events. Discarding a scenario removes or archives only scenario-owned records according to the approved retention policy. Applying a scenario to live data is not part of v1. If a later version adds an apply workflow, it requires a separate approval, preview, validation, audit trail and ADR.

**D15 — Intervention semantics.** An intervention is an explicit hypothetical change, not an automatic recommendation. V1 supports: (a) node mitigation override `m` in the range 0.0–1.0; (b) dependency weight override in the range 0.0–1.0; (c) dependency deactivation in the scenario overlay; and (d) adding a hypothetical dependency marked `draft`. Each intervention has a human-readable title, rationale, assumptions, author and creation time. `estimated_effect` is derived by comparing baseline and scenario results; do not accept an arbitrary user-entered score as if it were measured effectiveness. The UI may describe a scenario as “lower estimated impact”, never “guaranteed mitigation”.

**D16 — Confidence semantics.** Confidence is independent of impact severity. Use D6 exactly: confidence values are derived from the weakest review status along the primary path. Map 0.5 to `low`, 0.8 to `medium` and 1.0 to `high`. For a trigger-only path confidence is high. Display the underlying review status and explain that confidence describes dependency-data review quality, not the likelihood of an outcome. Do not average confidence or infer it from the impact score.

**D17 — Result persistence and reproducibility.** Every run stores an immutable snapshot of all inputs that affect its result: event fields and trigger associations, relevant entity fields, eligible dependency fields and review statuses, scenario overrides, algorithm version, configuration, `as_of`, and the selected aggregation rule. Store a canonical input hash and algorithm version. Historical results must remain viewable even if source entities or dependencies later change. Do not recalculate an old run silently. A deliberate rerun creates a new run.

**D18 — API contract.** Use REST JSON endpoints under `/api/v1`. Publish OpenAPI through FastAPI and keep a reviewed OpenAPI snapshot in the repository. Use UUIDs in public resource paths. Use pagination for collection endpoints, stable ordering, filtering and consistent error envelopes. Pydantic request and response schemas are separate from SQLAlchemy/database models and engine data structures. Do not expose ORM objects directly. Breaking API changes require a versioning decision and ADR.

**D19 — Authentication baseline.** Implement an authentication adapter so the domain and authorization code do not depend directly on one identity provider. For local development, use a documented local authentication implementation suitable for the test environment. If Supabase Auth is selected, verify JWTs server-side and keep service-role credentials server-only. Do not invent a production identity configuration. Authentication provider, token issuer/audience, allowed algorithms and key discovery must be explicitly configured and validated. Never accept an unsigned token or trust organization/role claims supplied only by the browser.

**D20 — Authorization baseline.** Roles are `administrator`, `operations_coordinator`, `department_coordinator` and `analyst`. Enforce permissions on the server for every endpoint and resource. A membership in an organization is required before any tenant-owned record can be accessed. Non-members receive 404 for organization-owned resources; members lacking a role permission receive 403. A user may belong to multiple organizations and must explicitly select an active organization. Never use a client-provided `organization_id` as proof of access. The server derives the active organization from a validated membership context.

**D21 — Role permissions.** Default permissions:
- `administrator`: manage organization settings, members, roles and reference data; full CRUD for operational records; view audit logs; run analyses and scenarios.
- `operations_coordinator`: create/update events; manage entities and dependencies; run live analyses; create and run scenarios; inspect run history.
- `department_coordinator`: read organization-wide entities and dependencies; inspect events and analysis results; propose dependency edits if the proposal workflow is implemented. No direct member/role administration.
- `analyst`: read operational model and event data; run scenarios and compare results; cannot modify live entities, dependencies or event records by default.
These are server-side defaults, not UI-only hiding rules. Any finer-grained permission model must be documented and tested.

**D22 — Audit logging.** Every successful state-changing API operation must write an audit record in the same database transaction as the change where practical. Include actor, organization, action, resource type and ID, timestamp, request/correlation ID and a minimal before/after summary or changed-field list. Never log passwords, tokens, secrets or unnecessary personal data. Failed authorization attempts may be recorded in security logs without revealing resource existence. Audit records are append-only through the application; no ordinary API may update or delete them. Analysis runs and scenario execution are auditable actions.

**D23 — Database and migrations.** Use PostgreSQL as the authoritative persistence layer, SQLAlchemy 2.x (or a comparably explicit supported ORM) and Alembic migrations. Use UUID primary keys, timezone-aware timestamps, check constraints, unique constraints and indexes. Every tenant-owned table has `organization_id`. Enforce composite foreign keys for tenant-owned references. Migrations are reviewed source files; do not rely on `create_all()` in deployed environments. A fresh database must be constructible from migrations and documented seed commands.

**D24 — Frontend baseline.** Use React and TypeScript with Vite. Use React Flow for the dependency and impact graph. Use a consistent component system and accessible form controls. Tailwind CSS is the proposed styling utility; confirm its current stable configuration before implementation. Use Vitest and React Testing Library for component/unit tests and Playwright for end-to-end tests. Keep API calls in a typed client/service layer. Do not place business logic or impact calculations in React components.

**D25 — Graph layout and visual encoding.** The graph is a visualization of the directed model, not the source of truth. Arrows always follow source → target. Edge labels and tooltips show relationship type, weight, review status and rationale. Node styling distinguishes entity type and impact level, but never relies on colour alone; include text/icon/shape cues and a visible legend. Trigger nodes, affected nodes, unaffected context nodes and scenario-added nodes must be distinguishable. Provide a list/table alternative for keyboard and screen-reader users. Large graphs must support filtering and focused subgraph views.

**D26 — Reporting and export.** A user may view a run in the application. CSV export of tabular impact results is a SHOULD; a printable report is a COULD unless required by the course or final acceptance. Any export must include run ID, timestamp, algorithm version, configuration, limitations and the “estimate, not probability” statement. Exports must be tenant-scoped and audited. Do not expose internal database IDs unnecessarily.

**D27 — Observability.** Use structured application logs with severity, timestamp, service, request/correlation ID and event type. Health endpoints must distinguish process liveness from readiness (database connectivity and required dependencies). Do not log graph payloads or personal data wholesale. Basic metrics may include request count/latency, run duration, number of visited nodes/paths and run status. Metrics are operational indicators, not claims of product accuracy.

**D28 — Deployment baseline.** Local development uses Docker Compose with `web`, `api` and `db` services, plus a one-shot migration service if useful. The syllabus-aligned cloud demonstration is ACR image publishing and ACI deployment. ACI is the required cloud target in this brief; AKS is optional and must not displace ACI. Build an image once and promote the same immutable digest between environments. Do not deploy to cloud without explicit human execution and approval.

**D29 — Dependency policy.** Prefer a small, maintained dependency set. Pin direct runtime and development dependencies using lockfiles. Before adding a runtime package, report its purpose, current stable version, licence, maintenance evidence, security posture, alternatives and why the existing stack is insufficient. Ask for approval under Section 2.1. Do not add a graph database, message broker, cache, ML framework or microservice merely for architectural appearance.

**D30 — No fabricated validation.** All personas, interview findings, usability scores, performance benchmarks, deployment results, screenshots and CI claims must be backed by actual evidence. Until obtained, mark them `TODO(human)` or `HYPOTHESIS — to be validated`. The demonstration data in Appendix C is synthetic and must be labelled as illustrative.

---

## 5. Target architecture and repository structure

### 5.1 Architecture boundaries

Implement a modular monolith first. The web client, API, domain services, analysis engine and persistence layer may run as separate containers, but do not split the backend into networked microservices in v1.

Required dependency direction:

1. Presentation layer calls typed API services.
2. API routes authenticate, authorize, validate and delegate.
3. Application services coordinate use cases and transactions.
4. Domain modules define rules and value objects.
5. The ripple engine accepts plain, validated input structures and returns deterministic results.
6. Persistence adapters load and save data; the engine must not import SQLAlchemy, FastAPI or frontend packages.

The engine must be runnable in unit tests without a database or HTTP server. Domain logic must be testable without React. API tests may use a disposable test database.

### 5.2 Suggested repository layout

Adapt to an existing repository rather than creating duplicate structures. Keep the following logical separation:

```text
ripple-effect/
├── AGENTS.md
├── README.md
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── .env.example
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── events/
│   │   │   ├── entities/
│   │   │   ├── dependencies/
│   │   │   ├── analysis/
│   │   │   ├── scenarios/
│   │   │   └── administration/
│   │   ├── lib/
│   │   ├── services/
│   │   ├── types/
│   │   └── tests/
│   └── Dockerfile
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock                 # or the selected package manager's lockfile
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── domain/
│   │   ├── services/
│   │   ├── engine/
│   │   └── repositories/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
├── infra/
│   ├── azure/
│   ├── terraform/              # or bicep/, select one
│   └── README.md
├── .github/
│   ├── workflows/
│   └── copilot-instructions.md
├── docs/
│   ├── agent-brief.md
│   ├── progress.md
│   ├── architecture/
│   ├── adr/
│   ├── api/
│   ├── ux/
│   ├── runbooks/
│   ├── evidence/
│   ├── viva-notes.md
│   └── reports/
└── scripts/
```

The exact folders may differ if the repository already has a coherent convention. Do not create empty folders merely to match this tree. Document any material deviation.

### 5.3 Module contracts

- `domain`: entity, event, dependency, membership and scenario rules; no HTTP or ORM imports.
- `engine`: graph input/output types, eligibility filtering, depth calculation, path enumeration, scoring, aggregation and explanations.
- `services`: use-case orchestration and transaction boundaries.
- `repositories`: organization-scoped database access.
- `api`: HTTP concerns only; no graph algorithms in route handlers.
- `frontend/features`: user workflows; no direct database access.
- `infra`: reproducible infrastructure definitions and human-executed runbooks.

Create a short `README.md` in a module only when it explains non-obvious responsibilities or invariants. Avoid documentation that merely repeats filenames.

### 5.4 Required architecture documentation

Create:
- `docs/architecture/system-context.md`
- `docs/architecture/container-view.md`
- `docs/architecture/data-model.md`
- `docs/architecture/engine.md`
- `docs/architecture/security-and-tenancy.md`
- `docs/architecture/deployment.md`

Use Mermaid diagrams where useful. Diagrams must match the implemented system, not an aspirational architecture. Mark planned components clearly.

---

## 6. Data model and persistence specification

### 6.1 Required tables

Implement the following logical tables. Exact column names may follow the repository's naming convention, but preserve the semantics and constraints.

| Table | Required purpose and fields |
|---|---|
| `organizations` | `id`, `name`, `created_at`, `updated_at` |
| `users` | Identity-provider subject or local user ID, minimal profile fields, timestamps; do not store passwords if an external identity provider is used |
| `organization_members` | `id`, `organization_id`, `user_id`, `role`, status, timestamps; unique membership per organization/user |
| `entities` | `id`, `organization_id`, `name`, `description`, `entity_type`, `status`, `exposure`, `mitigation`, `metadata`, timestamps, optional archive time |
| `dependencies` | `id`, `organization_id`, `source_entity_id`, `target_entity_id`, `relationship_type`, `weight`, `rationale`, `review_status`, `is_active`, `valid_from`, `valid_until`, timestamps |
| `events` | `id`, `organization_id`, `title`, `description`, `severity`, `start_at`, `duration_minutes`, `status`, timestamps |
| `event_triggers` | `id`, `organization_id`, `event_id`, `entity_id`, `exposure`, `rationale`, created time; unique event/entity association |
| `impact_runs` | `id`, `organization_id`, `event_id`, optional `scenario_id`, `status`, `configuration`, `algorithm_version`, `input_hash`, `as_of`, summary fields, creator and timestamps |
| `impact_results` | `id`, `organization_id`, `run_id`, `entity_id`, `depth`, `score`, `confidence_value`, `confidence_label`, primary path reference/data, explanation, result flags |
| `impact_paths` | `id`, `organization_id`, `run_id`, `entity_id`, `trigger_entity_id`, ordered entity/dependency sequence, score, edge count, is-primary, provenance metadata |
| `scenarios` | `id`, `organization_id`, `name`, `description`, `baseline_run_id`, status, version, creator and timestamps |
| `scenario_events` | Scenario-owned hypothetical event inputs or overrides; never overwrite the original event |
| `scenario_entity_overrides` | Scenario-owned entity exposure/mitigation/status overrides |
| `scenario_dependency_overrides` | Scenario-owned dependency weight/active/review-status overrides and hypothetical edges |
| `interventions` | `id`, `organization_id`, `scenario_id`, title, action type, target reference, rationale, assumptions, author and timestamps |
| `audit_logs` | `id`, `organization_id`, actor, action, resource type/ID, request ID, timestamp, minimal change summary |
| `refresh_tokens` or equivalent | Only if the chosen authentication design requires application-managed refresh tokens; prefer provider-managed sessions |

Do not implement a table that is not needed by the approved design. If a separate `impact_paths` table is too complex for the selected persistence design, an equivalent normalized child structure is acceptable, but do not lose path provenance or deterministic ordering.

### 6.2 Tenant constraints

- Every tenant-owned table contains `organization_id NOT NULL`.
- Use composite unique constraints such as `(id, organization_id)` on referenced tenant-owned tables.
- Use composite foreign keys such as `(event_id, organization_id)` → `events(id, organization_id)`.
- Apply the same rule to entity, run, scenario and dependency references.
- Ensure uniqueness of `(organization_id, source_entity_id, target_entity_id)` for dependencies.
- Add a check constraint preventing `source_entity_id = target_entity_id`.
- Enforce weight, severity, exposure and mitigation ranges at both API and database levels where supported.
- Ensure `valid_until` is null or later than `valid_from`.
- Ensure `organization_members` has a unique `(organization_id, user_id)` pair.
- Do not rely on application checks alone for cross-tenant references.

### 6.3 Indexes and query patterns

At minimum, consider indexes for:
- organization membership lookup by `user_id` and `organization_id`;
- entities by `(organization_id, status, entity_type)`;
- dependencies by `(organization_id, source_entity_id, is_active)`;
- dependencies by `(organization_id, target_entity_id)`;
- events by `(organization_id, status, start_at)`;
- event triggers by `(organization_id, event_id)`;
- impact runs by `(organization_id, created_at)` and `(organization_id, event_id)`;
- results by `(organization_id, run_id, score)`;
- audit logs by `(organization_id, timestamp)` and resource reference.

Avoid speculative indexes. Use query plans only when performance evidence justifies additional indexes.

### 6.4 Entity and relationship vocabulary

Entity types must be configurable or represented as validated reference values. Seed useful generic values such as `person`, `department`, `resource`, `activity`, `system`, `location` and `group`. Do not hard-code laboratory-specific rules into the engine.

Relationship types are labels describing source → target, such as `hosts`, `enables`, `staffs`, `supplies`, `schedules`, `shares_capacity_with` and `affects`. Store a stable key and display label. The UI may provide a curated list but the backend validates the stable key.

### 6.5 Review status and temporal eligibility

A dependency is eligible for a run only if:
- it is active;
- `valid_from` is null or `valid_from <= as_of`;
- `valid_until` is null or `as_of <= valid_until`;
- both endpoint entities are not archived;
- its weight meets `min_edge_weight`;
- its source and target belong to the active organization.

Use a consistent inclusive validity-window rule. Store the selected `as_of` value on the run. Do not query current time separately for individual edges.

### 6.6 Migrations and seed data

- Use Alembic revisions for all schema changes.
- Test both an empty-database upgrade and an upgrade from the previous revision.
- Use deterministic, clearly labelled synthetic seed records.
- Seed scripts must be idempotent or must fail safely with a clear message if records already exist.
- Never put real student, staff or institutional personal data in sample data.
- Do not run seed scripts automatically against a non-local database.
- Document how to reset only the local development database.

---

## 7. Ripple analysis engine — implementation contract

This is the most logic-sensitive component. Tests must be written before implementation. Keep the engine independent of FastAPI, SQLAlchemy and React.

### 7.1 Input contract

A run input must contain:
- organization ID;
- event ID and immutable event snapshot;
- one or more trigger entities and trigger exposure values;
- eligible entity snapshots, including exposure, mitigation and archived status;
- eligible dependency snapshots, including weight, review status, rationale and validity metadata;
- `as_of`;
- `max_depth`;
- `min_edge_weight`;
- `depth_attenuation`;
- aggregation method (`max` or `capped_sum`);
- impact-level thresholds;
- path and node safety ceilings;
- algorithm version;
- optional scenario overlay.

Validate the input before graph construction. Reject malformed IDs, duplicate dependency IDs, invalid numeric ranges, self-loops, duplicate ordered pairs and cross-organization references. The persistence layer should already enforce most of these invariants; engine validation is still required because the engine must be independently safe.

### 7.2 Output contract

Return a deterministic result object containing:
- run status (`completed`, `completed_with_limits` or `failed`);
- algorithm version and canonical input hash;
- effective configuration;
- all trigger results;
- one aggregate result per affected entity;
- minimum depth from any trigger;
- aggregate score and impact level;
- confidence value/label and explanation;
- primary path and all retained alternative/contributing paths;
- path scores, edge counts and originating triggers;
- counts of eligible nodes, eligible edges, visited nodes and enumerated paths;
- any safety limit reached and a clear incompleteness warning.

Do not persist partial outputs as a successful completed run. If an unexpected engine error occurs, record a failed run with a safe error code and diagnostic correlation ID; do not expose stack traces to the browser.

### 7.3 Algorithm stages

Implement these stages as separate, testable functions:

1. **Normalize and validate input.**
2. **Resolve temporal and status eligibility.**
3. **Construct a directed graph** using source → target semantics.
4. **Calculate minimum depth** from all trigger nodes using breadth-first search (`collections.deque` or an equivalent NetworkX method). Depth is independent of score.
5. **Enumerate bounded simple paths** from each trigger, stopping at `max_depth` and never revisiting a node in the current path.
6. **Calculate each path score** using D3.
7. **Aggregate paths** using D5 and D12.
8. **Calculate confidence** using D6/D16.
9. **Generate a human-readable explanation** from actual path facts and run configuration.
10. **Sort and serialize results deterministically.**

Do not use a single global `visited` set to discard alternate paths during scoring. It is suitable for reachability/depth discovery, but would incorrectly remove paths that may have a higher score. Keep the depth traversal and path enumeration conceptually separate.

### 7.4 Scoring details

For a path of `k` edges beginning at trigger `t`:

```text
S_eff = (event_severity / 100) * trigger_exposure * (1 - trigger_mitigation)

path_score_0_to_1 =
    S_eff * product(
        edge_weight_i
        * depth_attenuation
        * (1 - mitigation_of_entered_node_i)
    )

path_score_0_to_100 = path_score_0_to_1 * 100
```

For the trigger node itself, the zero-edge path score is `S_eff * 100`. For each downstream edge, apply the entered node's mitigation exactly once. Do not apply the trigger mitigation twice. Round only at the persistence/display boundary: persist to six decimal places on the 0–100 scale and display one decimal place. Keep full precision internally for aggregation and deterministic comparisons.

Validate `depth_attenuation` in the inclusive range 0.0–1.0; default 0.8. Store it in each run. If a configuration sets it to zero, downstream path scores are zero; this is valid and should be tested.

### 7.5 Aggregation details

**`max`:**
- Select the highest-scoring qualifying simple path for each entity.
- On a score tie, select fewer edges.
- If still tied, select lexicographically smaller ordered entity-ID sequence.
- Preserve other qualifying paths as alternatives for explanation, subject to safety limits.

**`capped_sum`:**
- For the final entity, retain the best path for each distinct final dependency edge.
- Sum those path scores and cap at 100.
- A path is not counted twice.
- The primary path is the highest individual contributing path, using the same tie-break rules.
- Explain that the displayed score combines distinct incoming dependency paths and is capped at 100.

Minimum depth is the smallest edge count among qualifying paths from any trigger. It may differ from the primary path's edge count. Display both values when they differ.

### 7.6 Impact levels and confidence

Use D2 thresholds exactly:
- `low`: score below 25;
- `moderate`: 25 to below 50;
- `high`: 50 to below 75;
- `critical`: 75 and above.

Thresholds are stored in every run's configuration. If thresholds become configurable in a later release, validate that they are ordered, non-overlapping and cover the 0–100 range.

Confidence is the weakest review-status value on the primary path. Map `draft=0.5`, `reviewed=0.8`, `validated=1.0`. Display both label and reason. A hypothetical dependency introduced in a scenario counts as draft. Confidence is not probability and must not be multiplied into the impact score.

### 7.7 Explanation requirements

Each result must explain, in plain language:
- which trigger or triggers connect to the entity;
- the primary source → target path;
- relationship labels and edge weights;
- the number of edges in the primary path;
- minimum depth from any trigger;
- event severity, trigger exposure and node mitigation assumptions;
- depth attenuation and aggregation rule;
- weakest dependency review status and confidence meaning;
- any run limit or truncation warning.

Generate explanations from structured facts. Do not use an LLM or free-form generated reasoning as the source of the score. Avoid wording such as “will happen”, “probability”, “certain” or “predicted with X% confidence”.

### 7.8 Cycle and path handling

- Cycles are allowed in stored dependencies.
- A simple path may not repeat an entity.
- A cycle returning to the trigger is not a new affected result.
- A cycle that offers a distinct simple route to another node may be enumerated if within limits.
- Parallel edges between the same ordered entity pair are disallowed by D1.
- A path that reaches an entity through a longer route may be retained as an alternative even if a shorter route already reached it.
- A disconnected entity is not an impact result.
- A trigger entity is depth 0.

### 7.9 Performance and deterministic limits

Begin with NetworkX and in-memory processing. Establish benchmark fixtures with synthetic graph sizes, but report only measured results. Test:
- sparse and dense graphs;
- branching graphs;
- cycles;
- many alternate paths;
- maximum depth;
- path-ceiling and node-ceiling behaviour.

If path enumeration approaches the configured ceiling, stop safely and mark the run incomplete. Do not optimize by silently dropping paths. Any later pruning or approximation requires an ADR, documented semantics and tests.

### 7.10 Required engine test matrix

At minimum test:
1. trigger-only result;
2. one edge;
3. two-edge synopsis example (0.9 × 0.8 × 0.7 × 0.8² = 0.32256, displayed 32.3);
4. edge direction;
5. reverse edge does not propagate;
6. disconnected node;
7. cycle with no repeated node in a path;
8. two paths where the longer path scores higher;
9. equal scores and deterministic tie-breaking;
10. minimum depth differing from primary-path length;
11. `max` aggregation;
12. `capped_sum` by distinct final edge;
13. duplicate path prevention;
14. multiple triggers;
15. trigger exposure and mitigation;
16. entered-node mitigation;
17. draft/reviewed/validated confidence;
18. hypothetical scenario edge confidence;
19. inactive edge;
20. edge outside validity window;
21. archived endpoint;
22. minimum edge weight boundary;
23. maximum depth boundary;
24. score thresholds at 24.999999, 25, 49.999999, 50, 74.999999 and 75;
25. path ceiling and node ceiling;
26. deterministic output and input hash;
27. invalid weights, severity and mitigation;
28. empty graph and missing trigger.

Use explicit expected values; do not test only that a function returns a non-empty list.

---

## 8. API specification

### 8.1 API conventions

- Prefix: `/api/v1`.
- JSON request and response bodies.
- UUID resource identifiers.
- UTC ISO-8601 timestamps.
- Consistent pagination, e.g. `limit` and `cursor` or `limit` and `offset`; choose one approach and document it.
- Stable collection ordering, with an explicit tie-break key.
- Validation errors use a consistent envelope and field-level details.
- Do not expose stack traces, SQL statements, secret values or internal filesystem paths.
- Generate OpenAPI from FastAPI and commit a reviewed snapshot.
- Document authentication requirements and role permissions per endpoint.

Suggested error envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request could not be validated.",
    "details": [],
    "request_id": "..."
  }
}
```

Use appropriate status codes: 400 for malformed business requests where applicable, 401 for missing/invalid authentication, 403 for authenticated members lacking permission, 404 for absent or cross-tenant resources, 409 for state conflicts, 422 for schema validation where FastAPI conventions are retained, and 500 for unexpected server failures. Be consistent and document the chosen distinction between 400 and 422.

### 8.2 Required endpoint groups

The following is the minimum endpoint surface. Adjust exact route names if the repository already has a consistent REST convention, but preserve capability and authorization.

| Resource | Minimum operations |
|---|---|
| Authentication/session | Current user, sign-in/session verification and sign-out as supported by the selected provider |
| Organizations | List memberships; retrieve active organization context; create organization only if onboarding design permits |
| Members | List members; invite/add, change role and deactivate/remove (administrator only) |
| Entities | List, retrieve, create, update, archive |
| Dependencies | List, retrieve, create, update, deactivate/reactivate |
| Events | List, retrieve, create, update, resolve/reopen/archive |
| Event triggers | Add, list and remove trigger associations |
| Analysis | Create/run analysis; retrieve run; list runs; retrieve result and paths |
| Scenarios | Create, retrieve, list, update metadata, discard/archive |
| Scenario changes | Create/update/remove hypothetical event, entity override, dependency override and intervention |
| Scenario analysis | Run scenario; compare against baseline; retrieve comparison |
| Audit | List/filter audit records (administrator only) |
| Health | Liveness and readiness endpoints |

### 8.3 Request and response rules

- Validate all IDs against the active organization.
- Validate dependency direction and prevent self-loops/duplicate ordered pairs.
- Validate time windows and numeric scales.
- Reject unknown fields unless the API's documented compatibility policy says otherwise.
- Use explicit response schemas.
- Do not return secrets or authentication-provider internals.
- Return enough information for the UI to explain an impact without requiring unbounded N+1 requests.
- Paginate large collections and cap maximum page size.
- Use optimistic concurrency or an `updated_at`/version check for edits where lost updates are plausible.

### 8.4 Analysis lifecycle

An analysis request should:
1. validate event ownership and status;
2. authorize the role;
3. load a consistent snapshot of event, triggers, entities and dependencies;
4. resolve `as_of` and configuration defaults;
5. create a run record in `running` state;
6. execute the deterministic engine;
7. persist results, paths, summary and input hash;
8. mark the run `completed` or `completed_with_limits`;
9. write an audit entry;
10. return the run summary and link to its detail endpoint.

If the engine fails, mark the run `failed` with a safe error code and write an audit record. Do not leave a run permanently `running` after an ordinary handled failure. If asynchronous execution is later required, propose it separately; do not introduce a queue without approval.

### 8.5 API documentation and contract tests

- Document every endpoint's purpose, authentication, role requirement, request schema, response schema and errors.
- Include examples using synthetic data only.
- Test OpenAPI generation and ensure the checked-in snapshot changes only with intentional API changes.
- Add contract tests for the frontend's key API shapes.
- Never claim an endpoint is implemented merely because it appears in OpenAPI; verify its behaviour.

---

## 9. Frontend and interaction requirements

### 9.1 Primary navigation

Provide a clear organization-aware application shell with:
- dashboard;
- events;
- dependency model (entities and dependencies);
- ripple analysis/history;
- scenario lab;
- administration (role-gated);
- current organization selector;
- account/session controls.

The active organization must be visible. Switching organization must refresh all tenant-scoped data and clear stale cached records from the previous organization.

### 9.2 Required user journeys

**Journey A — Register an event**
1. Open Events.
2. Create an event with title, description, severity, start time and optional duration.
3. Select one or more trigger entities.
4. Provide rationale/exposure if applicable.
5. Save as draft or open according to role and workflow.
6. See validation and confirmation.

**Journey B — Maintain dependencies**
1. Search/select a source entity and target entity.
2. Choose a relationship type.
3. Set weight and review status.
4. Add rationale and optional validity window.
5. See a directional preview.
6. Save and view the relationship in the graph/list.
7. Receive a clear error for self-loop, duplicate pair or invalid cross-organization reference.

**Journey C — Run ripple analysis**
1. Select an eligible event.
2. Review its trigger entities.
3. Configure maximum depth, minimum edge weight, attenuation and aggregation.
4. Review the “estimate, not probability” notice.
5. Start analysis.
6. See queued/running/completed/failed state as applicable.
7. Inspect summary counts and impact levels.
8. Select a node and inspect its path, assumptions, confidence and alternatives.

**Journey D — Create and compare a scenario**
1. Select a completed baseline run.
2. Create a scenario.
3. Add one or more hypothetical interventions or overrides.
4. Review the assumptions and draft status of hypothetical dependencies.
5. Run scenario analysis.
6. Compare baseline and scenario by entity.
7. Inspect score changes and entities newly affected/no longer reached.
8. Discard/archive the scenario without modifying live records.

### 9.3 Screen requirements

**Dashboard**
- open events and recent runs;
- count of entities/dependencies where useful;
- high/critical estimated impacts from recent completed runs;
- quick actions;
- empty states for a new organization;
- no fabricated analytics or unsupported trend claims.

**Event manager**
- search, filters and stable sorting;
- status and severity indicators;
- create/edit form with validation;
- trigger association editor;
- clear lifecycle actions.

**Entity manager**
- searchable catalogue;
- type, status, exposure and mitigation;
- archive state;
- detail page showing inbound and outbound dependencies with direction explained.

**Dependency editor**
- source and target selectors;
- relationship type, weight, review status and rationale;
- validity window and active state;
- directional preview text: “A change in [source] may affect [target]”;
- validation before submission.

**Ripple analysis**
- run configuration;
- graph canvas and accessible list alternative;
- impact legend and filters;
- summary of affected entities by level;
- clear incomplete-run warning if a safety ceiling was reached;
- run configuration and algorithm version.

**Node detail**
- estimated score and impact level;
- minimum depth and primary-path length;
- primary path with directed arrows;
- contributing paths;
- edge weights and review statuses;
- explanation, assumptions and confidence meaning;
- source event and run metadata.

**Scenario lab**
- baseline selection;
- intervention editor;
- scenario version/history;
- comparison table and graph;
- score deltas;
- explicit “hypothetical only — live data unchanged” notice.

**Administration**
- members and roles;
- organization settings;
- audit history;
- confirmation before destructive membership changes.

### 9.4 UX and accessibility rules

- Use semantic HTML and correct heading order.
- All controls must have labels and keyboard operation.
- Visible focus indicators are required.
- Do not communicate impact level by colour alone.
- Provide sufficient contrast and responsive layouts.
- Use accessible names for graph nodes and edges.
- Provide a non-canvas list/table view for graph content.
- Respect reduced-motion preferences.
- Show loading, empty, error, success and disabled states.
- Confirm destructive actions and explain consequences.
- Preserve form values when a recoverable validation error occurs.
- Avoid unexplained technical terms; provide concise help text for depth, weight, confidence and aggregation.
- Do not use animation that obscures graph direction or impact meaning.

### 9.5 Visual design system

Create a restrained, consistent design system in Figma and implement the approved tokens:
- typography scale;
- spacing scale;
- colour tokens with contrast checks;
- impact-level tokens;
- entity-type markers;
- form and button states;
- graph node/edge styles;
- tables, dialogs, alerts and empty states.

Do not invent research findings to justify a visual choice. Mark unvalidated design assumptions. The graph must remain readable in both light and dark themes if both themes are implemented.

### 9.6 Frontend quality gates

- TypeScript strict mode.
- No unexplained `any`.
- Shared typed API client.
- Component tests for forms, validation, filters and node detail.
- Accessibility checks for primary screens.
- Playwright test for the principal user journey.
- No secrets or privileged database credentials in frontend environment variables.
- No graph scoring logic duplicated in the browser.

---

## 10. Security, privacy and reliability

### 10.1 Authentication and session handling

- Verify authentication server-side.
- Validate issuer, audience, expiry and signature according to the selected provider's official documentation.
- Keep secrets server-side and out of source control.
- Use secure, HttpOnly, SameSite cookies if cookie sessions are selected; document CSRF protection.
- If bearer tokens are used, document storage and refresh behaviour and avoid persistent browser storage for long-lived privileged tokens where a safer option exists.
- Provide a local test identity mechanism only for local/test environments; prevent it from being enabled accidentally in deployed environments.

### 10.2 Tenant isolation

For every tenant-owned query:
- derive organization context from verified membership;
- include organization scope in repository queries;
- verify referenced records share the same organization;
- apply composite database foreign keys;
- test list, retrieve, create, update, archive, analysis and scenario endpoints for cross-tenant access.

Do not rely on UUID unpredictability as authorization. Test both guessed IDs and IDs deliberately obtained from another test tenant.

### 10.3 Input and application security

- Validate and bound all user-controlled strings and numbers.
- Avoid dynamic SQL; use parameterized queries/ORM expressions.
- Protect against mass assignment by using explicit schemas.
- Apply request body and pagination limits.
- Configure CORS to approved origins; do not use wildcard origins with credentials.
- Use secure headers appropriate to the deployment.
- Rate-limit authentication and expensive analysis endpoints if a maintained approved solution is selected; otherwise document the limitation and implement basic application-level bounds.
- Avoid exposing internal exception details.
- Validate uploaded files only if uploads are explicitly approved and implemented; file upload is not required for v1.

### 10.4 Secrets and configuration

- Commit `.env.example` with placeholder values only.
- Ignore `.env`, private keys, tokens, local databases and generated secrets.
- Validate required environment variables at startup.
- Fail closed if a required security setting is missing.
- Never print secret values during diagnostics.
- Use separate local/test/cloud credentials.
- Prefer federated identity for GitHub-to-Azure authentication where supported and approved.
- Never put a Docker Hub or Azure credential in an image layer or build argument.

### 10.5 Audit and data retention

- Audit all successful state-changing operations.
- Keep audit data append-only at application level.
- Define a simple retention recommendation in documentation; do not delete records automatically in v1 without approval.
- Do not collect sensitive personal information not needed for the project.
- Synthetic demo data only.
- Provide a documented local database reset procedure that warns before deleting local records.

### 10.6 Security validation

Required checks:
- secret scan;
- dependency vulnerability audit;
- container image scan;
- authentication and role tests;
- tenant-isolation tests;
- security configuration review;
- migration constraint tests.

Do not suppress a finding merely to make CI green. Record severity, affected dependency/image, remediation or accepted risk, and human approval where needed.

---

## 11. DevOps, containers and delivery

### 11.1 Git collaboration

Use the repository's agreed branch model. If no model exists, recommend:
- `main`: release-ready;
- `develop`: integration branch if team size and workflow justify it;
- `feature/<area>-<slug>`: feature work;
- `fix/<area>-<slug>`: bug fixes;
- `docs/<slug>`: documentation-only work.

Do not commit directly to `main` or `develop`. Use Conventional Commits. PRs must contain purpose, scope, test evidence, screenshots for UI changes, migration notes and an AI-assistance disclosure. Human reviewers own the final approval.

### 11.2 Docker requirements

Create production-oriented Dockerfiles for frontend and backend:
- multi-stage builds where useful;
- pinned dependencies and reproducible installation;
- non-root runtime user where practical;
- minimal runtime image;
- `.dockerignore`;
- no secrets copied into the image;
- health checks where meaningful;
- explicit exposed ports;
- graceful process shutdown.

Use Compose for local `web`, `api` and `db`. A migration service may run before API readiness. Do not publish PostgreSQL to the host in a way that exposes it beyond local development unless required and explicitly documented. Use named volumes for local persistence.

### 11.3 Local Compose acceptance

A fresh clone should be able to:
1. copy `.env.example` to a local `.env`;
2. set only required local values;
3. build images;
4. start services;
5. apply migrations;
6. seed synthetic data;
7. reach the web app and API health endpoint;
8. sign in using the documented local/test mechanism;
9. complete the primary event-to-analysis journey.

Document exact commands and expected outputs. The agent must run these commands when the environment allows. If Docker is unavailable, report that fact and provide commands for the human; do not claim Compose passed.

### 11.4 GitHub Actions

Required PR checks:
- frontend install from lockfile;
- frontend lint and type-check;
- frontend unit/component tests;
- backend install from lockfile;
- backend lint and type-check where configured;
- backend unit and integration tests;
- migration validation;
- Docker build;
- container smoke test where practical;
- dependency/security scan.

Use least-privilege workflow permissions. Pin third-party actions to reviewed immutable commit SHAs where practical. Do not add or change a GitHub Action without approval under Section 2.1. Never use untrusted PR code with write permissions or privileged secrets.

### 11.5 Image tagging and registry

- Use a clear image name for frontend and backend.
- Tag release images with a version and commit SHA.
- Do not rely on `latest` as the only release identifier.
- Record the image digest.
- Build once and promote the same digest.
- Keep local development images distinct from release images.
- Docker Hub may be used for the course's registry practice; ACR is the target for the Azure deployment demonstration.
- Do not push images or authenticate to a registry on the user's behalf without explicit approval.

### 11.6 ACR and ACI

Prepare:
- ACR repository naming and image-tag plan;
- human-executed Azure setup runbook;
- least-privilege identity requirements;
- secret/federated-auth configuration guide;
- ACI deployment manifest or script;
- health-check and verification steps;
- cost and cleanup warnings;
- rollback instructions using a previously published immutable image.

The agent may create and validate local templates and scripts with dry-run behaviour. The human must create cloud resources, configure permissions/secrets, approve costs and execute cloud-changing commands. Do not claim a cloud deployment succeeded until the human provides verifiable output or the approved environment reports success.

### 11.7 Infrastructure as Code

Select Terraform or Bicep, not both for the same resources unless a documented reason exists. Include:
- variables with safe non-secret examples;
- outputs;
- validation;
- resource naming conventions;
- region as an explicit human decision;
- tags for project/environment/owner;
- cost-aware defaults;
- plan/what-if instructions;
- destroy/cleanup instructions.

Never execute `apply`, deployment or resource deletion. The human reviews and runs those operations.

### 11.8 Jenkins and Kubernetes extensions

These are advanced, optional milestones. Complete the baseline GitHub Actions + Docker + ACR + ACI path first.

If approved:
- Jenkins should demonstrate a separate pipeline purpose, not duplicate uncontrolled production deployments.
- Use a local/test Jenkins instance and scoped credentials.
- Kubernetes should begin locally with kind or minikube.
- Include Deployment, Service, ConfigMap, Secret references, probes, resource requests/limits and an optional Ingress.
- Do not put secret values in manifests.
- AKS is optional and requires a separate cost/approval review.
- Keep ACI and AKS instructions distinct; ACI is not Kubernetes.

---

## 12. Implementation phases and gates

The phases below are the authoritative execution sequence. Work on one phase at a time, except Phase 2 UX discovery may proceed in parallel with Phases 3–5 as described. Do not begin the next phase until the human has reviewed the current phase report and explicitly approved continuation.

### Phase 0 — Product definition and repository assessment

**Goal:** remove ambiguity and establish a reviewed baseline without changing application code.

**Tasks**
1. Read the entire master brief, repository instructions and existing project files.
2. Inspect Git status, branch, recent commits and existing structure using read-only commands.
3. Compare repository state with the target architecture; do not overwrite existing work.
4. Create an ambiguity/risk register.
5. Ask the open questions in Appendix F with recommended defaults.
6. Draft ADRs for D1–D30.
7. Define backlog items and acceptance criteria.
8. Create `docs/progress.md` and `docs/viva-notes.md` templates if absent.
9. Identify the local toolchain and versions without installing anything.
10. Present a Phase 0 plan and wait for approval before any write operation.

**Exit criteria**
- Human has approved scope, stack, authentication approach and role model.
- ADRs are drafted and accepted.
- Repository baseline and risks are documented.
- Backlog is ordered.
- No unapproved code or environment changes.

### Phase 1 — Environment and repository foundation

**Goal:** establish a reproducible, runnable skeleton.

**Tasks**
1. Create or confirm frontend and backend skeletons.
2. Add pinned dependency manifests and lockfiles after approval for any new runtime dependencies.
3. Add formatter, linter and type-check configuration.
4. Add `.gitignore`, `.dockerignore` and `.env.example`.
5. Add minimal frontend route/shell and backend health endpoints.
6. Add local Dockerfiles and Compose configuration if Docker is available.
7. Add repository instructions (`AGENTS.md`, Copilot instructions and optional Claude import).
8. Add README setup instructions.
9. Add a minimal CI proposal; request approval before creating/changing workflows.
10. Verify fresh startup and record exact commands/results.

**Exit criteria**
- Frontend and backend start locally.
- Health endpoints behave as documented.
- Lockfiles are committed.
- No secrets are present.
- Fresh-clone instructions are tested or clearly marked unverified if environment limitations prevent testing.

### Phase 2 — UX discovery and Figma (human-led; can run in parallel)

**Goal:** validate the problem and interaction design.

**Agent tasks**
- Prepare interview guide, consent reminder and note-taking template.
- Create hypothesis personas and journey-map templates, clearly labelled as hypotheses.
- Prepare information architecture and task flows.
- Produce low-fidelity screen requirements and a Figma component checklist.
- Review screenshots or exported frames supplied by the human.
- Convert genuine feedback into findings and design changes.

**Human tasks**
- Identify and interview suitable participants.
- Obtain appropriate consent.
- Conduct interviews and record actual observations.
- Create/own the Figma file and clickable prototype.
- Conduct task-based testing and provide actual results.

**Exit criteria**
- A clickable prototype covers event creation → analysis → inspect impact → scenario → comparison.
- Research artefacts distinguish observed evidence from hypotheses.
- Findings and resulting design decisions are documented.
- No fabricated persona, quote, SUS score or usability result.

### Phase 3 — Data foundation and tenancy

**Goal:** implement schema, migrations, membership and tenant boundaries.

**Tasks**
1. Implement core SQLAlchemy models and constraints.
2. Implement Alembic migrations.
3. Implement organization membership and active-organization context.
4. Implement repository methods with mandatory organization scoping.
5. Implement local test authentication adapter.
6. Implement role/permission checks.
7. Implement audit-log persistence.
8. Add synthetic seed data for two organizations.
9. Add database integration tests, including cross-tenant composite-FK failures.
10. Document the data model and security boundaries.

**Exit criteria**
- Fresh migration succeeds.
- CRUD foundations work for authorized users.
- Cross-tenant references fail at database level.
- API/repository tests prove tenant isolation.
- Audit records are written for tested state changes.

### Phase 4 — API foundation

**Goal:** implement the core event, entity and dependency API.

**Tasks**
1. Implement typed request/response schemas.
2. Implement entity CRUD/archive.
3. Implement dependency CRUD/activation and validation.
4. Implement event CRUD/lifecycle.
5. Implement event-trigger associations.
6. Implement filtering, pagination and stable ordering.
7. Implement consistent error responses.
8. Add endpoint authorization and audit logging.
9. Generate and review OpenAPI snapshot.
10. Add API integration tests.

**Exit criteria**
- Required CRUD workflows pass.
- Invalid direction, duplicate edge, self-loop and cross-tenant operations are rejected.
- Role permissions are tested.
- OpenAPI matches actual endpoint behaviour.

### Phase 5 — Ripple engine

**Goal:** implement deterministic, explainable graph analysis.

**Tasks**
1. Define engine input/output types.
2. Write the test matrix in Section 7.10 before implementation.
3. Implement temporal eligibility and graph construction.
4. Implement BFS minimum-depth calculation.
5. Implement bounded simple-path enumeration.
6. Implement D3 scoring and D5/D12 aggregation.
7. Implement confidence and impact-level classification.
8. Implement explanations and safety-limit reporting.
9. Implement canonical input hashing and algorithm versioning.
10. Integrate run persistence and audit logging.
11. Add fixtures for the laboratory and transport scenarios.
12. Benchmark only after correctness tests pass.

**Exit criteria**
- All required deterministic engine tests pass.
- The synopsis numerical example is reproduced.
- Cycles and multiple paths are handled correctly.
- Incomplete runs are never labelled complete.
- Results can be reproduced from the stored snapshot.

### Phase 6 — Frontend integration

**Goal:** complete the primary product workflow.

**Tasks**
1. Implement organization-aware application shell.
2. Implement dashboard and event manager.
3. Implement entity and dependency management.
4. Implement accessible graph visualization.
5. Implement impact summary and node detail.
6. Implement run history and status handling.
7. Implement validation, loading, empty and error states.
8. Connect typed API client.
9. Add component and accessibility tests.
10. Add Playwright test for the principal user journey.

**Exit criteria**
- A user can complete event → dependencies → analysis → inspect result.
- Graph direction matches the API and engine.
- Every impact result is explainable.
- Keyboard/list alternative works.
- No scoring logic is duplicated in the frontend.

### Phase 7 — Scenario simulation and comparison

**Goal:** support isolated what-if analysis.

**Tasks**
1. Implement scenario creation and versioning.
2. Implement event/entity/dependency overlays.
3. Implement intervention types in D15.
4. Ensure hypothetical dependencies count as draft.
5. Run analysis using baseline snapshot plus overlay.
6. Compare baseline and scenario results by entity.
7. Show added, removed and changed impact results.
8. Add isolation tests proving live data is unchanged.
9. Add scenario audit events and documentation.

**Exit criteria**
- Scenario execution does not mutate live operational records.
- Baseline and scenario results are reproducible.
- Comparison shows score deltas and assumptions.
- Discard/archive affects only scenario-owned records.

### Phase 8 — Docker, Compose and CI

**Goal:** produce reproducible local containers and automated validation.

**Tasks**
1. Finalize production Dockerfiles.
2. Finalize Compose services, volumes, health checks and migration sequence.
3. Add smoke tests.
4. Add GitHub Actions only after human approval.
5. Add PR validation stages.
6. Add image build and vulnerability scan.
7. Document registry tagging and digest verification.
8. Test a fresh-clone Compose workflow.
9. Capture actual test/build evidence.

**Exit criteria**
- Local Compose startup is reproducible.
- Images run as documented.
- CI checks pass on the approved branch/PR.
- No secrets are baked into images.
- Evidence reflects actual runs.

### Phase 9 — Azure ACR and ACI deployment

**Goal:** demonstrate the syllabus-aligned cloud container workflow.

**Agent tasks**
- Prepare infrastructure and deployment templates.
- Prepare a human runbook for resource creation, identity, registry publishing, ACI deployment, verification and cleanup.
- Validate templates locally where possible.
- Document expected outputs and troubleshooting.

**Human tasks**
- Confirm account eligibility, region, cost and institutional policy.
- Set budget alerts.
- Create approved Azure resources.
- Configure GitHub/Azure identity and secrets through the approved interface.
- Execute deployment and provide evidence.

**Exit criteria**
- ACR contains the approved versioned images.
- ACI runs the approved image digest.
- Health checks succeed.
- Deployment and rollback steps are documented.
- Cloud costs and cleanup are reviewed.

### Phase 10 — Advanced DevOps (optional)

**Goal:** demonstrate Jenkins and local Kubernetes without delaying the required baseline.

**Tasks, only if approved**
- Jenkins pipeline and secured local/test instance.
- Local Kubernetes manifests or Helm chart.
- Local deployment and health verification.
- Separate ACI versus Kubernetes architecture notes.
- AKS assessment only if time, budget and approval permit.

**Exit criteria**
- Optional demonstrations are reproducible.
- Credentials are not committed.
- No duplicate uncontrolled deployment path exists.
- Optional work has not weakened the core product.

### Phase 11 — Hardening, evaluation and final report

**Goal:** deliver a secure, documented and demonstrable release candidate.

**Tasks**
1. Run full unit, integration, E2E and migration suites.
2. Run security and dependency scans.
3. Review tenant isolation and role matrix.
4. Review accessibility and usability findings.
5. Test backup/restore guidance for local data if included.
6. Review performance using measured test fixtures.
7. Resolve release-blocking defects.
8. Update README, user guide, architecture, runbooks and viva notes.
9. Prepare final demonstration script.
10. Prepare a limitations and future-work section.
11. Assemble evidence index and final phase report.

**Exit criteria**
- Acceptance criteria in Section 13 are met or explicitly reported as not met.
- No known critical security issue is hidden.
- All evidence is genuine and traceable.
- Team can explain the engine, data constraints, CI and deployment.
- Human approves the release candidate.

---

## 13. Acceptance criteria and definition of done

### 13.1 Product acceptance

- A user can authenticate and select an organization.
- Organization members see only their organization's protected data.
- A permitted user can create entities, dependencies and events.
- An event can be linked to one or more trigger entities.
- Dependency direction is consistently source → target.
- An analysis can be configured and executed.
- The engine handles cycles, multiple paths and depth limits deterministically.
- Scores follow D3 and aggregation follows D5/D12.
- Impact level and confidence are displayed separately.
- Each result includes a primary path or a clear trigger-only explanation.
- Run configuration, algorithm version and input snapshot are persisted.
- A scenario can be run without modifying live records.
- Baseline and scenario results can be compared.
- Users can inspect run history and audit records according to role.
- UI communicates that results are estimates, not probabilities.

### 13.2 Engineering acceptance

- Migrations build a fresh database.
- Composite tenant foreign keys reject cross-organization references.
- Backend tests cover authorization and tenant isolation.
- Frontend tests cover primary interactions and validation.
- Playwright covers the primary user journey.
- Engine tests cover all cases in Section 7.10.
- Docker Compose starts the local stack from documented instructions.
- GitHub Actions runs approved PR checks.
- A versioned image can be published to ACR and deployed to ACI by the human.
- Security scans and dependency audits are recorded.
- Documentation reflects the actual implementation.

### 13.3 Academic and evidence acceptance

- Git branches, commits, PRs and reviews demonstrate collaboration.
- CI/CD evidence is captured from actual runs.
- Docker/Compose and ACR/ACI evidence is genuine.
- Figma artefacts and UX research evidence are genuine.
- Jenkins/Kubernetes evidence is included only if implemented.
- Viva notes explain core technical decisions.
- AI assistance is disclosed according to course policy.
- No claim is made that the institution supplied data unless it actually did.

### 13.4 Definition of done for every task

A task is complete only when:
- acceptance criteria are met;
- tests are added or updated;
- relevant checks are run and results recorded;
- documentation is updated;
- migrations and seed data are updated if needed;
- audit logging is present for state-changing endpoints;
- no secrets or unrelated changes are included;
- the change is on an appropriate feature branch;
- a Conventional Commit is created if authorized;
- `docs/progress.md` is current;
- the human can review the result.

---

## 14. Risks, constraints and mitigations

Maintain a living risk register in `docs/progress.md` or `docs/risks.md`.

| Risk | Impact | Required mitigation |
|---|---|---|
| Incomplete or incorrect dependency data | Misleading analysis | Rationale, review status, data ownership and visible confidence |
| Heuristic interpreted as probability | False certainty | Consistent estimate language and explicit assumptions |
| Cycles/multiple paths | Infinite traversal or inflated scores | Simple-path bounds, deterministic aggregation and tests |
| Path explosion | Resource exhaustion | Node/path ceilings and incomplete-run status |
| Tenant leakage | Data exposure | Composite FKs, scoped repositories and adversarial tests |
| Scenario mutates live data | Operational corruption | Separate overlay tables and isolation tests |
| AI-generated defects | Incorrect implementation | Tests-first, review and viva-level understanding |
| Cloud cost | Unexpected charges | Budget alerts, short-lived demo resources and cleanup runbook |
| Credential exposure | Account compromise | Secret handling rules and federated identity where supported |
| Team merge conflicts | Delays and regressions | Module ownership, small PRs and agreed API contracts |
| Scope expansion | Core release delayed | MUST-first sequencing; optional Jenkins/Kubernetes only after baseline |
| Tool/version drift | Broken builds | Pin versions, lockfiles and official documentation checks |
| Unvalidated UX | Poor usability | Real task-based tests and documented revisions |
| Deployment drift | Different environments | Immutable image digest and recorded configuration |

The agent must add newly discovered risks with likelihood, impact, mitigation, owner and status. Do not invent numeric risk scores without an agreed scale.

---

## 15. Required final deliverables

The final repository should contain the following, with status clearly marked as complete, partial or not implemented.

### Product
- Working Ripple Effect web application.
- Event, entity and dependency management.
- Explainable ripple analysis.
- Run history and audit log.
- Scenario simulation and comparison.
- Two synthetic demonstration organizations/scenarios.

### Source control and collaboration
- GitHub repository.
- Branch and review policy.
- Issues/PR evidence where used.
- Conventional Commit history.
- Release tag and notes.

### Architecture and engineering
- System architecture and data model.
- ADRs for approved design decisions.
- Engine algorithm and test documentation.
- OpenAPI snapshot.
- Migration history.
- Viva notes.

### UX
- Hypothesis personas and validated research findings kept distinct.
- User journeys and task flows.
- Wireframes.
- Figma design system.
- High-fidelity screens.
- Clickable prototype.
- Usability test evidence and resulting changes.

### Delivery
- Frontend and backend Dockerfiles.
- Compose file and local run guide.
- GitHub Actions workflows.
- Container scan and test evidence.
- ACR/ACI runbook and human-provided deployment evidence.
- Terraform or Bicep templates and safe execution instructions.
- Optional Jenkins/Kubernetes artefacts only if completed.

### Documentation
- README and quick start.
- Environment variable reference.
- User guide.
- Developer guide.
- Architecture and ADRs.
- API documentation.
- Troubleshooting guide.
- Security and tenant-isolation notes.
- Deployment and rollback runbooks.
- Evidence index.
- Final report and demo script.

---

## 16. Final operating instruction to the coding agent

You are responsible for engineering quality, not for bypassing human control.

At the beginning of each task:
1. Read `AGENTS.md`, `docs/progress.md` and the relevant phase section.
2. Restate the task, acceptance criteria and files likely to change.
3. Identify dependencies, risks and approvals needed.
4. For logic-heavy work, write tests first.
5. Make the smallest coherent change.
6. Run checks and report exact outcomes.
7. Update documentation and progress.
8. Stop at the phase boundary and submit the report in Appendix H.

Do not:
- assume approval from silence;
- perform cloud or remote Git operations;
- read or expose secrets;
- change authentication, role or tenant-isolation semantics without approval;
- fabricate research, benchmark, test or deployment evidence;
- hide failed checks;
- begin a later phase before explicit approval.

If blocked, ask one precise question with a recommended default. If the human's answer changes a binding decision, update the relevant ADR and progress log before implementation.

---

# Appendices

## Appendix A — Always-loaded repository instructions (`AGENTS.md`)

Copy the following block into the repository-root `AGENTS.md`. Mirror it to `.github/copilot-instructions.md`. For Claude Code, create a `CLAUDE.md` that imports or points to `AGENTS.md`.

```markdown
# Ripple Effect — Agent Operating Instructions

## Source of truth
- Read `docs/agent-brief.md` before project work.
- Follow approved decisions and phase gates in that brief.
- Read `docs/progress.md` and the current phase before resuming.
- If the brief and repository disagree, report the conflict; do not silently rewrite either.

## Autonomy
- Work only inside the project workspace.
- Read-only inspection is allowed before kickoff approval.
- After approval, local edits, tests, formatters, local branches and local commits are allowed.
- Ask before adding runtime dependencies or GitHub Actions, changing auth/authorization/tenant isolation, using network access beyond approved registries/docs, or performing remote Git operations.
- Never deploy, create/change/delete cloud resources, change GitHub settings/secrets, use sudo, force-push shared branches, disable checks, or expose secrets.
- Never commit directly to main or develop.

## Engineering workflow
- Restate task and acceptance criteria.
- Write tests first for graph/authorization logic.
- Make small, reviewable changes.
- Run relevant format, lint, type-check, test and build commands.
- Fix root causes; do not suppress failures.
- Update docs, migrations, OpenAPI and `docs/progress.md`.
- Use Conventional Commits on `feature/<area>-<slug>` branches.

## Product invariants
- A dependency source -> target means a change in source may affect target.
- Scores are heuristic estimates, never probabilities.
- Preserve path provenance, deterministic aggregation and bounded cycle-safe traversal.
- Confidence measures dependency review quality, not likelihood.
- Scenarios must not mutate live records.
- Every tenant-owned record and reference is organization-scoped.
- Non-members receive 404 for tenant-owned resources; unauthorized members receive 403.
- Every state-changing endpoint is audited.

## Evidence integrity
- Never fabricate interviews, personas as validated facts, usability scores, tests, benchmarks, screenshots, CI or cloud results.
- Mark missing human evidence as TODO(human).
- Record copied material and its licence.
- Include AI-assistance disclosure in PR descriptions according to course policy.

## Phase discipline
- Work one approved phase at a time.
- Stop at the end of each phase and submit Appendix H's phase report.
- Do not proceed until the human explicitly approves.
```

## Appendix B — Kickoff message

Send this message after placing the complete brief at `docs/agent-brief.md`:

> You are the lead engineer on Ripple Effect, a full-stack, DevOps-ready dependency and impact-analysis platform. The complete build brief is in `docs/agent-brief.md`; read all of it before you act.
>
> Then:
> 1. Summarise your understanding in at most 15 lines.
> 2. List every ambiguity, conflict or risk you found, each with a recommended resolution.
> 3. Ask me the open questions listed in Appendix F, each with your recommended default.
> 4. Inspect the repository using read-only commands only.
> 5. Propose a checklist plan for Phase 0 and Phase 1.
>
> Do not change files, install anything, create branches or run any command except read-only inspection until I reply exactly “approved”. Do not infer approval from this message. After approval, work one phase at a time under Section 2, keep `docs/progress.md` current, and finish every phase with the report in Appendix H.

## Appendix C — Synthetic demonstration datasets

All records below are illustrative synthetic data. They are not supplied by NIE Mysuru and do not represent actual campus schedules, roads, people or operational records. Use generated UUIDs and synthetic labels in seed scripts. Keep the graph engine domain-neutral.

### C1. Organization A — Campus operations

Organization: `North Campus Demo` (synthetic).

Suggested entities:
- `AC-LAB`: Advanced Computing Laboratory (resource).
- `SESSION-A`: Practical Session A (activity).
- `SESSION-B`: Practical Session B (activity).
- `BATCH-1`: Student Batch 1 (group).
- `BATCH-2`: Student Batch 2 (group).
- `LAB-B`: Alternative Laboratory B (resource).
- `LAB-C`: Alternative Laboratory C (resource).
- `SLOT-1`: Afternoon Slot 1 (activity/resource-capacity representation).
- `SLOT-2`: Afternoon Slot 2 (activity/resource-capacity representation).
- `TIMETABLE`: Shared Timetable (system).

Suggested directed dependencies:
- `AC-LAB -> SESSION-A`, relationship `hosts`, weight 0.90, reviewed.
- `AC-LAB -> SESSION-B`, relationship `hosts`, weight 0.85, validated.
- `SESSION-A -> BATCH-1`, relationship `affects`, weight 0.80, reviewed.
- `SESSION-B -> BATCH-2`, relationship `affects`, weight 0.80, reviewed.
- `SESSION-A -> TIMETABLE`, relationship `updates`, weight 0.60, draft.
- `SESSION-B -> TIMETABLE`, relationship `updates`, weight 0.60, draft.
- `LAB-B -> SLOT-1`, relationship `provides_capacity_for`, weight 0.75, reviewed.
- `LAB-C -> SLOT-2`, relationship `provides_capacity_for`, weight 0.70, reviewed.
- `TIMETABLE -> SLOT-1`, relationship `schedules`, weight 0.50, draft.
- `TIMETABLE -> SLOT-2`, relationship `schedules`, weight 0.50, draft.

Treat these as example relationships, not as a complete or necessarily realistic timetable model. If the demonstration needs a relocation chain, model the capacity conflict explicitly as synthetic entities and dependencies. Do not assume that a free slot exists merely because it appears in the seed list.

Suggested event:
- Title: `Advanced Computing Laboratory unavailable`.
- Description: `Synthetic electrical-maintenance closure for demonstration`.
- Severity: 90.
- Start time: a fixed documented timestamp in the seed fixture.
- Duration: 3 days (informational only in v1).
- Status: open.
- Trigger: `AC-LAB`, exposure 1.0.

Demonstration questions:
1. Which scheduled sessions are directly connected to the laboratory?
2. Which batches may be affected through those sessions?
3. Which paths have the highest estimated impact?
4. Which dependencies have lower review confidence?
5. What changes when a hypothetical alternative-lab dependency or mitigation is added?
6. Does the scenario leave live records unchanged?

### C2. Organization B — Transport operations

Organization: `City Transport Demo` (synthetic).

Suggested entities:
- `ROAD-X`: Road Segment X (location/resource).
- `ROUTE-1`: Bus Route 1 (activity/system).
- `ROUTE-2`: Bus Route 2 (activity/system).
- `STOP-A`: Stop A (location).
- `STOP-B`: Stop B (location).
- `COMMUTE-GROUP`: Commuter Group (group).
- `CONNECTION`: Transfer Connection (activity).
- `SCHEDULE`: Transport Schedule (system).

Suggested dependencies:
- `ROAD-X -> ROUTE-1`, relationship `affects`, weight 0.90, reviewed.
- `ROAD-X -> ROUTE-2`, relationship `affects`, weight 0.70, draft.
- `ROUTE-1 -> STOP-A`, relationship `serves`, weight 0.80, reviewed.
- `ROUTE-2 -> STOP-B`, relationship `serves`, weight 0.80, reviewed.
- `STOP-A -> CONNECTION`, relationship `enables`, weight 0.65, draft.
- `CONNECTION -> COMMUTE-GROUP`, relationship `affects`, weight 0.75, reviewed.
- `ROUTE-1 -> SCHEDULE`, relationship `updates`, weight 0.50, draft.

Suggested event:
- Title: `Road Segment X closed`.
- Description: `Synthetic road-closure scenario`.
- Severity: 80.
- Start time: fixed timestamp in fixture.
- Status: open.
- Trigger: `ROAD-X`.

### C3. Seed-data requirements

- Create two organizations with separate memberships and records.
- Use at least two test users where possible: one member of Organization A and one member of Organization B. Add a cross-tenant test user only if the auth fixture supports it safely.
- Demonstrate that one organization cannot retrieve or reference the other's records.
- Keep all seed IDs stable in test fixtures or resolve them by unique synthetic keys.
- Include at least one inactive dependency, one expired/future-valid dependency, one archived entity and one draft dependency for temporal/review tests.
- Include a small cycle and multiple distinct paths in engine-only fixtures; do not distort the main demonstration merely to force every edge case into it.
- Seed scripts must state that all records are synthetic.

## Appendix D — Required architecture decision records

Create one ADR per decision, using a consistent format:

```markdown
# ADR-NNN: <Decision title>

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Decision owners: TODO(human)

## Context
What problem or ambiguity requires a decision?

## Decision
What is being decided?

## Alternatives considered
List credible alternatives and why they were not selected.

## Consequences
Benefits, trade-offs, constraints and follow-up work.

## Evidence
Documentation, tests or project requirements supporting the decision.
```

At minimum create ADRs for:
- D1 edge direction and uniqueness;
- D2 scales and impact levels;
- D3 scoring formula;
- D4 depth definition;
- D5 aggregation;
- D6 confidence semantics;
- D7 temporal eligibility;
- D8 tenant isolation;
- D9 multi-trigger input;
- D11 bounded path enumeration;
- D14 scenario isolation;
- D18 REST/OpenAPI contract;
- D19 authentication adapter/provider;
- D21 role permission matrix;
- D23 persistence/ORM/migrations;
- D24 frontend stack;
- D28 deployment baseline;
- package manager and lockfile choice;
- any material deviation from this brief.

An ADR may reference several closely related decisions only if the reasoning remains clear and reviewable. Do not create an ADR that claims a human approved a decision when approval has not occurred.

## Appendix E — Human-only work and approval checklist

The agent may prepare instructions and templates. The human performs the following actions.

### E1. Research and UX
- Identify appropriate interview participants.
- Obtain consent and conduct interviews.
- Record actual observations and anonymize notes where appropriate.
- Create and own the Figma project.
- Validate prototype tasks with participants.
- Provide genuine usability findings and revisions.

### E2. Accounts and cloud
- Confirm GitHub repository ownership and team membership.
- Create/use Docker Hub account if required by the course.
- Confirm Azure account eligibility and institutional policy.
- Review current ACR, ACI and networking costs.
- Configure budget alerts before provisioning.
- Select region and resource group.
- Create cloud resources and role assignments.
- Configure federated identity or approved secrets.
- Execute ACR push and ACI deployment.
- Verify deployment and perform cleanup when no longer required.

### E3. Repository governance
- Configure branch protection/rulesets.
- Configure required reviewers and status checks.
- Configure GitHub environments and secrets.
- Approve workflow permissions.
- Review and merge pull requests.
- Push branches and tags where the agent has not been explicitly authorized to do so.

### E4. Academic integrity
- Check course policy on AI assistance.
- Review generated code and documentation.
- Ensure every team member can explain submitted work.
- Confirm that research, screenshots and results are genuine.
- Approve the final report and presentation.

### E5. Human approval record

Keep a record in `docs/evidence/approvals.md` containing:
- item requiring approval;
- date;
- approver/team role;
- decision;
- relevant PR/ADR/runbook;
- conditions or expiry, if any.

Do not store passwords, tokens or secret values in this file.

## Appendix F — Phase 0 open questions

Ask these questions before implementation. Provide a recommended default for each and explain any consequence of choosing differently. Do not ask questions whose answers are already explicitly fixed by D1–D30.

1. **Repository state:** Is there an existing repository and codebase to preserve, and which branch is the agreed integration branch? Default: inspect and preserve the current repository; use `develop` only if the team already uses it, otherwise branch from the agreed shared baseline.
2. **Team workflow:** How many contributors will actively commit, and who reviews PRs? Default: feature branches and at least one human review for every PR; do not enforce a complex Gitflow if the team is very small.
3. **Authentication provider:** Is Supabase Auth required, or should the first release use a local adapter with a later provider integration? Default: local test adapter behind an interface; select Supabase only after the team confirms account and deployment requirements.
4. **Frontend styling:** Is Tailwind CSS acceptable, or does the team already have a UI library? Default: Tailwind with accessible reusable components, subject to dependency approval.
5. **Python and Node versions:** Are there course/lab machine constraints? Default: choose currently maintained LTS/stable versions compatible with dependencies, pin them in project configuration and document them.
6. **Package managers:** Does the team prefer npm and uv, or already have lockfiles? Default: preserve existing lockfiles; for a new repository use npm and uv if compatible with the team environment.
7. **Deployment target:** Is Azure ACR + ACI available through a student/institutional subscription? Default: build and test locally first; prepare ACR/ACI runbooks but do not provision until account, cost and policy are confirmed.
8. **Registry practice:** Does the course require Docker Hub in addition to ACR? Default: support Docker Hub practice separately if required, while keeping ACR as the Azure deployment registry.
9. **UX participants:** Which participant groups can the team legitimately interview? Default: students and relevant coordinators who voluntarily agree; label personas as hypotheses until validated.
10. **Data scope:** Is synthetic data sufficient for the demonstration? Default: yes; do not request or import real institutional data.
11. **Optional extensions:** Is there enough time for Jenkins and Kubernetes after the required ACI milestone? Default: defer until all MUST criteria and the ACI demonstration are complete.
12. **Report format:** Does the course prescribe a report/presentation format or rubric? Default: follow the institution's official format if supplied; otherwise use the deliverable list in Section 15.

After the human answers, summarize the accepted choices in `docs/progress.md` and create/update ADRs. Ask one additional question only if a new material blocker is discovered.

## Appendix G — Traceability and final acceptance checklist

Use this checklist during Phase 11. Mark each item `PASS`, `FAIL`, `NOT RUN` or `NOT APPLICABLE`, and attach evidence references. Never mark a check PASS based only on code inspection if execution is required.

| ID | Requirement | Evidence required |
|---|---|---|
| G-01 | Fresh local setup documented | Commands and observed startup output |
| G-02 | Frontend and backend start | Local verification log |
| G-03 | Database migrations work from empty DB | Migration test output |
| G-04 | Two organizations seeded | Seed output and fixture reference |
| G-05 | Tenant composite constraints enforced | Database integration test |
| G-06 | Role permissions enforced | API authorization tests |
| G-07 | Event CRUD and trigger associations work | API/UI test |
| G-08 | Entity CRUD/archive works | API/UI test |
| G-09 | Dependency direction and validation work | API/UI test |
| G-10 | Engine numerical example matches 32.256/32.3 | Unit test |
| G-11 | Cycles and multiple paths work | Engine tests |
| G-12 | Depth and edge thresholds work | Engine tests |
| G-13 | Confidence semantics correct | Engine/UI tests |
| G-14 | Incomplete-run limits are visible | Engine/API/UI test |
| G-15 | Run snapshot and algorithm version stored | Persistence test |
| G-16 | Scenario does not mutate live data | Isolation test |
| G-17 | Baseline/scenario comparison works | Integration/E2E evidence |
| G-18 | Audit records created | API/database test |
| G-19 | Graph has accessible alternative | Accessibility review/test |
| G-20 | Primary user journey works | Playwright report |
| G-21 | Docker Compose reproducible | Build/start/smoke output |
| G-22 | CI checks run on PR | GitHub Actions run URL or exported evidence |
| G-23 | Image tags/digests documented | Registry evidence |
| G-24 | ACR/ACI deployment verified | Human-provided deployment evidence |
| G-25 | Security/dependency scans reviewed | Scan reports and disposition |
| G-26 | UX research is genuine | Anonymized notes and method |
| G-27 | Figma prototype exists | Link/screenshots supplied by human |
| G-28 | Viva notes cover core concepts | `docs/viva-notes.md` review |
| G-29 | Limitations documented | Final limitations section |
| G-30 | AI assistance disclosed appropriately | PR/report disclosure |

### G.1 Traceability rules

- Link each acceptance criterion to one or more tests, documents or evidence files.
- Use stable IDs in issues or test names where practical.
- A requirement not implemented must be marked as such, with reason and impact.
- Do not remove a failed criterion from the table to improve the apparent result.
- Include date and software revision/commit for test evidence.
- Distinguish local test evidence from cloud deployment evidence.

## Appendix H — Mandatory phase report template

At the end of every phase, stop and submit a report in this format. Update `docs/progress.md` before reporting.

```markdown
# Phase N Report — <Phase name>

## 1. Objective
Restate the phase goal and its approved scope.

## 2. Work completed
- List concrete files, modules, endpoints, tests or runbooks created/changed.
- Distinguish implemented work from documentation-only work.

## 3. Decisions
- List decisions made under existing ADRs.
- List new ADRs proposed or updated.
- Identify anything that still requires human approval.

## 4. Verification performed
| Command/check | Result | Evidence |
|---|---|---|
| `<exact command>` | PASS / FAIL / NOT RUN | `<output, report or reason>` |

Do not report a command as passed unless it was actually executed successfully.

## 5. Test results
- Tests run:
- Passed:
- Failed:
- Skipped:
- Coverage, only if actually measured:
- Known gaps:

## 6. Security and data integrity
- Tenant-isolation checks:
- Authorization checks:
- Secret scan:
- Dependency/container scan:
- Audit-log checks:
- Any unresolved concern:

## 7. Evidence integrity
- Evidence produced:
- Evidence still TODO(human):
- Any hypotheses that remain unvalidated:
- Any claims intentionally not made:

## 8. Deviations and blockers
- Deviations from the brief:
- Why they were necessary:
- Approval status:
- Blockers and recommended resolution:

## 9. Progress file
Confirm `docs/progress.md` includes:
- Done
- In progress
- Next
- Blockers
- Verification commands/results
- Decisions/ADRs
- Current branch and commit, if applicable

## 10. Human review required
List the exact items the human must inspect or approve.

## 11. Phase exit assessment
- Exit criteria met: YES / PARTIAL / NO
- Evidence-backed explanation:
- Recommended next phase:

STOP HERE. Do not begin the next phase until the human explicitly approves.
```

## Appendix I — `docs/progress.md` starter template

```markdown
# Ripple Effect — Project Progress

- Last updated: TODO
- Current phase: Phase 0
- Current branch: TODO
- Current commit: TODO
- Overall status: Not started / In progress / Blocked

## Done
- TODO

## In progress
- TODO

## Next
- TODO

## Blockers
- TODO

## Verification
| Date | Command/check | Result | Notes |
|---|---|---|---|
| TODO | TODO | NOT RUN | TODO |

## Decisions and ADRs
- TODO

## Human actions pending
- TODO

## Evidence index
- TODO

## Session handoff
- Last completed task:
- Exact next task:
- Files to read first:
- Commands to verify:
- Approval needed:
```

## Appendix J — Viva notes starter outline

Maintain `docs/viva-notes.md` as a practical explanation, not a copied textbook.

For every concept, record:
- what it means in this project;
- why it was selected;
- where it is implemented (file/module);
- a short example;
- how it is tested;
- a limitation or trade-off.

Required topics:
1. Directed graphs and source → target dependency semantics.
2. BFS and minimum propagation depth.
3. Bounded simple-path enumeration and cycle safety.
4. Impact scoring, attenuation and mitigation.
5. Max versus capped-sum aggregation.
6. Confidence as dependency-data quality.
7. Composite foreign keys and tenant isolation.
8. Authentication versus authorization.
9. REST API and OpenAPI.
10. Database migrations and seed data.
11. Scenario overlays and immutable baseline data.
12. Audit logging and transaction boundaries.
13. React component architecture and React Flow.
14. Docker images, layers and Compose networking.
15. Git branches, commits, PRs and review.
16. CI stages and quality gates.
17. Image tags versus immutable digests.
18. ACR and ACI deployment.
19. Infrastructure as Code and plan/apply separation.
20. Security scanning and secret management.

Mark any topic not yet implemented as `PLANNED` rather than describing it as completed.

---

**End of continuation.** Append this material after D8 in `docs/agent-brief.md`. The existing Sections 1–4 and this continuation together constitute the master build brief.
