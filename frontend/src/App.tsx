import { useState } from "react";
import {
  ApiClient,
  ApiError,
  type AnalysisRun,
  type Dependency,
  type Entity,
  type EntityType,
  type EventRecord,
  type EventTrigger,
  type ImpactPath,
  type ImpactResult,
} from "./api";
import ImpactGraph from "./ImpactGraph";

type WorkspaceSection = "events" | "dependencies" | "analysis";

const sections: { id: WorkspaceSection; label: string }[] = [
  { id: "events", label: "Events" },
  { id: "dependencies", label: "Dependencies" },
  { id: "analysis", label: "Analysis" },
];

const entityTypes: EntityType[] = [
  "person",
  "department",
  "resource",
  "activity",
  "system",
  "location",
  "group",
];

function localDateTimeValue(date = new Date()) {
  date = new Date(date);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    const requestId = error.requestId ? ` Request ID: ${error.requestId}.` : "";
    return `${error.message}${requestId}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "The requested operation failed with an unknown error.";
}

function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(
    import.meta.env.VITE_API_BASE_URL ?? "",
  );
  const [userId, setUserId] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [client, setClient] = useState<ApiClient | null>(null);
  const [section, setSection] = useState<WorkspaceSection>("events");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityTotal, setEntityTotal] = useState(0);
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [dependencyTotal, setDependencyTotal] = useState(0);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [eventTotal, setEventTotal] = useState(0);
  const [selectedEventId, setSelectedEventId] = useState("");
  const [triggers, setTriggers] = useState<EventTrigger[]>([]);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [results, setResults] = useState<ImpactResult[]>([]);
  const [resultTotal, setResultTotal] = useState(0);
  const [resultOffset, setResultOffset] = useState(0);
  const [selectedResultId, setSelectedResultId] = useState("");
  const [paths, setPaths] = useState<ImpactPath[]>([]);
  const [dependencySearch, setDependencySearch] = useState("");

  const [eventTitle, setEventTitle] = useState("");
  const [eventDescription, setEventDescription] = useState("");
  const [eventSeverity, setEventSeverity] = useState("80");
  const [eventStartAt, setEventStartAt] = useState(localDateTimeValue);
  const [editingEvent, setEditingEvent] = useState<EventRecord | null>(null);
  const [triggerEntityId, setTriggerEntityId] = useState("");
  const [newEntityName, setNewEntityName] = useState("");
  const [newEntityType, setNewEntityType] = useState<EntityType>("resource");
  const [newEntityDescription, setNewEntityDescription] = useState("");
  const [editingEntity, setEditingEntity] = useState<Entity | null>(null);
  const [dependencySourceId, setDependencySourceId] = useState("");
  const [dependencyTargetId, setDependencyTargetId] = useState("");
  const [dependencyType, setDependencyType] = useState("");
  const [dependencyLabel, setDependencyLabel] = useState("");
  const [dependencyWeight, setDependencyWeight] = useState("0.8");
  const [dependencyReview, setDependencyReview] = useState<
    "draft" | "reviewed" | "validated"
  >("draft");
  const [dependencyRationale, setDependencyRationale] = useState("");
  const [editingDependency, setEditingDependency] = useState<Dependency | null>(
    null,
  );

  const selectedEvent = events.find((item) => item.id === selectedEventId);
  const selectedRun = runs.find((item) => item.id === selectedRunId);
  const selectedResult = results.find((item) => item.id === selectedResultId);
  const primaryPath = paths.find((item) => item.is_primary) ?? paths[0] ?? null;
  const activeEntities = entities.filter(
    (entity) => entity.status === "active",
  );
  const entityById = new Map(entities.map((entity) => [entity.id, entity]));
  const visibleDependencies = dependencies.filter((dependency) => {
    const query = dependencySearch.trim().toLowerCase();
    if (!query) {
      return true;
    }
    const source = entityById.get(dependency.source_entity_id)?.name ?? "";
    const target = entityById.get(dependency.target_entity_id)?.name ?? "";
    return [
      source,
      target,
      dependency.relationship_type,
      dependency.relationship_label,
      dependency.review_status,
    ].some((value) => value.toLowerCase().includes(query));
  });

  async function loadRunDetails(
    activeClient: ApiClient,
    runId: string,
    offset = 0,
  ) {
    const resultPage = await activeClient.listResults(runId, offset);
    setResults(resultPage.items);
    setResultTotal(resultPage.total);
    setResultOffset(resultPage.offset);
    const firstResult = resultPage.items[0];
    setSelectedResultId(firstResult?.id ?? "");
    if (firstResult) {
      const pathPage = await activeClient.listPaths(
        runId,
        firstResult.entity_id,
      );
      setPaths(pathPage.items);
    } else {
      setPaths([]);
    }
  }

  async function loadEventContext(activeClient: ApiClient, eventId: string) {
    const [triggerPage, runPage] = await Promise.all([
      activeClient.listTriggers(eventId),
      activeClient.listRuns(eventId),
    ]);
    setTriggers(triggerPage.items);
    setRuns(runPage.items);
    const firstRun = runPage.items[0];
    setSelectedRunId(firstRun?.id ?? "");
    if (firstRun) {
      await loadRunDetails(activeClient, firstRun.id);
    } else {
      setResults([]);
      setResultTotal(0);
      setResultOffset(0);
      setSelectedResultId("");
      setPaths([]);
    }
  }

  async function loadWorkspace(activeClient: ApiClient) {
    const [entityPage, dependencyPage, eventPage] = await Promise.all([
      activeClient.listEntities(),
      activeClient.listDependencies(),
      activeClient.listEvents(),
    ]);
    setEntities(entityPage.items);
    setEntityTotal(entityPage.total);
    setDependencies(dependencyPage.items);
    setDependencyTotal(dependencyPage.total);
    setEvents(eventPage.items);
    setEventTotal(eventPage.total);

    const firstEvent = eventPage.items[0];
    setSelectedEventId(firstEvent?.id ?? "");
    if (firstEvent) {
      await loadEventContext(activeClient, firstEvent.id);
    } else {
      setTriggers([]);
      setRuns([]);
      setSelectedRunId("");
      setResults([]);
      setResultTotal(0);
      setSelectedResultId("");
      setPaths([]);
    }
  }

  async function perform(action: () => Promise<void>) {
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      await action();
    } catch (actionError) {
      setError(getErrorMessage(actionError));
    } finally {
      setBusy(false);
    }
  }

  async function connect(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await perform(async () => {
      const activeClient = new ApiClient({
        baseUrl: apiBaseUrl.trim(),
        userId: userId.trim(),
        organizationId: organizationId.trim(),
      });
      const health = await activeClient.health();
      if (health.status !== "ready") {
        throw new Error(
          `The API health check returned "${health.status}" instead of "ready".`,
        );
      }
      await loadWorkspace(activeClient);
      setClient(activeClient);
      setNotice("Connected to the selected local organization.");
    });
  }

  async function createEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client) {
      return;
    }
    await perform(async () => {
      const created = await client.createEvent({
        title: eventTitle.trim(),
        description: eventDescription.trim() || undefined,
        severity: Number(eventSeverity),
        start_at: new Date(eventStartAt).toISOString(),
        status: "draft",
      });
      setEvents((current) => [created, ...current]);
      setEventTotal((current) => current + 1);
      setSelectedEventId(created.id);
      setTriggers([]);
      setRuns([]);
      setSelectedRunId("");
      setResults([]);
      setPaths([]);
      setEventTitle("");
      setEventDescription("");
      await loadEventContext(client, created.id);
      setNotice(
        "Event created as a draft. Add a trigger and open it to run analysis.",
      );
    });
  }

  async function saveEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client || !editingEvent) {
      return;
    }
    await perform(async () => {
      const updated = await client.updateEvent(editingEvent.id, {
        expected_updated_at: editingEvent.updated_at,
        title: editingEvent.title.trim(),
        description: editingEvent.description ?? "",
        severity: editingEvent.severity,
        start_at: new Date(editingEvent.start_at).toISOString(),
      });
      setEvents((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setEditingEvent(null);
      setNotice("Event updated.");
    });
  }

  async function addTrigger() {
    if (!client || !selectedEvent) {
      return;
    }
    const selectedEntityId = triggerEntityId || activeEntities[0]?.id;
    if (!selectedEntityId) {
      setError(
        "Create or select an active entity before adding an event trigger.",
      );
      return;
    }
    await perform(async () => {
      const created = await client.addTrigger(selectedEvent.id, {
        entity_id: selectedEntityId,
        exposure: 1,
      });
      setTriggers((current) => [...current, created]);
      setNotice("Event trigger added.");
    });
  }

  async function openEvent() {
    if (!client || !selectedEvent) {
      return;
    }
    if (triggers.length === 0) {
      setError(
        "Add at least one trigger before opening this event for analysis.",
      );
      return;
    }
    await perform(async () => {
      const updated = await client.updateEventStatus(selectedEvent.id, {
        expected_updated_at: selectedEvent.updated_at,
        status: "open",
      });
      setEvents((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setNotice("Event is open and ready for analysis.");
    });
  }

  async function createEntity(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client) {
      return;
    }
    await perform(async () => {
      const created = await client.createEntity({
        name: newEntityName.trim(),
        entity_type: newEntityType,
        description: newEntityDescription.trim() || undefined,
      });
      setEntities((current) => [...current, created]);
      setEntityTotal((current) => current + 1);
      setNewEntityName("");
      setNewEntityDescription("");
      setNotice("Entity created.");
    });
  }

  async function saveEntity(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client || !editingEntity) {
      return;
    }
    await perform(async () => {
      const updated = await client.updateEntity(editingEntity.id, {
        expected_updated_at: editingEntity.updated_at,
        name: editingEntity.name.trim(),
        entity_type: editingEntity.entity_type,
        description: editingEntity.description ?? "",
        exposure: editingEntity.exposure,
        mitigation: editingEntity.mitigation,
      });
      setEntities((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setEditingEntity(null);
      setNotice("Entity updated.");
    });
  }

  async function archiveEntity(entity: Entity) {
    if (!client) {
      return;
    }
    await perform(async () => {
      const archived = await client.archiveEntity(entity.id, entity.updated_at);
      setEntities((current) =>
        current.map((item) => (item.id === archived.id ? archived : item)),
      );
      setEditingEntity((current) =>
        current?.id === archived.id ? null : current,
      );
      setNotice(
        "Entity archived. Existing analysis snapshots remain unchanged.",
      );
    });
  }

  async function createDependency(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client) {
      return;
    }
    if (dependencySourceId === dependencyTargetId) {
      setError("A dependency must connect two different entities.");
      return;
    }
    await perform(async () => {
      const created = await client.createDependency({
        source_entity_id: dependencySourceId,
        target_entity_id: dependencyTargetId,
        relationship_type: dependencyType.trim(),
        relationship_label: dependencyLabel.trim() || undefined,
        weight: Number(dependencyWeight),
        rationale: dependencyRationale.trim() || undefined,
        review_status: dependencyReview,
      });
      setDependencies((current) => [...current, created]);
      setDependencyTotal((current) => current + 1);
      setDependencyType("");
      setDependencyLabel("");
      setDependencyRationale("");
      setNotice("Dependency created. Its direction is source → target.");
    });
  }

  async function toggleDependency(dependency: Dependency) {
    if (!client) {
      return;
    }
    await perform(async () => {
      const updated = await client.setDependencyActive(dependency.id, {
        expected_updated_at: dependency.updated_at,
        is_active: !dependency.is_active,
      });
      setDependencies((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setNotice(
        updated.is_active ? "Dependency activated." : "Dependency deactivated.",
      );
    });
  }

  async function saveDependency(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client || !editingDependency) {
      return;
    }
    if (
      editingDependency.source_entity_id === editingDependency.target_entity_id
    ) {
      setError("A dependency must connect two different entities.");
      return;
    }
    await perform(async () => {
      const updated = await client.updateDependency(editingDependency.id, {
        expected_updated_at: editingDependency.updated_at,
        source_entity_id: editingDependency.source_entity_id,
        target_entity_id: editingDependency.target_entity_id,
        relationship_type: editingDependency.relationship_type.trim(),
        relationship_label: editingDependency.relationship_label.trim(),
        weight: editingDependency.weight,
        rationale: editingDependency.rationale ?? "",
        review_status: editingDependency.review_status,
      });
      setDependencies((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setEditingDependency(null);
      setNotice("Dependency updated. Its direction remains source → target.");
    });
  }

  async function selectEvent(eventId: string) {
    if (!client) {
      return;
    }
    setSelectedEventId(eventId);
    setError(null);
    setNotice(null);
    if (!eventId) {
      setTriggers([]);
      setRuns([]);
      setSelectedRunId("");
      setResults([]);
      setPaths([]);
      return;
    }
    await perform(() => loadEventContext(client, eventId));
  }

  async function runAnalysis() {
    if (!client || !selectedEvent) {
      return;
    }
    if (selectedEvent.status !== "open" || triggers.length === 0) {
      setError(
        "Open the event and add at least one trigger before running analysis.",
      );
      return;
    }
    await perform(async () => {
      const createdRun = await client.createAnalysisRun(selectedEvent.id);
      const runPage = await client.listRuns(selectedEvent.id);
      setRuns(runPage.items);
      setSelectedRunId(createdRun.id);
      await loadRunDetails(client, createdRun.id);
      setSection("analysis");
      setNotice(
        createdRun.status === "completed_with_limits"
          ? "Analysis completed with configured safety limits; results may be incomplete."
          : "Analysis run completed and results were loaded from the API.",
      );
    });
  }

  async function selectRun(runId: string) {
    if (!client) {
      return;
    }
    setSelectedRunId(runId);
    setError(null);
    if (!runId) {
      setResults([]);
      setResultTotal(0);
      setSelectedResultId("");
      setPaths([]);
      return;
    }
    await perform(() => loadRunDetails(client, runId));
  }

  async function selectResult(result: ImpactResult) {
    if (!client || !selectedRunId) {
      return;
    }
    setSelectedResultId(result.id);
    setError(null);
    await perform(async () => {
      const pathPage = await client.listPaths(selectedRunId, result.entity_id);
      setPaths(pathPage.items);
    });
  }

  async function changeResultsPage(offset: number) {
    if (!client || !selectedRunId) {
      return;
    }
    await perform(() => loadRunDetails(client, selectedRunId, offset));
  }

  function disconnect() {
    setClient(null);
    setEntities([]);
    setDependencies([]);
    setEvents([]);
    setTriggers([]);
    setRuns([]);
    setResults([]);
    setPaths([]);
    setSelectedEventId("");
    setSelectedRunId("");
    setSelectedResultId("");
    setError(null);
    setNotice(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Ripple Effect home">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>Ripple Effect</span>
        </a>
        {client && (
          <div className="topbar-controls">
            <span className="scope-pill">
              Local workspace · {organizationId}
            </span>
            <button
              className="secondary-button"
              onClick={disconnect}
              type="button"
            >
              Disconnect
            </button>
          </div>
        )}
      </header>

      <main>
        {!client ? (
          <section aria-labelledby="connect-title" className="setup-card">
            <p className="eyebrow">EVENT → DEPENDENCIES → CONSEQUENCES</p>
            <h1 id="connect-title">Connect to a Ripple Effect workspace</h1>
            <p className="intro-copy">
              Use the local development API and an active organization
              membership. This form does not provide production sign-in.
            </p>
            <div className="integrity-banner" role="note">
              <strong>Local development authentication only.</strong>
              <span>
                The user and organization IDs are sent in the API headers. The
                server enforces membership and permissions; do not use this
                adapter as production authentication.
              </span>
            </div>
            {error && (
              <div className="error-banner" role="alert">
                <strong>Connection failed.</strong>
                <span>{error}</span>
              </div>
            )}
            <form className="setup-form" onSubmit={connect}>
              <label>
                API base URL
                <input
                  autoComplete="url"
                  onChange={(inputEvent) =>
                    setApiBaseUrl(inputEvent.target.value)
                  }
                  placeholder="Blank uses the same-origin API proxy"
                  type="url"
                  value={apiBaseUrl}
                />
              </label>
              <label>
                Local user ID
                <input
                  autoComplete="off"
                  onChange={(inputEvent) => setUserId(inputEvent.target.value)}
                  required
                  value={userId}
                />
              </label>
              <label>
                Active organization ID
                <input
                  autoComplete="off"
                  onChange={(inputEvent) =>
                    setOrganizationId(inputEvent.target.value)
                  }
                  required
                  value={organizationId}
                />
              </label>
              <div className="form-actions">
                <button
                  className="primary-button"
                  disabled={busy}
                  type="submit"
                >
                  {busy ? "Connecting…" : "Connect to local API"}
                </button>
                {busy && (
                  <span role="status">Checking API and loading records…</span>
                )}
              </div>
            </form>
          </section>
        ) : (
          <>
            <section className="intro" aria-labelledby="page-title">
              <div>
                <p className="eyebrow">
                  EVENT → DEPENDENCIES → CONSEQUENCES → DECISIONS
                </p>
                <h1 id="page-title">
                  Trace a change through your dependencies
                </h1>
                <p className="intro-copy">
                  Review organization-scoped records, run the deterministic
                  analysis API, and inspect why each entity appears in the
                  result.
                </p>
              </div>
              <div
                className="scale-card"
                aria-label="Current workspace record counts"
              >
                <span className="scale-label">Current organization</span>
                <strong>{entityTotal.toLocaleString()} entities</strong>
                <span>
                  {dependencyTotal.toLocaleString()} directed dependencies
                </span>
              </div>
            </section>

            <div className="integrity-banner" role="note">
              <strong>
                Impact scores are heuristic estimates, not probabilities.
              </strong>
              <span>
                Analysis is calculated by the backend engine. Confidence
                describes dependency review quality, not likelihood. This
                organization scope comes from the authenticated API membership,
                not a client-side tenant switch.
              </span>
            </div>

            <nav className="workspace-nav" aria-label="Workspace sections">
              {sections.map((item, index) => (
                <button
                  key={item.id}
                  aria-current={section === item.id ? "page" : undefined}
                  className={
                    section === item.id ? "nav-step active" : "nav-step"
                  }
                  onClick={() => setSection(item.id)}
                  type="button"
                >
                  <span className="nav-number">{index + 1}</span>
                  {item.label}
                </button>
              ))}
            </nav>

            {error && (
              <div className="error-banner" role="alert">
                <strong>Request failed.</strong>
                <span>{error}</span>
                <button
                  aria-label="Dismiss error"
                  className="dismiss-button"
                  onClick={() => setError(null)}
                  type="button"
                >
                  Dismiss
                </button>
              </div>
            )}
            {notice && (
              <p className="success-banner" role="status">
                {notice}
              </p>
            )}
            {busy && (
              <p className="loading-banner" role="status">
                Working with the API…
              </p>
            )}

            {section === "events" && (
              <div className="workspace-grid">
                <section
                  className="content-card"
                  aria-labelledby="events-title"
                >
                  <div className="section-heading">
                    <div>
                      <p className="section-kicker">STEP 1 · EVENT</p>
                      <h2 id="events-title">Events</h2>
                      <p>
                        Create a draft, attach at least one trigger, then open
                        it before running analysis.
                      </p>
                    </div>
                    <span className="status-pill">
                      {eventTotal.toLocaleString()} total
                    </span>
                  </div>
                  {events.length === 0 ? (
                    <p className="empty-state">
                      No events have been created in this organization.
                    </p>
                  ) : (
                    <ul className="record-list" aria-label="Events">
                      {events.map((item) => (
                        <li key={item.id}>
                          <button
                            aria-pressed={selectedEventId === item.id}
                            className={
                              selectedEventId === item.id
                                ? "record-button selected"
                                : "record-button"
                            }
                            disabled={busy}
                            onClick={() => void selectEvent(item.id)}
                            type="button"
                          >
                            <span className="record-title">{item.title}</span>
                            <span className={`event-status ${item.status}`}>
                              {item.status}
                            </span>
                            <span className="record-meta">
                              Severity {item.severity} ·{" "}
                              {new Date(item.start_at).toLocaleString()}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                  {eventTotal > events.length && (
                    <p className="table-caption">
                      Showing {events.length} of {eventTotal} events. The API
                      page limit is 100.
                    </p>
                  )}
                </section>

                <section
                  className="content-card"
                  aria-labelledby="create-event-title"
                >
                  <div className="section-heading">
                    <div>
                      <p className="section-kicker">NEW RECORD</p>
                      <h2 id="create-event-title">Create an event</h2>
                      <p>Events begin as drafts and are audited by the API.</p>
                    </div>
                  </div>
                  <form className="form-stack" onSubmit={createEvent}>
                    <label>
                      Event title
                      <input
                        maxLength={200}
                        onChange={(inputEvent) =>
                          setEventTitle(inputEvent.target.value)
                        }
                        required
                        value={eventTitle}
                      />
                    </label>
                    <label>
                      Description
                      <textarea
                        maxLength={5000}
                        onChange={(inputEvent) =>
                          setEventDescription(inputEvent.target.value)
                        }
                        rows={3}
                        value={eventDescription}
                      />
                    </label>
                    <div className="form-row">
                      <label>
                        Severity (0–100)
                        <input
                          max={100}
                          min={0}
                          onChange={(inputEvent) =>
                            setEventSeverity(inputEvent.target.value)
                          }
                          required
                          type="number"
                          value={eventSeverity}
                        />
                      </label>
                      <label>
                        Start time
                        <input
                          onChange={(inputEvent) =>
                            setEventStartAt(inputEvent.target.value)
                          }
                          required
                          type="datetime-local"
                          value={eventStartAt}
                        />
                      </label>
                    </div>
                    <div className="form-actions">
                      <button
                        className="primary-button"
                        disabled={busy}
                        type="submit"
                      >
                        Create event
                      </button>
                    </div>
                  </form>
                </section>

                {selectedEvent && (
                  <section
                    className="content-card full-width"
                    aria-labelledby="selected-event-title"
                  >
                    <div className="section-heading">
                      <div>
                        <p className="section-kicker">SELECTED EVENT</p>
                        <h2 id="selected-event-title">{selectedEvent.title}</h2>
                        <p>
                          Severity {selectedEvent.severity} · starts{" "}
                          {new Date(selectedEvent.start_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="header-actions">
                        <span
                          className={`event-status ${selectedEvent.status}`}
                        >
                          {selectedEvent.status}
                        </span>
                        <button
                          className="secondary-button"
                          disabled={busy}
                          onClick={() =>
                            setEditingEvent({
                              ...selectedEvent,
                              start_at: localDateTimeValue(
                                new Date(selectedEvent.start_at),
                              ),
                            })
                          }
                          type="button"
                        >
                          Edit event
                        </button>
                      </div>
                    </div>
                    {editingEvent?.id === selectedEvent.id && (
                      <form
                        aria-label={`Edit event ${editingEvent.title}`}
                        className="edit-form"
                        onSubmit={saveEvent}
                      >
                        <h3>Edit event details</h3>
                        <label>
                          Title
                          <input
                            maxLength={200}
                            onChange={(inputEvent) =>
                              setEditingEvent({
                                ...editingEvent,
                                title: inputEvent.target.value,
                              })
                            }
                            required
                            value={editingEvent.title}
                          />
                        </label>
                        <label>
                          Description
                          <textarea
                            maxLength={5000}
                            onChange={(inputEvent) =>
                              setEditingEvent({
                                ...editingEvent,
                                description: inputEvent.target.value,
                              })
                            }
                            rows={2}
                            value={editingEvent.description ?? ""}
                          />
                        </label>
                        <div className="form-row">
                          <label>
                            Severity (0–100)
                            <input
                              max={100}
                              min={0}
                              onChange={(inputEvent) =>
                                setEditingEvent({
                                  ...editingEvent,
                                  severity: Number(inputEvent.target.value),
                                })
                              }
                              required
                              type="number"
                              value={editingEvent.severity}
                            />
                          </label>
                          <label>
                            Start time
                            <input
                              onChange={(inputEvent) =>
                                setEditingEvent({
                                  ...editingEvent,
                                  start_at: inputEvent.target.value,
                                })
                              }
                              required
                              type="datetime-local"
                              value={editingEvent.start_at}
                            />
                          </label>
                        </div>
                        <div className="form-actions">
                          <button
                            className="primary-button"
                            disabled={busy}
                            type="submit"
                          >
                            Save event changes
                          </button>
                          <button
                            className="secondary-button"
                            onClick={() => setEditingEvent(null)}
                            type="button"
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    )}
                    <div className="event-detail-grid">
                      <div>
                        <h3>Trigger entities</h3>
                        {triggers.length === 0 ? (
                          <p className="empty-state">
                            Add an active entity as a trigger before opening
                            this event.
                          </p>
                        ) : (
                          <ul className="trigger-list">
                            {triggers.map((trigger) => (
                              <li key={trigger.id}>
                                <strong>
                                  {entityById.get(trigger.entity_id)?.name ??
                                    `Entity ${trigger.entity_id}`}
                                </strong>
                                <span>
                                  Exposure {trigger.exposure.toFixed(2)}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <form
                        className="trigger-form"
                        onSubmit={(submitEvent) => {
                          submitEvent.preventDefault();
                          void addTrigger();
                        }}
                      >
                        <label>
                          Add trigger entity
                          <select
                            onChange={(inputEvent) =>
                              setTriggerEntityId(inputEvent.target.value)
                            }
                            required
                            value={
                              triggerEntityId || activeEntities[0]?.id || ""
                            }
                          >
                            <option value="" disabled>
                              Select an active entity
                            </option>
                            {activeEntities.map((entity) => (
                              <option key={entity.id} value={entity.id}>
                                {entity.name} · {entity.entity_type}
                              </option>
                            ))}
                          </select>
                        </label>
                        <button
                          className="secondary-button"
                          disabled={busy || activeEntities.length === 0}
                          type="submit"
                        >
                          Add trigger
                        </button>
                      </form>
                    </div>
                    {selectedEvent.status === "draft" && (
                      <div className="section-actions">
                        <button
                          className="primary-button"
                          disabled={busy || triggers.length === 0}
                          onClick={() => void openEvent()}
                          type="button"
                        >
                          Open event
                        </button>
                        {triggers.length === 0 && (
                          <span className="muted-copy">
                            At least one trigger is required.
                          </span>
                        )}
                      </div>
                    )}
                  </section>
                )}
              </div>
            )}

            {section === "dependencies" && (
              <div className="workspace-grid">
                <section
                  className="content-card"
                  aria-labelledby="entity-management-title"
                >
                  <div className="section-heading">
                    <div>
                      <p className="section-kicker">MODEL ENTITIES</p>
                      <h2 id="entity-management-title">Entities</h2>
                      <p>
                        Entity records are scoped to this server-selected
                        organization.
                      </p>
                    </div>
                    <span className="status-pill">
                      {entityTotal.toLocaleString()} total
                    </span>
                  </div>
                  <form
                    className="form-stack compact-form"
                    onSubmit={createEntity}
                  >
                    <label>
                      Entity name
                      <input
                        maxLength={160}
                        onChange={(inputEvent) =>
                          setNewEntityName(inputEvent.target.value)
                        }
                        required
                        value={newEntityName}
                      />
                    </label>
                    <label>
                      Entity type
                      <select
                        onChange={(inputEvent) =>
                          setNewEntityType(
                            inputEvent.target.value as EntityType,
                          )
                        }
                        value={newEntityType}
                      >
                        {entityTypes.map((type) => (
                          <option key={type} value={type}>
                            {type}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Description
                      <textarea
                        maxLength={5000}
                        onChange={(inputEvent) =>
                          setNewEntityDescription(inputEvent.target.value)
                        }
                        rows={2}
                        value={newEntityDescription}
                      />
                    </label>
                    <button
                      className="primary-button"
                      disabled={busy}
                      type="submit"
                    >
                      Create entity
                    </button>
                  </form>
                </section>

                <section
                  className="content-card"
                  aria-labelledby="dependency-create-title"
                >
                  <div className="section-heading">
                    <div>
                      <p className="section-kicker">SOURCE → TARGET</p>
                      <h2 id="dependency-create-title">Add a dependency</h2>
                      <p>A change in the source may affect the target.</p>
                    </div>
                    <span className="status-pill">
                      {dependencyTotal.toLocaleString()} total
                    </span>
                  </div>
                  {activeEntities.length < 2 ? (
                    <p className="empty-state">
                      Create at least two active entities before adding a
                      dependency.
                    </p>
                  ) : (
                    <form
                      className="form-stack compact-form"
                      onSubmit={createDependency}
                    >
                      <div className="form-row">
                        <label>
                          Source
                          <select
                            onChange={(inputEvent) =>
                              setDependencySourceId(inputEvent.target.value)
                            }
                            required
                            value={dependencySourceId}
                          >
                            <option value="" disabled>
                              Select source
                            </option>
                            {activeEntities.map((entity) => (
                              <option key={entity.id} value={entity.id}>
                                {entity.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Target
                          <select
                            onChange={(inputEvent) =>
                              setDependencyTargetId(inputEvent.target.value)
                            }
                            required
                            value={dependencyTargetId}
                          >
                            <option value="" disabled>
                              Select target
                            </option>
                            {activeEntities.map((entity) => (
                              <option key={entity.id} value={entity.id}>
                                {entity.name}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                      <div className="form-row">
                        <label>
                          Relationship type
                          <input
                            maxLength={60}
                            onChange={(inputEvent) =>
                              setDependencyType(inputEvent.target.value)
                            }
                            required
                            value={dependencyType}
                          />
                        </label>
                        <label>
                          Display label
                          <input
                            maxLength={80}
                            onChange={(inputEvent) =>
                              setDependencyLabel(inputEvent.target.value)
                            }
                            value={dependencyLabel}
                          />
                        </label>
                      </div>
                      <div className="form-row">
                        <label>
                          Weight (0–1)
                          <input
                            max={1}
                            min={0}
                            onChange={(inputEvent) =>
                              setDependencyWeight(inputEvent.target.value)
                            }
                            required
                            step={0.01}
                            type="number"
                            value={dependencyWeight}
                          />
                        </label>
                        <label>
                          Review status
                          <select
                            onChange={(inputEvent) =>
                              setDependencyReview(
                                inputEvent.target.value as
                                  "draft" | "reviewed" | "validated",
                              )
                            }
                            value={dependencyReview}
                          >
                            <option value="draft">Draft</option>
                            <option value="reviewed">Reviewed</option>
                            <option value="validated">Validated</option>
                          </select>
                        </label>
                      </div>
                      <label>
                        Rationale
                        <textarea
                          maxLength={5000}
                          onChange={(inputEvent) =>
                            setDependencyRationale(inputEvent.target.value)
                          }
                          rows={2}
                          value={dependencyRationale}
                        />
                      </label>
                      <button
                        className="primary-button"
                        disabled={busy}
                        type="submit"
                      >
                        Create dependency
                      </button>
                    </form>
                  )}
                </section>

                <section
                  className="content-card full-width"
                  aria-labelledby="entity-records-title"
                >
                  <div className="section-heading">
                    <div>
                      <p className="section-kicker">ENTITY REGISTER</p>
                      <h2 id="entity-records-title">Manage entities</h2>
                    </div>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <caption className="visually-hidden">
                        Entities in the active organization
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Name</th>
                          <th scope="col">Type</th>
                          <th scope="col">Status</th>
                          <th scope="col">Exposure</th>
                          <th scope="col">Mitigation</th>
                          <th scope="col">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {entities.map((entity) => (
                          <tr key={entity.id}>
                            <td>{entity.name}</td>
                            <td>{entity.entity_type}</td>
                            <td>{entity.status}</td>
                            <td>{entity.exposure.toFixed(2)}</td>
                            <td>{entity.mitigation.toFixed(2)}</td>
                            <td className="table-actions">
                              <button
                                aria-label={`Edit ${entity.name}`}
                                className="table-action"
                                disabled={busy || entity.status === "archived"}
                                onClick={() => setEditingEntity(entity)}
                                type="button"
                              >
                                Edit
                                <span className="visually-hidden">
                                  {" "}
                                  {entity.name}
                                </span>
                              </button>
                              {entity.status !== "archived" && (
                                <button
                                  aria-label={`Archive ${entity.name}`}
                                  className="table-action danger-action"
                                  disabled={busy}
                                  onClick={() => void archiveEntity(entity)}
                                  type="button"
                                >
                                  Archive
                                  <span className="visually-hidden">
                                    {" "}
                                    {entity.name}
                                  </span>
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                        {entities.length === 0 && (
                          <tr>
                            <td className="empty-cell" colSpan={6}>
                              No entities have been created in this
                              organization.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  {entityTotal > entities.length && (
                    <p className="table-caption">
                      Showing the first {entities.length} of {entityTotal}{" "}
                      entities.
                    </p>
                  )}
                  {editingEntity && (
                    <form
                      className="edit-form"
                      onSubmit={saveEntity}
                      aria-label={`Edit ${editingEntity.name}`}
                    >
                      <h3>Edit {editingEntity.name}</h3>
                      <div className="form-row">
                        <label>
                          Name
                          <input
                            maxLength={160}
                            onChange={(inputEvent) =>
                              setEditingEntity({
                                ...editingEntity,
                                name: inputEvent.target.value,
                              })
                            }
                            required
                            value={editingEntity.name}
                          />
                        </label>
                        <label>
                          Type
                          <select
                            onChange={(inputEvent) =>
                              setEditingEntity({
                                ...editingEntity,
                                entity_type: inputEvent.target
                                  .value as EntityType,
                              })
                            }
                            value={editingEntity.entity_type}
                          >
                            {entityTypes.map((type) => (
                              <option key={type} value={type}>
                                {type}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                      <label>
                        Description
                        <textarea
                          maxLength={5000}
                          onChange={(inputEvent) =>
                            setEditingEntity({
                              ...editingEntity,
                              description: inputEvent.target.value,
                            })
                          }
                          rows={2}
                          value={editingEntity.description ?? ""}
                        />
                      </label>
                      <div className="form-row">
                        <label>
                          Exposure (0–1)
                          <input
                            max={1}
                            min={0}
                            onChange={(inputEvent) =>
                              setEditingEntity({
                                ...editingEntity,
                                exposure: Number(inputEvent.target.value),
                              })
                            }
                            required
                            step={0.01}
                            type="number"
                            value={editingEntity.exposure}
                          />
                        </label>
                        <label>
                          Mitigation (0–1)
                          <input
                            max={1}
                            min={0}
                            onChange={(inputEvent) =>
                              setEditingEntity({
                                ...editingEntity,
                                mitigation: Number(inputEvent.target.value),
                              })
                            }
                            required
                            step={0.01}
                            type="number"
                            value={editingEntity.mitigation}
                          />
                        </label>
                      </div>
                      <div className="form-actions">
                        <button
                          className="primary-button"
                          disabled={busy}
                          type="submit"
                        >
                          Save entity changes
                        </button>
                        <button
                          className="secondary-button"
                          onClick={() => setEditingEntity(null)}
                          type="button"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </section>

                <section
                  className="content-card full-width"
                  aria-labelledby="dependency-table-title"
                >
                  <div className="section-heading">
                    <div>
                      <p className="section-kicker">RELATIONSHIP MODEL</p>
                      <h2 id="dependency-table-title">Dependencies</h2>
                    </div>
                  </div>
                  <label className="search-field">
                    Filter displayed dependencies
                    <input
                      onChange={(inputEvent) =>
                        setDependencySearch(inputEvent.target.value)
                      }
                      placeholder="Search entities, relationship, or review status"
                      type="search"
                      value={dependencySearch}
                    />
                  </label>
                  {dependencyTotal > dependencies.length && (
                    <p className="table-caption">
                      Showing the first {dependencies.length} of{" "}
                      {dependencyTotal} dependencies.
                    </p>
                  )}
                  <div className="table-scroll">
                    <table>
                      <caption className="visually-hidden">
                        Directed dependencies in the active organization
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Source</th>
                          <th scope="col">Direction</th>
                          <th scope="col">Target</th>
                          <th scope="col">Weight</th>
                          <th scope="col">Review</th>
                          <th scope="col">Status</th>
                          <th scope="col">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleDependencies.map((dependency) => (
                          <tr key={dependency.id}>
                            <td>
                              {entityById.get(dependency.source_entity_id)
                                ?.name ??
                                `Entity ${dependency.source_entity_id}`}
                            </td>
                            <td aria-label="source to target">→</td>
                            <td>
                              {entityById.get(dependency.target_entity_id)
                                ?.name ??
                                `Entity ${dependency.target_entity_id}`}
                            </td>
                            <td>{dependency.weight.toFixed(2)}</td>
                            <td>{dependency.review_status}</td>
                            <td>
                              {dependency.is_active ? "Active" : "Inactive"}
                            </td>
                            <td className="table-actions">
                              <button
                                aria-label={`Edit dependency from ${entityById.get(dependency.source_entity_id)?.name ?? "source"} to ${entityById.get(dependency.target_entity_id)?.name ?? "target"}`}
                                className="table-action"
                                disabled={busy}
                                onClick={() => setEditingDependency(dependency)}
                                type="button"
                              >
                                Edit
                              </button>
                              <button
                                aria-label={`${dependency.is_active ? "Deactivate" : "Activate"} ${entityById.get(dependency.source_entity_id)?.name ?? "source"} to ${entityById.get(dependency.target_entity_id)?.name ?? "target"}`}
                                className="table-action"
                                disabled={busy}
                                onClick={() =>
                                  void toggleDependency(dependency)
                                }
                                type="button"
                              >
                                {dependency.is_active
                                  ? "Deactivate"
                                  : "Activate"}
                                <span className="visually-hidden">
                                  {" "}
                                  {entityById.get(dependency.source_entity_id)
                                    ?.name ?? "source"}{" "}
                                  to{" "}
                                  {entityById.get(dependency.target_entity_id)
                                    ?.name ?? "target"}
                                </span>
                              </button>
                            </td>
                          </tr>
                        ))}
                        {visibleDependencies.length === 0 && (
                          <tr>
                            <td className="empty-cell" colSpan={7}>
                              {dependencies.length === 0
                                ? "No dependencies have been created in this organization."
                                : "No dependencies match this filter."}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  {editingDependency && (
                    <form
                      aria-label="Edit dependency"
                      className="edit-form"
                      onSubmit={saveDependency}
                    >
                      <h3>Edit dependency</h3>
                      <div className="form-row">
                        <label>
                          Source
                          <select
                            onChange={(inputEvent) =>
                              setEditingDependency({
                                ...editingDependency,
                                source_entity_id: inputEvent.target.value,
                              })
                            }
                            required
                            value={editingDependency.source_entity_id}
                          >
                            {activeEntities.map((entity) => (
                              <option key={entity.id} value={entity.id}>
                                {entity.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Target
                          <select
                            onChange={(inputEvent) =>
                              setEditingDependency({
                                ...editingDependency,
                                target_entity_id: inputEvent.target.value,
                              })
                            }
                            required
                            value={editingDependency.target_entity_id}
                          >
                            {activeEntities.map((entity) => (
                              <option key={entity.id} value={entity.id}>
                                {entity.name}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                      <div className="form-row">
                        <label>
                          Relationship type
                          <input
                            maxLength={60}
                            onChange={(inputEvent) =>
                              setEditingDependency({
                                ...editingDependency,
                                relationship_type: inputEvent.target.value,
                              })
                            }
                            required
                            value={editingDependency.relationship_type}
                          />
                        </label>
                        <label>
                          Display label
                          <input
                            maxLength={80}
                            onChange={(inputEvent) =>
                              setEditingDependency({
                                ...editingDependency,
                                relationship_label: inputEvent.target.value,
                              })
                            }
                            required
                            value={editingDependency.relationship_label}
                          />
                        </label>
                      </div>
                      <div className="form-row">
                        <label>
                          Weight (0–1)
                          <input
                            max={1}
                            min={0}
                            onChange={(inputEvent) =>
                              setEditingDependency({
                                ...editingDependency,
                                weight: Number(inputEvent.target.value),
                              })
                            }
                            required
                            step={0.01}
                            type="number"
                            value={editingDependency.weight}
                          />
                        </label>
                        <label>
                          Review status
                          <select
                            onChange={(inputEvent) =>
                              setEditingDependency({
                                ...editingDependency,
                                review_status: inputEvent.target.value as
                                  "draft" | "reviewed" | "validated",
                              })
                            }
                            value={editingDependency.review_status}
                          >
                            <option value="draft">Draft</option>
                            <option value="reviewed">Reviewed</option>
                            <option value="validated">Validated</option>
                          </select>
                        </label>
                      </div>
                      <label>
                        Rationale
                        <textarea
                          maxLength={5000}
                          onChange={(inputEvent) =>
                            setEditingDependency({
                              ...editingDependency,
                              rationale: inputEvent.target.value,
                            })
                          }
                          rows={2}
                          value={editingDependency.rationale ?? ""}
                        />
                      </label>
                      <div className="form-actions">
                        <button
                          className="primary-button"
                          disabled={busy}
                          type="submit"
                        >
                          Save dependency changes
                        </button>
                        <button
                          className="secondary-button"
                          onClick={() => setEditingDependency(null)}
                          type="button"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </section>
              </div>
            )}

            {section === "analysis" && (
              <section
                className="content-card"
                aria-labelledby="analysis-title"
              >
                <div className="section-heading">
                  <div>
                    <p className="section-kicker">STEP 3 · CONSEQUENCES</p>
                    <h2 id="analysis-title">Impact analysis</h2>
                    <p>
                      Run the backend engine for an open event and inspect its
                      immutable results and path provenance.
                    </p>
                  </div>
                  <button
                    className="primary-button"
                    disabled={
                      busy ||
                      !selectedEvent ||
                      selectedEvent.status !== "open" ||
                      triggers.length === 0
                    }
                    onClick={() => void runAnalysis()}
                    type="button"
                  >
                    Run analysis
                  </button>
                </div>

                {!selectedEvent ? (
                  <p className="empty-state">
                    Select or create an event before reviewing analysis.
                  </p>
                ) : (
                  <div className="analysis-context">
                    <p>
                      <strong>Event:</strong> {selectedEvent.title}
                      <span className={`event-status ${selectedEvent.status}`}>
                        {selectedEvent.status}
                      </span>
                    </p>
                    {selectedEvent.status !== "open" && (
                      <p className="muted-copy">
                        Open this event from the Events section before analysis.
                      </p>
                    )}
                    {triggers.length === 0 && (
                      <p className="muted-copy">
                        Add at least one trigger entity in the Events section.
                      </p>
                    )}
                  </div>
                )}

                {runs.length > 0 && (
                  <div className="run-controls">
                    <label>
                      Run history
                      <select
                        disabled={busy}
                        onChange={(inputEvent) =>
                          void selectRun(inputEvent.target.value)
                        }
                        value={selectedRunId}
                      >
                        {runs.map((run) => (
                          <option key={run.id} value={run.id}>
                            {new Date(run.created_at).toLocaleString()} ·{" "}
                            {run.status}
                          </option>
                        ))}
                      </select>
                    </label>
                    {selectedRun && (
                      <div className="run-meta">
                        <span>
                          {selectedRun.algorithm_version} ·{" "}
                          {selectedRun.input_hash.slice(0, 12)}
                        </span>
                        <span className={`event-status ${selectedRun.status}`}>
                          {selectedRun.status}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {selectedRun?.status === "completed_with_limits" && (
                  <div className="warning-banner" role="status">
                    This run reached a configured safety limit. Results may be
                    incomplete; review the run summary before relying on them.
                  </div>
                )}
                {selectedRun?.status === "failed" && (
                  <div className="error-banner" role="alert">
                    This analysis run failed. The API retains a diagnostic ID;
                    internal engine details are not exposed here.
                  </div>
                )}

                {!selectedRun && (
                  <p className="empty-state">
                    No analysis run is available for this event yet.
                  </p>
                )}

                {selectedRun && selectedRun.status !== "failed" && (
                  <div className="results-layout">
                    <section aria-labelledby="impact-results-title">
                      <div className="section-heading compact-heading">
                        <div>
                          <h3 id="impact-results-title">Affected entities</h3>
                          <p>
                            {resultTotal.toLocaleString()} results · score is a
                            heuristic estimate, not a probability.
                          </p>
                        </div>
                      </div>
                      <div className="table-scroll">
                        <table>
                          <caption className="visually-hidden">
                            Impact estimates produced by the selected analysis
                            run
                          </caption>
                          <thead>
                            <tr>
                              <th scope="col">Entity</th>
                              <th scope="col">Estimate</th>
                              <th scope="col">Impact level</th>
                              <th scope="col">Depth</th>
                              <th scope="col">Confidence</th>
                            </tr>
                          </thead>
                          <tbody>
                            {results.map((result) => (
                              <tr
                                aria-selected={selectedResultId === result.id}
                                className={
                                  selectedResultId === result.id
                                    ? "selected-row"
                                    : undefined
                                }
                                key={result.id}
                              >
                                <td>
                                  <button
                                    aria-pressed={
                                      selectedResultId === result.id
                                    }
                                    className="table-link"
                                    disabled={busy}
                                    onClick={() => void selectResult(result)}
                                    type="button"
                                  >
                                    {result.entity_name}
                                  </button>
                                </td>
                                <td>{result.score.toFixed(3)}</td>
                                <td>{result.impact_level}</td>
                                <td>{result.depth}</td>
                                <td>{result.confidence_label}</td>
                              </tr>
                            ))}
                            {results.length === 0 && (
                              <tr>
                                <td className="empty-cell" colSpan={5}>
                                  This run has no impact results.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                      {resultTotal > 50 && (
                        <div className="pagination-controls">
                          <button
                            className="secondary-button"
                            disabled={busy || resultOffset === 0}
                            onClick={() =>
                              void changeResultsPage(
                                Math.max(0, resultOffset - 50),
                              )
                            }
                            type="button"
                          >
                            Previous results
                          </button>
                          <span>
                            {resultOffset + 1}–
                            {Math.min(
                              resultOffset + results.length,
                              resultTotal,
                            )}{" "}
                            of {resultTotal}
                          </span>
                          <button
                            className="secondary-button"
                            disabled={busy || resultOffset + 50 >= resultTotal}
                            onClick={() =>
                              void changeResultsPage(resultOffset + 50)
                            }
                            type="button"
                          >
                            Next results
                          </button>
                        </div>
                      )}
                    </section>

                    <aside className="detail-panel" aria-live="polite">
                      {selectedResult ? (
                        <>
                          <p className="section-kicker">IMPACT EXPLANATION</p>
                          <h3>{selectedResult.entity_name}</h3>
                          <div className="score-summary">
                            <strong>{selectedResult.score.toFixed(3)}</strong>
                            <span>
                              heuristic estimate · {selectedResult.impact_level}
                            </span>
                          </div>
                          <p>{selectedResult.explanation}</p>
                          <dl className="detail-list">
                            <div>
                              <dt>Minimum depth</dt>
                              <dd>{selectedResult.depth}</dd>
                            </div>
                            <div>
                              <dt>Confidence</dt>
                              <dd>{selectedResult.confidence_label}</dd>
                            </div>
                          </dl>
                          <p>{selectedResult.confidence_reason}</p>
                          <p className="muted-copy">
                            Confidence reflects dependency review quality, not
                            likelihood.
                          </p>
                          <ImpactGraph path={primaryPath} />
                        </>
                      ) : (
                        <p className="empty-state">
                          Select an impact result to inspect its explanation and
                          primary path.
                        </p>
                      )}
                    </aside>
                  </div>
                )}
              </section>
            )}
          </>
        )}
      </main>

      <footer className="page-footer">
        <span>Ripple Effect · API-connected workspace</span>
        <span>
          Organization-scoped records · deterministic estimates · auditable
          state changes
        </span>
      </footer>
    </div>
  );
}

export default App;
