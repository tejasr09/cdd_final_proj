import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  AnalysisRun,
  Dependency,
  Entity,
  EventRecord,
  EventTrigger,
  ImpactPath,
  ImpactResult,
  Page,
} from "./api";
import App from "./App";

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    health: vi.fn(),
    listEntities: vi.fn(),
    listDependencies: vi.fn(),
    listEvents: vi.fn(),
    createEntity: vi.fn(),
    updateEntity: vi.fn(),
    archiveEntity: vi.fn(),
    createDependency: vi.fn(),
    updateDependency: vi.fn(),
    setDependencyActive: vi.fn(),
    createEvent: vi.fn(),
    updateEvent: vi.fn(),
    listTriggers: vi.fn(),
    addTrigger: vi.fn(),
    updateEventStatus: vi.fn(),
    listRuns: vi.fn(),
    createAnalysisRun: vi.fn(),
    listResults: vi.fn(),
    listPaths: vi.fn(),
  },
}));

vi.mock("./api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("./api")>();
  return {
    ...actual,
    ApiClient: vi.fn(function MockApiClient() {
      return mockApi;
    }),
  };
});

vi.mock("@xyflow/react", () => ({
  Background: () => null,
  Controls: () => null,
  MarkerType: { ArrowClosed: "arrowclosed" },
  ReactFlow: () => null,
}));

