export type Page<T> = {
  items: T[];
  limit: number;
  offset: number;
  total: number;
};

export type EntityType =
  | "person"
  | "department"
  | "resource"
  | "activity"
  | "system"
  | "location"
  | "group";

export type Entity = {
  id: string;
  name: string;
  description: string | null;
  entity_type: EntityType;
  status: "active" | "inactive" | "archived";
  exposure: number;
  mitigation: number;
  attributes: Record<string, unknown>;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Dependency = {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  relationship_label: string;
  weight: number;
  rationale: string | null;
  review_status: "draft" | "reviewed" | "validated";
  is_active: boolean;
  valid_from: string | null;
  valid_until: string | null;
  created_at: string;
  updated_at: string;
};

export type EventRecord = {
  id: string;
  title: string;
  description: string | null;
  severity: number;
  start_at: string;
  duration_minutes: number | null;
  status: "draft" | "open" | "resolved" | "archived";
  created_at: string;
  updated_at: string;
};

export type EventTrigger = {
  id: string;
  event_id: string;
  entity_id: string;
  exposure: number;
  rationale: string | null;
  created_at: string;
};

export type AnalysisRun = {
  id: string;
  organization_id: string;
  event_id: string;
  scenario_id: string | null;
  status:
    | "pending"
    | "running"
    | "completed"
    | "completed_with_limits"
    | "incomplete"
    | "failed";
  configuration: Record<string, unknown>;
  algorithm_version: string;
  input_hash: string;
  as_of: string;
  summary: Record<string, unknown>;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type Scenario = {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  baseline_run_id: string | null;
  status: "draft" | "archived";
  version: number;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type ScenarioDetail = Scenario & {
  event_overlay: {
    event: {
      id: string;
      title: string;
      status: EventRecord["status"];
      severity: number;
      start_at: string;
    };
    triggers: Array<{
      entity_id: string;
      exposure: number;
      rationale: string | null;
    }>;
  };
  entity_overrides: Array<{
    id: string;
    entity_id: string;
    exposure: number | null;
    mitigation: number | null;
    status: Entity["status"] | null;
    rationale: string | null;
  }>;
  dependency_overrides: Array<{
    id: string;
    dependency_id: string | null;
    source_entity_id: string | null;
    target_entity_id: string | null;
    relationship_type: string | null;
    relationship_label: string | null;
    weight: number | null;
    is_active: boolean | null;
    review_status: Dependency["review_status"] | null;
    rationale: string | null;
  }>;
  interventions: ScenarioIntervention[];
};

export type ScenarioInterventionType =
  | "mitigation"
  | "weight_override"
  | "deactivate_dependency"
  | "hypothetical_dependency";

export type ScenarioIntervention = {
  id: string;
  scenario_id: string;
  title: string;
  action_type: ScenarioInterventionType;
  target_entity_id: string | null;
  target_dependency_id: string | null;
  rationale: string;
  assumptions: Record<string, unknown>;
  author_user_id: string;
  created_at: string;
};

export type ScenarioComparison = {
  scenario_id: string;
  baseline_run_id: string;
  scenario_run_id: string;
  scenario_version: number;
  baseline_status: AnalysisRun["status"];
  scenario_status: AnalysisRun["status"];
  potentially_incomplete: boolean;
  estimated_effect: {
    baseline_total_score: number;
    scenario_total_score: number;
    score_delta: number;
  };
  assumptions: ScenarioIntervention[];
  items: Array<{
    entity_id: string;
    entity_name: string;
    change_type: "added" | "removed" | "changed" | "unchanged";
    baseline_score: number;
    scenario_score: number;
    delta: number;
  }>;
};

export type ImpactResult = {
  id: string;
  run_id: string;
  entity_id: string;
  entity_name: string;
  entity_type: EntityType;
  depth: number;
  score: number;
  impact_level: "low" | "moderate" | "high" | "critical";
  confidence_value: number;
  confidence_label: "low" | "medium" | "high";
  confidence_reason: string;
  primary_path_id: string | null;
  trigger_entity_ids: string[];
  explanation: string;
  result_flags: Record<string, unknown>;
};

export type ImpactPathStep = {
  entity_id: string;
  entity_name: string;
  entity_type: EntityType;
  mitigation: number;
  dependency_id: string | null;
  relationship_type: string | null;
  relationship_label: string | null;
  weight: number | null;
  review_status: "draft" | "reviewed" | "validated" | null;
  rationale: string | null;
  is_hypothetical: boolean;
};

export type ImpactPath = {
  id: string;
  run_id: string;
  entity_id: string;
  trigger_entity_id: string;
  score: number;
  edge_count: number;
  is_primary: boolean;
  provenance: {
    entity_ids: string[];
    entity_names: string[];
    dependency_labels: string[];
    dependency_types: string[];
    weights: number[];
    review_statuses: string[];
    steps: ImpactPathStep[];
    [key: string]: unknown;
  };
};

export type ApiConfig = {
  baseUrl: string;
  userId: string;
  organizationId: string;
};

export type ApiErrorDetail = {
  field: string;
  message: string;
  code: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly requestId: string | null,
    readonly details: ApiErrorDetail[],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function errorFromPayload(
  payload: unknown,
  status: number,
  requestId: string | null,
) {
  if (isRecord(payload) && isRecord(payload.error)) {
    const body = payload.error;
    const details = Array.isArray(body.details)
      ? body.details.filter(
          (detail): detail is ApiErrorDetail =>
            isRecord(detail) &&
            typeof detail.field === "string" &&
            typeof detail.message === "string" &&
            typeof detail.code === "string",
        )
      : [];
    const detailMessage = details
      .map((detail) => `${detail.field}: ${detail.message}`)
      .join("; ");
    const message =
      typeof body.message === "string"
        ? body.message
        : "The API request failed.";
    return new ApiError(
      detailMessage ? `${message} ${detailMessage}` : message,
      status,
      typeof body.code === "string" ? body.code : "request_error",
      typeof body.request_id === "string" ? body.request_id : requestId,
      details,
    );
  }

  return new ApiError(
    "The API returned an unsuccessful response without its documented error details.",
    status,
    "request_error",
    requestId,
    [],
  );
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetcher: typeof fetch;

  constructor(
    private readonly config: ApiConfig,
    fetcher?: typeof fetch,
  ) {
    this.baseUrl = config.baseUrl.trim().replace(/\/+$/, "");
    this.fetcher = fetcher ?? globalThis.fetch.bind(globalThis);
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const url = this.baseUrl ? `${this.baseUrl}${path}` : path;
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    headers.set("X-Local-User-ID", this.config.userId);
    headers.set("X-Active-Organization-ID", this.config.organizationId);
    if (init.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }

    const response = await this.fetcher(url, { ...init, headers });
    const requestId = response.headers.get("X-Request-ID");
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      if (!response.ok) {
        throw new ApiError(
          `The API request failed with HTTP ${response.status} and an unreadable response.`,
          response.status,
          "invalid_error_response",
          requestId,
          [],
        );
      }
      throw new ApiError(
        "The API returned a response that could not be decoded as JSON.",
        response.status,
        "invalid_success_response",
        requestId,
        [],
      );
    }

    if (!response.ok) {
      throw errorFromPayload(payload, response.status, requestId);
    }
    return payload as T;
  }

  private page<T>(path: string, params = new URLSearchParams()) {
    params.set("limit", "100");
    return this.request<Page<T>>(`${path}?${params.toString()}`);
  }

  health() {
    return this.request<{ status: string }>("/api/v1/health/ready");
  }

  listEntities() {
    return this.page<Entity>("/api/v1/entities");
  }

  listDependencies() {
    return this.page<Dependency>("/api/v1/dependencies");
  }

  listEvents() {
    return this.page<EventRecord>("/api/v1/events");
  }

  createEntity(payload: {
    name: string;
    entity_type: EntityType;
    description?: string;
  }) {
    return this.request<Entity>("/api/v1/entities", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  updateEntity(
    entityId: string,
    payload: {
      expected_updated_at: string;
      name: string;
      entity_type: EntityType;
      description: string;
      exposure: number;
      mitigation: number;
    },
  ) {
    return this.request<Entity>(`/api/v1/entities/${entityId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  archiveEntity(entityId: string, expectedUpdatedAt: string) {
    const params = new URLSearchParams({
      expected_updated_at: expectedUpdatedAt,
    });
    return this.request<Entity>(
      `/api/v1/entities/${entityId}?${params.toString()}`,
      { method: "DELETE" },
    );
  }

  createDependency(payload: {
    source_entity_id: string;
    target_entity_id: string;
    relationship_type: string;
    relationship_label?: string;
    weight: number;
    rationale?: string;
    review_status: "draft" | "reviewed" | "validated";
  }) {
    return this.request<Dependency>("/api/v1/dependencies", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  updateDependency(
    dependencyId: string,
    payload: {
      expected_updated_at: string;
      source_entity_id: string;
      target_entity_id: string;
      relationship_type: string;
      relationship_label: string;
      weight: number;
      rationale: string;
      review_status: "draft" | "reviewed" | "validated";
    },
  ) {
    return this.request<Dependency>(`/api/v1/dependencies/${dependencyId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  setDependencyActive(
    dependencyId: string,
    payload: { expected_updated_at: string; is_active: boolean },
  ) {
    return this.request<Dependency>(
      `/api/v1/dependencies/${dependencyId}/activation`,
      { method: "PATCH", body: JSON.stringify(payload) },
    );
  }

  createEvent(payload: {
    title: string;
    description?: string;
    severity: number;
    start_at: string;
    status: "draft";
  }) {
    return this.request<EventRecord>("/api/v1/events", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  updateEvent(
    eventId: string,
    payload: {
      expected_updated_at: string;
      title: string;
      description: string;
      severity: number;
      start_at: string;
    },
  ) {
    return this.request<EventRecord>(`/api/v1/events/${eventId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  listTriggers(eventId: string) {
    return this.page<EventTrigger>(`/api/v1/events/${eventId}/triggers`);
  }

  addTrigger(
    eventId: string,
    payload: { entity_id: string; exposure: number },
  ) {
    return this.request<EventTrigger>(`/api/v1/events/${eventId}/triggers`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  updateEventStatus(
    eventId: string,
    payload: { expected_updated_at: string; status: "open" },
  ) {
    return this.request<EventRecord>(`/api/v1/events/${eventId}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  listRuns(eventId: string) {
    const params = new URLSearchParams({ event_id: eventId, limit: "100" });
    return this.page<AnalysisRun>("/api/v1/analysis-runs", params);
  }

  listScenarioRuns(scenarioId: string) {
    const params = new URLSearchParams({
      scenario_id: scenarioId,
      limit: "100",
    });
    return this.page<AnalysisRun>("/api/v1/analysis-runs", params);
  }

  listScenarios() {
    return this.page<Scenario>("/api/v1/scenarios");
  }

  getScenario(scenarioId: string) {
    return this.request<ScenarioDetail>(`/api/v1/scenarios/${scenarioId}`);
  }

  createScenario(payload: {
    name: string;
    description?: string;
    baseline_run_id: string;
  }) {
    return this.request<Scenario>("/api/v1/scenarios", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  updateScenarioEvent(
    scenarioId: string,
    payload: {
      expected_version: number;
      title?: string;
      severity?: number;
      start_at?: string;
    },
  ) {
    return this.request<Scenario>(`/api/v1/scenarios/${scenarioId}/event`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  createScenarioIntervention(
    scenarioId: string,
    payload: {
      expected_version: number;
      title: string;
      action_type: ScenarioInterventionType;
      target_entity_id?: string;
      target_dependency_id?: string;
      source_entity_id?: string;
      mitigation?: number;
      weight?: number;
      relationship_type?: string;
      relationship_label?: string;
      rationale: string;
      assumptions: Record<string, unknown>;
    },
  ) {
    return this.request<ScenarioIntervention>(
      `/api/v1/scenarios/${scenarioId}/interventions`,
      { method: "POST", body: JSON.stringify(payload) },
    );
  }

  runScenario(
    scenarioId: string,
    payload: {
      expected_version: number;
    },
  ) {
    return this.request<AnalysisRun>(
      `/api/v1/scenarios/${scenarioId}/analysis-runs`,
      { method: "POST", body: JSON.stringify(payload) },
    );
  }

  compareScenario(scenarioId: string, scenarioRunId: string) {
    const params = new URLSearchParams({ scenario_run_id: scenarioRunId });
    return this.request<ScenarioComparison>(
      `/api/v1/scenarios/${scenarioId}/comparison?${params.toString()}`,
    );
  }

  archiveScenario(scenarioId: string, expectedVersion: number) {
    const params = new URLSearchParams({
      expected_version: String(expectedVersion),
    });
    return this.request<Scenario>(`/api/v1/scenarios/${scenarioId}?${params}`, {
      method: "DELETE",
    });
  }

  createAnalysisRun(eventId: string) {
    return this.request<AnalysisRun>(
      `/api/v1/events/${eventId}/analysis-runs`,
      {
        method: "POST",
        body: JSON.stringify({}),
      },
    );
  }

  listResults(runId: string, offset = 0) {
    const params = new URLSearchParams({ limit: "50", offset: String(offset) });
    return this.request<Page<ImpactResult>>(
      `/api/v1/analysis-runs/${runId}/results?${params.toString()}`,
    );
  }

  listPaths(runId: string, entityId: string) {
    return this.page<ImpactPath>(
      `/api/v1/analysis-runs/${runId}/results/${entityId}/paths`,
    );
  }
}
