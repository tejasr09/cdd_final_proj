import { expect, test } from "@playwright/test";

test("event to analysis workflow is connected to API responses", async ({
  page,
}) => {
  const source = {
    id: "entity-source",
    name: "North Campus Laboratory",
    description: null,
    entity_type: "resource",
    status: "active",
    exposure: 1,
    mitigation: 0,
    attributes: {},
    archived_at: null,
    created_at: "2026-11-07T09:00:00Z",
    updated_at: "2026-11-07T09:00:00Z",
  };
  const target = {
    ...source,
    id: "entity-target",
    name: "Practical Session",
    entity_type: "activity",
  };
  let event = {
    id: "event-id",
    title: "Laboratory unavailable",
    description: null,
    severity: 80,
    start_at: "2026-11-07T09:00:00Z",
    duration_minutes: null,
    status: "draft",
    created_at: "2026-11-07T09:00:00Z",
    updated_at: "2026-11-07T09:00:00Z",
  };
  let eventCreated = false;
  const triggers: Record<string, unknown>[] = [];
  let runCreated = false;
  const run = {
    id: "run-id",
    organization_id: "organization-id",
    event_id: event.id,
    status: "completed",
    configuration: { max_depth: 4 },
    algorithm_version: "1",
    input_hash: "abcdef123456",
    as_of: event.start_at,
    summary: {},
    created_by_user_id: "user-id",
    created_at: event.start_at,
    updated_at: event.start_at,
  };
  const result = {
    id: "result-id",
    run_id: run.id,
    entity_id: target.id,
    entity_name: target.name,
    entity_type: target.entity_type,
    depth: 1,
    score: 23.25,
    impact_level: "moderate",
    confidence_value: 0.75,
    confidence_label: "medium",
    confidence_reason: "Dependency review quality is mixed.",
    primary_path_id: "path-id",
    trigger_entity_ids: [source.id],
    explanation: "The laboratory affects the practical session.",
    result_flags: {},
  };
  const path = {
    id: "path-id",
    run_id: run.id,
    entity_id: target.id,
    trigger_entity_id: source.id,
    score: 23.25,
    edge_count: 1,
    is_primary: true,
    provenance: {
      entity_ids: [source.id, target.id],
      entity_names: [source.name, target.name],
      dependency_labels: ["hosts"],
      dependency_types: ["hosts"],
      weights: [0.8],
      review_statuses: ["reviewed"],
      steps: [
        {
          entity_id: source.id,
          entity_name: source.name,
          entity_type: source.entity_type,
          mitigation: 0,
          dependency_id: null,
          relationship_type: null,
          relationship_label: null,
          weight: null,
          review_status: null,
          rationale: null,
          is_hypothetical: false,
        },
        {
          entity_id: target.id,
          entity_name: target.name,
          entity_type: target.entity_type,
          mitigation: 0,
          dependency_id: "dependency-id",
          relationship_type: "hosts",
          relationship_label: "hosts",
          weight: 0.8,
          review_status: "reviewed",
          rationale: null,
          is_hypothetical: false,
        },
      ],
    },
  };
  const pageResponse = (items: unknown[]) => ({
    items,
    limit: 100,
    offset: 0,
    total: items.length,
  });

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const pathName = url.pathname;
    if (pathName.endsWith("/health/ready")) {
      await route.fulfill({ json: { status: "ready" } });
    } else if (pathName.endsWith("/entities") && method === "GET") {
      await route.fulfill({ json: pageResponse([source, target]) });
    } else if (pathName.endsWith("/dependencies") && method === "GET") {
      await route.fulfill({ json: pageResponse([]) });
    } else if (pathName.endsWith("/events") && method === "GET") {
      await route.fulfill({
        json: pageResponse(eventCreated ? [event] : []),
      });
    } else if (pathName.endsWith("/events") && method === "POST") {
      const body = request.postDataJSON() as {
        title: string;
        severity: number;
      };
      event = {
        ...event,
        title: body.title,
        severity: body.severity,
        status: "draft",
      };
      eventCreated = true;
      await route.fulfill({ status: 201, json: event });
    } else if (
      pathName.endsWith("/events/event-id/triggers") &&
      method === "GET"
    ) {
      await route.fulfill({ json: pageResponse(triggers) });
    } else if (
      pathName.endsWith("/events/event-id/triggers") &&
      method === "POST"
    ) {
      const body = request.postDataJSON() as {
        entity_id: string;
        exposure: number;
      };
      const created = {
        id: "trigger-id",
        event_id: event.id,
        entity_id: body.entity_id,
        exposure: body.exposure,
        rationale: null,
        created_at: event.created_at,
      };
      triggers.push(created);
      await route.fulfill({ status: 201, json: created });
    } else if (
      pathName.endsWith("/events/event-id/status") &&
      method === "PATCH"
    ) {
      event = { ...event, status: "open" };
      await route.fulfill({ json: event });
    } else if (
      pathName.endsWith("/events/event-id/analysis-runs") &&
      method === "POST"
    ) {
      runCreated = true;
      await route.fulfill({ status: 201, json: run });
    } else if (pathName.endsWith("/analysis-runs") && method === "GET") {
      await route.fulfill({ json: pageResponse(runCreated ? [run] : []) });
    } else if (
      pathName.endsWith("/analysis-runs/run-id/results") &&
      method === "GET"
    ) {
      await route.fulfill({ json: pageResponse([result]) });
    } else if (
      pathName.endsWith("/analysis-runs/run-id/results/entity-target/paths") &&
      method === "GET"
    ) {
      await route.fulfill({ json: pageResponse([path]) });
    } else {
      await route.fulfill({
        status: 404,
        json: {
          error: {
            code: "not_found",
            message: `Unmocked test endpoint: ${method} ${pathName}`,
            details: [],
            request_id: "test-request",
          },
        },
      });
    }
  });

  await page.goto("/");
  await page.getByLabel("Local user ID").fill("user-id");
  await page.getByLabel("Active organization ID").fill("organization-id");
  await page.getByRole("button", { name: "Connect to local API" }).click();
  await expect(page.getByRole("heading", { name: "Events" })).toBeVisible();

  await page.getByLabel("Event title").fill("Water service outage");
  await page.getByRole("button", { name: "Create event" }).click();
  await page.getByRole("button", { name: "Add trigger" }).click();
  await page.getByRole("button", { name: "Open event" }).click();

  await page.getByRole("button", { name: "Analysis" }).click();
  await page.getByRole("button", { name: "Run analysis" }).click();

  await expect(page.getByText("23.250")).toHaveCount(2);
  await expect(
    page.getByText("The laboratory affects the practical session."),
  ).toBeVisible();
  await expect(
    page.getByRole("list", { name: "Source-to-target impact path" }),
  ).toContainText("North Campus Laboratory");
  await expect(
    page.getByRole("group", {
      name: "Directed impact graph: North Campus Laboratory to Practical Session",
    }),
  ).toBeVisible();
});