const entity: Entity = {
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

const targetEntity: Entity = {
  ...entity,
  id: "entity-target",
  name: "Practical Session",
  entity_type: "activity",
};

const event: EventRecord = {
  id: "event-id",
  title: "Laboratory unavailable",
  description: null,
  severity: 80,
  start_at: "2026-11-07T09:00:00Z",
  duration_minutes: null,
  status: "open",
  created_at: "2026-11-07T09:00:00Z",
  updated_at: "2026-11-07T09:00:00Z",
};

const dependency: Dependency = {
  id: "dependency-id",
  source_entity_id: entity.id,
  target_entity_id: targetEntity.id,
  relationship_type: "hosts",
  relationship_label: "hosts",
  weight: 0.8,
  rationale: null,
  review_status: "reviewed",
  is_active: true,
  valid_from: null,
  valid_until: null,
  created_at: "2026-11-07T09:00:00Z",
  updated_at: "2026-11-07T09:00:00Z",
};

const run: AnalysisRun = {
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

const result: ImpactResult = {
  id: "result-id",
  run_id: run.id,
  entity_id: targetEntity.id,
  entity_name: targetEntity.name,
  entity_type: targetEntity.entity_type,
  depth: 1,
  score: 23.25,
  impact_level: "moderate",
  confidence_value: 0.75,
  confidence_label: "medium",
  confidence_reason: "Dependency review quality is mixed.",
  primary_path_id: "path-id",
  trigger_entity_ids: [entity.id],
  explanation: "The laboratory affects the practical session.",
  result_flags: {},
};

const path: ImpactPath = {
  id: "path-id",
  run_id: run.id,
  entity_id: targetEntity.id,
  trigger_entity_id: entity.id,
  score: 23.25,
  edge_count: 1,
  is_primary: true,
  provenance: {
    entity_ids: [entity.id, targetEntity.id],
    entity_names: [entity.name, targetEntity.name],
    dependency_labels: ["hosts"],
    dependency_types: ["hosts"],
    weights: [0.8],
    review_statuses: ["reviewed"],
    steps: [
      {
        entity_id: entity.id,
        entity_name: entity.name,
        entity_type: entity.entity_type,
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
        entity_id: targetEntity.id,
        entity_name: targetEntity.name,
        entity_type: targetEntity.entity_type,
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

function page<T>(items: T[]): Page<T> {
  return { items, limit: 100, offset: 0, total: items.length };
}

function configureEmptyWorkspace() {
  mockApi.health.mockResolvedValue({ status: "ready" });
  mockApi.listEntities.mockResolvedValue(page([entity, targetEntity]));
  mockApi.listDependencies.mockResolvedValue(page<Dependency>([]));
  mockApi.listEvents.mockResolvedValue(page<EventRecord>([]));
  mockApi.listTriggers.mockResolvedValue(page<EventTrigger>([]));
  mockApi.listRuns.mockResolvedValue(page<AnalysisRun>([]));
  mockApi.listResults.mockResolvedValue(page<ImpactResult>([]));
  mockApi.listPaths.mockResolvedValue(page<ImpactPath>([]));
}

async function connectToWorkspace() {
  const user = userEvent.setup();
  render(<App />);
  await user.type(screen.getByLabelText("Local user ID"), "user-id");
  await user.type(
    screen.getByLabelText("Active organization ID"),
    "organization-id",
  );
  await user.click(
    screen.getByRole("button", { name: "Connect to local API" }),
  );
  return user;
}

beforeEach(() => {
  vi.clearAllMocks();
  configureEmptyWorkspace();
});

describe("application workflow", () => {
  it("connects with local identity headers and shows an honest empty state", async () => {
    await connectToWorkspace();

    expect(
      await screen.findByRole("heading", { name: "Events" }),
    ).toBeVisible();
    expect(
      screen.getByText("No events have been created in this organization."),
    ).toBeVisible();
    expect(mockApi.health).toHaveBeenCalledOnce();
    expect(mockApi.listEntities).toHaveBeenCalledOnce();
  });

  it("shows API connection failures rather than a success-shaped fallback", async () => {
    mockApi.health.mockRejectedValue(new Error("Connection refused"));

    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Local user ID"), "user-id");
    await user.type(
      screen.getByLabelText("Active organization ID"),
      "organization-id",
    );
    await user.click(
      screen.getByRole("button", { name: "Connect to local API" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Connection refused",
    );
    expect(
      screen.queryByRole("heading", { name: "Events" }),
    ).not.toBeInTheDocument();
  });

  it("creates an event, attaches a trigger, and opens it before analysis", async () => {
    const user = await connectToWorkspace();
    const draftEvent = {
      ...event,
      title: "New service outage",
      status: "draft" as const,
    };
    mockApi.createEvent.mockResolvedValue(draftEvent);
    mockApi.addTrigger.mockResolvedValue({
      id: "trigger-id",
      event_id: event.id,
      entity_id: entity.id,
      exposure: 1,
      rationale: null,
      created_at: event.created_at,
    });
    mockApi.updateEventStatus.mockResolvedValue(event);

    await user.type(screen.getByLabelText("Event title"), "New service outage");
    await user.click(screen.getByRole("button", { name: "Create event" }));
    expect(
      await screen.findByRole("heading", { name: "New service outage" }),
    ).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Edit event" }));
    const updatedDraftEvent = {
      ...draftEvent,
      title: "Revised service outage",
      updated_at: "2026-11-07T10:00:00Z",
    };
    mockApi.updateEvent.mockResolvedValue(updatedDraftEvent);
    const eventForm = within(
      screen.getByRole("form", { name: "Edit event New service outage" }),
    );
    const eventTitleInput = eventForm.getByLabelText("Title");
    await user.clear(eventTitleInput);
    await user.type(eventTitleInput, "Revised service outage");
    await user.click(
      screen.getByRole("button", { name: "Save event changes" }),
    );
    await waitFor(() => expect(mockApi.updateEvent).toHaveBeenCalledOnce());
    expect(mockApi.updateEvent).toHaveBeenCalledWith(
      draftEvent.id,
      expect.objectContaining({
        expected_updated_at: draftEvent.updated_at,
        title: "Revised service outage",
        severity: draftEvent.severity,
      }),
    );

    await user.click(screen.getByRole("button", { name: "Add trigger" }));
    await waitFor(() => expect(mockApi.addTrigger).toHaveBeenCalledOnce());
    await user.click(screen.getByRole("button", { name: "Open event" }));

    expect(mockApi.createEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "New service outage",
        severity: 80,
        status: "draft",
      }),
    );
    expect(mockApi.addTrigger).toHaveBeenCalledWith(event.id, {
      entity_id: entity.id,
      exposure: 1,
    });
    expect(mockApi.updateEventStatus).toHaveBeenCalledWith(event.id, {
      expected_updated_at: updatedDraftEvent.updated_at,
      status: "open",
    });
    expect(await screen.findAllByText("open")).not.toHaveLength(0);
  });

  it("supports audited entity edits and soft archival", async () => {
    const user = await connectToWorkspace();
    await user.click(screen.getByRole("button", { name: /Dependencies/ }));
    await user.click(
      screen.getByRole("button", { name: "Edit North Campus Laboratory" }),
    );
    const editor = screen.getByRole("form", {
      name: "Edit North Campus Laboratory",
    });
    const nameInput = screen.getByLabelText("Name", { selector: "input" });
    await user.clear(nameInput);
    await user.type(nameInput, "Updated Laboratory");

    const updatedEntity = { ...entity, name: "Updated Laboratory" };
    mockApi.updateEntity.mockResolvedValue(updatedEntity);
    await user.click(
      screen.getByRole("button", { name: "Save entity changes" }),
    );
    await waitFor(() => expect(mockApi.updateEntity).toHaveBeenCalledOnce());
    expect(mockApi.updateEntity).toHaveBeenCalledWith(entity.id, {
      expected_updated_at: entity.updated_at,
      name: "Updated Laboratory",
      entity_type: entity.entity_type,
      description: "",
      exposure: entity.exposure,
      mitigation: entity.mitigation,
    });

    mockApi.archiveEntity.mockResolvedValue({
      ...updatedEntity,
      status: "archived",
      archived_at: "2026-11-07T10:00:00Z",
    });
    await user.click(
      screen.getByRole("button", { name: "Archive Updated Laboratory" }),
    );
    await waitFor(() => expect(mockApi.archiveEntity).toHaveBeenCalledOnce());
    expect(mockApi.archiveEntity).toHaveBeenCalledWith(
      entity.id,
      entity.updated_at,
    );
    expect(
      screen.getByRole("row", { name: /Updated Laboratory.*archived/ }),
    ).toBeInTheDocument();
    expect(editor).not.toBeInTheDocument();
  });

  it("creates and deactivates a directed dependency", async () => {
    const user = await connectToWorkspace();
    await user.click(screen.getByRole("button", { name: /Dependencies/ }));
    mockApi.createDependency.mockResolvedValue(dependency);

    await user.selectOptions(screen.getByLabelText("Source"), entity.id);
    await user.selectOptions(screen.getByLabelText("Target"), targetEntity.id);
    await user.type(screen.getByLabelText("Relationship type"), "hosts");
    await user.click(screen.getByRole("button", { name: "Create dependency" }));
    await waitFor(() =>
      expect(mockApi.createDependency).toHaveBeenCalledWith({
        source_entity_id: entity.id,
        target_entity_id: targetEntity.id,
        relationship_type: "hosts",
        relationship_label: undefined,
        weight: 0.8,
        rationale: undefined,
        review_status: "draft",
      }),
    );
    expect(
      screen.getByRole("cell", { name: "source to target" }),
    ).toHaveTextContent("→");

    mockApi.setDependencyActive.mockResolvedValue({
      ...dependency,
      is_active: false,
    });
    await user.click(
      screen.getByRole("button", {
        name: "Deactivate North Campus Laboratory to Practical Session",
      }),
    );
    await waitFor(() =>
      expect(mockApi.setDependencyActive).toHaveBeenCalledWith(dependency.id, {
        expected_updated_at: dependency.updated_at,
        is_active: false,
      }),
    );

    mockApi.updateDependency.mockResolvedValue({
      ...dependency,
      relationship_type: "supports",
      relationship_label: "supports",
    });
    await user.click(
      screen.getByRole("button", {
        name: `Edit dependency from ${entity.name} to ${targetEntity.name}`,
      }),
    );
    const editDependencyForm = screen.getByRole("form", {
      name: "Edit dependency",
    });
    const relationshipType =
      within(editDependencyForm).getByLabelText("Relationship type");
    await user.clear(relationshipType);
    await user.type(relationshipType, "supports");
    const relationshipLabel =
      within(editDependencyForm).getByLabelText("Display label");
    await user.clear(relationshipLabel);
    await user.type(relationshipLabel, "supports");
    await user.click(
      screen.getByRole("button", { name: "Save dependency changes" }),
    );
    await waitFor(() =>
      expect(mockApi.updateDependency).toHaveBeenCalledWith(dependency.id, {
        expected_updated_at: dependency.updated_at,
        source_entity_id: entity.id,
        target_entity_id: targetEntity.id,
        relationship_type: "supports",
        relationship_label: "supports",
        weight: dependency.weight,
        rationale: "",
        review_status: dependency.review_status,
      }),
    );
  });

  it("shows persisted engine results and their source-to-target explanation", async () => {
    mockApi.listEvents.mockResolvedValue(page([event]));
    mockApi.listTriggers.mockResolvedValue(
      page([
        {
          id: "trigger-id",
          event_id: event.id,
          entity_id: entity.id,
          exposure: 1,
          rationale: null,
          created_at: event.created_at,
        },
      ]),
    );
    mockApi.listRuns.mockResolvedValue(page([run]));
    mockApi.listResults.mockResolvedValue(page([result]));
    mockApi.listPaths.mockResolvedValue(page([path]));

    const user = await connectToWorkspace();
    await user.click(screen.getByRole("button", { name: /Analysis/ }));

    expect(await screen.findAllByText("23.250")).toHaveLength(2);
    expect(
      screen.getByText("The laboratory affects the practical session."),
    ).toBeVisible();
    expect(
      screen.getByRole("list", { name: "Source-to-target impact path" }),
    ).toHaveTextContent(
      /Trigger\s*North Campus Laboratory\s*hosts →\s*Affected entity\s*Practical Session/,
    );
    expect(
      screen.getByText(
        "Confidence reflects dependency review quality, not likelihood.",
      ),
    ).toBeVisible();
  });
});
