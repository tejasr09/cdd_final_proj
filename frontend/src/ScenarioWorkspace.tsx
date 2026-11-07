import { useEffect, useState, type FormEvent } from "react";
import type {
  AnalysisRun,
  ApiClient,
  Dependency,
  Entity,
  ScenarioComparison,
  ScenarioDetail,
  ScenarioInterventionType,
  Scenario as ScenarioRecord,
} from "./api";

type ScenarioClient = Pick<
  ApiClient,
  | "listScenarios"
  | "getScenario"
  | "createScenario"
  | "updateScenarioEvent"
  | "createScenarioIntervention"
  | "listScenarioRuns"
  | "runScenario"
  | "compareScenario"
  | "archiveScenario"
>;

type Props = {
  client: ScenarioClient;
  runs: AnalysisRun[];
  entities: Entity[];
  dependencies: Dependency[];
};

const interventionTypes: {
  id: ScenarioInterventionType;
  label: string;
}[] = [
  { id: "mitigation", label: "Node mitigation override" },
  { id: "weight_override", label: "Dependency weight override" },
  { id: "deactivate_dependency", label: "Deactivate dependency" },
  { id: "hypothetical_dependency", label: "Add hypothetical dependency" },
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isInterventionType(value: string): value is ScenarioInterventionType {
  return interventionTypes.some((item) => item.id === value);
}

function errorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "The scenario request failed.";
}

function localDateTimeValue(value: string) {
  const date = new Date(value);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

function ScenarioWorkspace({ client, runs, entities, dependencies }: Props) {
  const [scenarios, setScenarios] = useState<ScenarioRecord[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("");
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [scenarioRuns, setScenarioRuns] = useState<AnalysisRun[]>([]);
  const [selectedScenarioRunId, setSelectedScenarioRunId] = useState("");
  const [comparison, setComparison] = useState<ScenarioComparison | null>(null);
  const [baselineRunId, setBaselineRunId] = useState("");
  const [scenarioName, setScenarioName] = useState("");
  const [scenarioDescription, setScenarioDescription] = useState("");
  const [eventTitle, setEventTitle] = useState("");
  const [eventSeverity, setEventSeverity] = useState("80");
  const [eventStartAt, setEventStartAt] = useState("");
  const [actionType, setActionType] =
    useState<ScenarioInterventionType>("mitigation");
  const [interventionTitle, setInterventionTitle] = useState("");
  const [interventionRationale, setInterventionRationale] = useState("");
  const [assumptions, setAssumptions] = useState("{}");
  const [targetEntityId, setTargetEntityId] = useState("");
  const [sourceEntityId, setSourceEntityId] = useState("");
  const [targetDependencyId, setTargetDependencyId] = useState("");
  const [mitigation, setMitigation] = useState("0.5");
  const [weight, setWeight] = useState("0.5");
  const [relationshipType, setRelationshipType] = useState("supports");
  const [relationshipLabel, setRelationshipLabel] = useState(
    "hypothetical support",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const baselineRuns = runs.filter(
    (run) =>
      run.scenario_id === null &&
      (run.status === "completed" || run.status === "completed_with_limits"),
  );
  const selectedBaselineRunId =
    baselineRuns.find((run) => run.id === baselineRunId)?.id ??
    baselineRuns[0]?.id ??
    "";
  const entityById = new Map(entities.map((entity) => [entity.id, entity]));
  const eventOverlay = scenario?.event_overlay.event;

  useEffect(() => {
    let active = true;
    client
      .listScenarios()
      .then((page) => {
        if (active) {
          setScenarios(page.items);
        }
      })
      .catch((loadError: unknown) => {
        if (active) {
          setError(errorMessage(loadError));
        }
      });
    return () => {
      active = false;
    };
  }, [client]);

  async function perform(action: () => Promise<void>) {
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      await action();
    } catch (actionError) {
      setError(errorMessage(actionError));
    } finally {
      setBusy(false);
    }
  }

  async function loadScenario(scenarioId: string) {
    const [details, runPage] = await Promise.all([
      client.getScenario(scenarioId),
      client.listScenarioRuns(scenarioId),
    ]);
    setSelectedScenarioId(scenarioId);
    setScenario(details);
    setScenarioRuns(runPage.items);
    setComparison(null);
    const latestRun = runPage.items[0];
    setSelectedScenarioRunId(latestRun?.id ?? "");
    if (latestRun) {
      setComparison(await client.compareScenario(scenarioId, latestRun.id));
    }
    setEventTitle(details.event_overlay.event.title);
    setEventSeverity(String(details.event_overlay.event.severity));
    setEventStartAt(localDateTimeValue(details.event_overlay.event.start_at));
  }

  async function createScenario(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await perform(async () => {
      const created = await client.createScenario({
        name: scenarioName.trim(),
        description: scenarioDescription.trim() || undefined,
        baseline_run_id: selectedBaselineRunId,
      });
      setScenarios((current) => [created, ...current]);
      setScenarioName("");
      setScenarioDescription("");
      await loadScenario(created.id);
      setNotice("Scenario created from an immutable baseline snapshot.");
    });
  }

  async function updateEventOverlay(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!scenario) {
      return;
    }
    await perform(async () => {
      await client.updateScenarioEvent(scenario.id, {
        expected_version: scenario.version,
        title: eventTitle.trim(),
        severity: Number(eventSeverity),
        start_at: new Date(eventStartAt).toISOString(),
      });
      await loadScenario(scenario.id);
      setNotice(
        "Scenario event overlay updated; the live event was not changed.",
      );
    });
  }

  async function addIntervention(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!scenario) {
      return;
    }
    let parsedAssumptions: unknown;
    try {
      parsedAssumptions = JSON.parse(assumptions);
    } catch {
      setError("Assumptions must be valid JSON.");
      return;
    }
    if (!isRecord(parsedAssumptions)) {
      setError("Assumptions must be a JSON object.");
      return;
    }

    await perform(async () => {
      const payload = {
        expected_version: scenario.version,
        title: interventionTitle.trim(),
        action_type: actionType,
        rationale: interventionRationale.trim(),
        assumptions: parsedAssumptions,
        ...(actionType === "mitigation"
          ? {
              target_entity_id: targetEntityId || entities[0]?.id,
              mitigation: Number(mitigation),
            }
          : {}),
        ...(actionType === "weight_override"
          ? {
              target_dependency_id: targetDependencyId || dependencies[0]?.id,
              weight: Number(weight),
            }
          : {}),
        ...(actionType === "deactivate_dependency"
          ? {
              target_dependency_id: targetDependencyId || dependencies[0]?.id,
            }
          : {}),
        ...(actionType === "hypothetical_dependency"
          ? {
              source_entity_id: sourceEntityId || entities[0]?.id,
              target_entity_id: targetEntityId || entities[1]?.id,
              relationship_type: relationshipType.trim(),
              relationship_label: relationshipLabel.trim(),
              weight: Number(weight),
            }
          : {}),
      };
      await client.createScenarioIntervention(scenario.id, payload);
      await loadScenario(scenario.id);
      setNotice(
        "Intervention added as a scenario-only assumption. No live records changed.",
      );
    });
  }

  async function runScenario() {
    if (!scenario) {
      return;
    }
    await perform(async () => {
      const run = await client.runScenario(scenario.id, {
        expected_version: scenario.version,
      });
      const runPage = await client.listScenarioRuns(scenario.id);
      setScenarioRuns(runPage.items);
      setSelectedScenarioRunId(run.id);
      const result = await client.compareScenario(scenario.id, run.id);
      setComparison(result);
      setNotice(
        run.status === "completed_with_limits"
          ? "Scenario analysis completed with safety limits; results may be incomplete."
          : "Scenario analysis completed. Impact differences are estimates, not guarantees.",
      );
    });
  }

  async function selectScenarioRun(runId: string) {
    if (!scenario || !runId) {
      setSelectedScenarioRunId("");
      setComparison(null);
      return;
    }
    await perform(async () => {
      setSelectedScenarioRunId(runId);
      setComparison(await client.compareScenario(scenario.id, runId));
    });
  }

  async function archiveScenario() {
    if (!scenario) {
      return;
    }
    await perform(async () => {
      const archived = await client.archiveScenario(
        scenario.id,
        scenario.version,
      );
      setScenario({ ...scenario, ...archived });
      setScenarios((current) =>
        current.map((item) => (item.id === archived.id ? archived : item)),
      );
      setNotice(
        "Scenario archived. Baseline and scenario history were retained.",
      );
    });
  }

  return (
    <div className="scenario-workspace">
      <section className="content-card" aria-labelledby="scenario-title">
        <div className="section-heading">
          <div>
            <p className="section-kicker">ISOLATED WHAT-IF ANALYSIS</p>
            <h2 id="scenario-title">Scenarios</h2>
            <p>
              Compare a versioned overlay with its immutable baseline. Scenario
              changes never update live records.
            </p>
          </div>
          <span className="status-pill">Versioned assumptions</span>
        </div>

        <div className="integrity-banner" role="note">
          <strong>
            Scenario estimates are not predictions or recommendations.
          </strong>
          <span>
            Compare score deltas and assumptions; no scenario action is applied
            to live events, entities, or dependencies.
          </span>
        </div>
        {error && (
          <div className="error-banner" role="alert">
            <strong>Scenario operation failed.</strong>
            <span>{error}</span>
          </div>
        )}
        {notice && (
          <p className="success-banner" role="status">
            {notice}
          </p>
        )}

        <form className="edit-form" onSubmit={createScenario}>
          <h3>Create a scenario</h3>
          <label>
            Baseline live analysis
            <select
              onChange={(inputEvent) =>
                setBaselineRunId(inputEvent.target.value)
              }
              required
              value={selectedBaselineRunId}
            >
              <option value="" disabled>
                Select a completed live analysis
              </option>
              {baselineRuns.map((run) => (
                <option key={run.id} value={run.id}>
                  {new Date(run.created_at).toLocaleString()} ·{" "}
                  {run.input_hash.slice(0, 12)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Scenario name
            <input
              maxLength={160}
              onChange={(inputEvent) =>
                setScenarioName(inputEvent.target.value)
              }
              required
              value={scenarioName}
            />
          </label>
          <label>
            Description
            <textarea
              maxLength={5000}
              onChange={(inputEvent) =>
                setScenarioDescription(inputEvent.target.value)
              }
              rows={2}
              value={scenarioDescription}
            />
          </label>
          <div className="form-actions">
            <button
              className="primary-button"
              disabled={busy || !selectedBaselineRunId}
              type="submit"
            >
              Create scenario
            </button>
            {busy && <span role="status">Saving scenario changes…</span>}
          </div>
        </form>

        <div className="form-stack">
          <label>
            Scenario
            <select
              disabled={busy || scenarios.length === 0}
              onChange={(inputEvent) => {
                if (inputEvent.target.value) {
                  void perform(() => loadScenario(inputEvent.target.value));
                } else {
                  setSelectedScenarioId("");
                  setScenario(null);
                  setComparison(null);
                }
              }}
              value={selectedScenarioId}
            >
              <option value="">Select a saved scenario</option>
              {scenarios.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} · v{item.version} · {item.status}
                </option>
              ))}
            </select>
          </label>
        </div>

        {scenarios.length === 0 && (
          <p className="empty-state">
            No scenarios have been created in this organization.
          </p>
        )}

        {scenario && eventOverlay && (
          <div className="scenario-details">
            <div className="section-heading compact-heading">
              <div>
                <h3>{scenario.name}</h3>
                <p>
                  Version {scenario.version} · baseline{" "}
                  {scenario.baseline_run_id?.slice(0, 12)}
                </p>
              </div>
              <div className="header-actions">
                <span className={`event-status ${scenario.status}`}>
                  {scenario.status}
                </span>
                {scenario.status === "draft" && (
                  <button
                    className="secondary-button"
                    disabled={busy}
                    onClick={() => void archiveScenario()}
                    type="button"
                  >
                    Archive scenario
                  </button>
                )}
              </div>
            </div>

            {scenario.status === "draft" && (
              <>
                <form className="edit-form" onSubmit={updateEventOverlay}>
                  <h3>Scenario event overlay</h3>
                  <div className="form-row">
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
                  </div>
                  <label>
                    Scenario start time
                    <input
                      onChange={(inputEvent) =>
                        setEventStartAt(inputEvent.target.value)
                      }
                      required
                      type="datetime-local"
                      value={eventStartAt}
                    />
                  </label>
                  <div className="form-actions">
                    <button className="secondary-button" disabled={busy}>
                      Save event overlay
                    </button>
                  </div>
                </form>

                <form className="edit-form" onSubmit={addIntervention}>
                  <h3>Add an intervention</h3>
                  <label>
                    Intervention type
                    <select
                      onChange={(inputEvent) =>
                        isInterventionType(inputEvent.target.value) &&
                        setActionType(inputEvent.target.value)
                      }
                      value={actionType}
                    >
                      {interventionTypes.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Intervention title
                    <input
                      maxLength={160}
                      onChange={(inputEvent) =>
                        setInterventionTitle(inputEvent.target.value)
                      }
                      required
                      value={interventionTitle}
                    />
                  </label>
                  {actionType === "mitigation" && (
                    <div className="form-row">
                      <label>
                        Target entity
                        <select
                          onChange={(inputEvent) =>
                            setTargetEntityId(inputEvent.target.value)
                          }
                          required
                          value={targetEntityId || entities[0]?.id || ""}
                        >
                          {entities.map((entity) => (
                            <option key={entity.id} value={entity.id}>
                              {entity.name}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Mitigation (0–1)
                        <input
                          max={1}
                          min={0}
                          onChange={(inputEvent) =>
                            setMitigation(inputEvent.target.value)
                          }
                          required
                          step={0.01}
                          type="number"
                          value={mitigation}
                        />
                      </label>
                    </div>
                  )}
                  {actionType === "weight_override" && (
                    <div className="form-row">
                      <label>
                        Target dependency
                        <select
                          onChange={(inputEvent) =>
                            setTargetDependencyId(inputEvent.target.value)
                          }
                          required
                          value={
                            targetDependencyId || dependencies[0]?.id || ""
                          }
                        >
                          {dependencies.map((dependency) => (
                            <option key={dependency.id} value={dependency.id}>
                              {entityById.get(dependency.source_entity_id)
                                ?.name ?? "Source"}{" "}
                              →{" "}
                              {entityById.get(dependency.target_entity_id)
                                ?.name ?? "Target"}{" "}
                              · {dependency.relationship_label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Weight (0–1)
                        <input
                          max={1}
                          min={0}
                          onChange={(inputEvent) =>
                            setWeight(inputEvent.target.value)
                          }
                          required
                          step={0.01}
                          type="number"
                          value={weight}
                        />
                      </label>
                    </div>
                  )}
                  {actionType === "deactivate_dependency" && (
                    <label>
                      Dependency to deactivate
                      <select
                        onChange={(inputEvent) =>
                          setTargetDependencyId(inputEvent.target.value)
                        }
                        required
                        value={targetDependencyId || dependencies[0]?.id || ""}
                      >
                        {dependencies.map((dependency) => (
                          <option key={dependency.id} value={dependency.id}>
                            {entityById.get(dependency.source_entity_id)
                              ?.name ?? "Source"}{" "}
                            →{" "}
                            {entityById.get(dependency.target_entity_id)
                              ?.name ?? "Target"}{" "}
                            · {dependency.relationship_label}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  {actionType === "hypothetical_dependency" && (
                    <>
                      <div className="form-row">
                        <label>
                          Source entity
                          <select
                            onChange={(inputEvent) =>
                              setSourceEntityId(inputEvent.target.value)
                            }
                            required
                            value={sourceEntityId || entities[0]?.id || ""}
                          >
                            {entities.map((entity) => (
                              <option key={entity.id} value={entity.id}>
                                {entity.name}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Target entity
                          <select
                            onChange={(inputEvent) =>
                              setTargetEntityId(inputEvent.target.value)
                            }
                            required
                            value={
                              targetEntityId ||
                              entities[1]?.id ||
                              entities[0]?.id ||
                              ""
                            }
                          >
                            {entities.map((entity) => (
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
                              setRelationshipType(inputEvent.target.value)
                            }
                            required
                            value={relationshipType}
                          />
                        </label>
                        <label>
                          Relationship label
                          <input
                            maxLength={80}
                            onChange={(inputEvent) =>
                              setRelationshipLabel(inputEvent.target.value)
                            }
                            required
                            value={relationshipLabel}
                          />
                        </label>
                      </div>
                      <label>
                        Hypothetical dependency weight (0–1)
                        <input
                          max={1}
                          min={0}
                          onChange={(inputEvent) =>
                            setWeight(inputEvent.target.value)
                          }
                          required
                          step={0.01}
                          type="number"
                          value={weight}
                        />
                      </label>
                    </>
                  )}
                  <label>
                    Rationale
                    <textarea
                      maxLength={5000}
                      onChange={(inputEvent) =>
                        setInterventionRationale(inputEvent.target.value)
                      }
                      required
                      rows={2}
                      value={interventionRationale}
                    />
                  </label>
                  <label>
                    Assumptions (JSON object)
                    <textarea
                      onChange={(inputEvent) =>
                        setAssumptions(inputEvent.target.value)
                      }
                      rows={3}
                      value={assumptions}
                    />
                  </label>
                  <div className="form-actions">
                    <button className="secondary-button" disabled={busy}>
                      Add scenario intervention
                    </button>
                  </div>
                </form>
              </>
            )}

            <section aria-labelledby="scenario-interventions-title">
              <h3 id="scenario-interventions-title">Recorded assumptions</h3>
              {scenario.interventions.length === 0 ? (
                <p className="empty-state">No interventions have been added.</p>
              ) : (
                <ul className="trigger-list">
                  {scenario.interventions.map((intervention) => (
                    <li key={intervention.id}>
                      <strong>
                        {intervention.title} · {intervention.action_type}
                      </strong>
                      <span>{intervention.rationale}</span>
                      <span>
                        Assumptions: {JSON.stringify(intervention.assumptions)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <div className="section-actions">
              <button
                className="primary-button"
                disabled={busy || scenario.status !== "draft"}
                onClick={() => void runScenario()}
                type="button"
              >
                Run scenario analysis
              </button>
              {scenarioRuns.length > 0 && (
                <label className="search-field">
                  Scenario run history
                  <select
                    disabled={busy}
                    onChange={(inputEvent) =>
                      void selectScenarioRun(inputEvent.target.value)
                    }
                    value={selectedScenarioRunId}
                  >
                    {scenarioRuns.map((run) => (
                      <option key={run.id} value={run.id}>
                        {new Date(run.created_at).toLocaleString()} ·{" "}
                        {run.status}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>

            {comparison && (
              <section
                className="scenario-comparison"
                aria-labelledby="scenario-comparison-title"
              >
                <div className="section-heading compact-heading">
                  <div>
                    <h3 id="scenario-comparison-title">Baseline vs scenario</h3>
                    <p>
                      Version {comparison.scenario_version} · baseline{" "}
                      {comparison.baseline_status} · scenario{" "}
                      {comparison.scenario_status}
                    </p>
                  </div>
                  {comparison.potentially_incomplete && (
                    <span className="event-status completed_with_limits">
                      potentially incomplete
                    </span>
                  )}
                </div>
                <div className="analysis-context">
                  <p>
                    <strong>
                      {comparison.estimated_effect.score_delta > 0
                        ? "Lower estimated impact in this scenario"
                        : comparison.estimated_effect.score_delta < 0
                          ? "Higher estimated impact in this scenario"
                          : "No aggregate score change"}
                    </strong>
                  </p>
                  <p>
                    Sum of baseline scores minus scenario scores:{" "}
                    {comparison.estimated_effect.score_delta.toFixed(3)}
                  </p>
                  <p className="muted-copy">
                    This aggregate is a comparison of heuristic estimates, not a
                    probability or guaranteed intervention effect.
                  </p>
                </div>
                <div className="table-scroll">
                  <table>
                    <caption className="visually-hidden">
                      Entity-level baseline and scenario estimate comparison
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Entity</th>
                        <th scope="col">Change</th>
                        <th scope="col">Baseline estimate</th>
                        <th scope="col">Scenario estimate</th>
                        <th scope="col">Scenario minus baseline</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.items.map((item) => (
                        <tr key={item.entity_id}>
                          <td>{item.entity_name}</td>
                          <td>{item.change_type}</td>
                          <td>{item.baseline_score.toFixed(3)}</td>
                          <td>{item.scenario_score.toFixed(3)}</td>
                          <td>{item.delta.toFixed(3)}</td>
                        </tr>
                      ))}
                      {comparison.items.length === 0 && (
                        <tr>
                          <td className="empty-cell" colSpan={5}>
                            This comparison contains no impact results.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export default ScenarioWorkspace;
