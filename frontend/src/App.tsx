import { useMemo, useState } from "react";
import {
  DEMO_ORGANIZATIONS,
  DEMO_SCALE,
  SYNTHETIC_DEPENDENCIES,
  SYNTHETIC_ENTITIES,
  type DemoOrganization,
  type DemoStep,
} from "./demoData";

const steps: { id: DemoStep; label: string }[] = [
  { id: "events", label: "1. Events" },
  { id: "dependencies", label: "2. Dependencies" },
  { id: "analysis", label: "3. Analysis" },
  { id: "scenario", label: "4. Scenario comparison" },
];

const resultExamples: Record<
  DemoOrganization,
  { key: string; score: number; level: string; path: string[] }[]
> = {
  campus: [
    {
      key: "SESSION-A",
      score: 76,
      level: "High",
      path: ["AC-LAB", "SESSION-A"],
    },
    {
      key: "SESSION-B",
      score: 69,
      level: "High",
      path: ["AC-LAB", "SESSION-B"],
    },
    {
      key: "BATCH-1",
      score: 58,
      level: "Moderate",
      path: ["AC-LAB", "SESSION-A", "BATCH-1"],
    },
    {
      key: "TIMETABLE",
      score: 34,
      level: "Low",
      path: ["AC-LAB", "SESSION-A", "TIMETABLE"],
    },
  ],
  transport: [
    {
      key: "ROUTE-1",
      score: 72,
      level: "High",
      path: ["ROAD-X", "ROUTE-1"],
    },
    {
      key: "ROUTE-2",
      score: 56,
      level: "Moderate",
      path: ["ROAD-X", "ROUTE-2"],
    },
    {
      key: "STOP-A",
      score: 51,
      level: "Moderate",
      path: ["ROAD-X", "ROUTE-1", "STOP-A"],
    },
    {
      key: "COMMUTE-GROUP",
      score: 37,
      level: "Low",
      path: ["ROAD-X", "ROUTE-1", "STOP-A", "CONNECTION", "COMMUTE-GROUP"],
    },
  ],
};

function App() {
  const [activeStep, setActiveStep] = useState<DemoStep>("events");
  const [organization, setOrganization] = useState<DemoOrganization>("campus");
  const [eventTitle, setEventTitle] = useState(
    "Advanced Computing Laboratory unavailable",
  );
  const [severity, setSeverity] = useState(90);
  const [saved, setSaved] = useState(false);
  const [dependencySearch, setDependencySearch] = useState("");
  const [selectedResult, setSelectedResult] = useState(0);
  const [mitigationEnabled, setMitigationEnabled] = useState(false);

  const selectedOrganization = DEMO_ORGANIZATIONS[organization];
  const organizationResults = resultExamples[organization];
  const selectedImpact = organizationResults[selectedResult];

  const dependencyRows = useMemo(() => {
    const query = dependencySearch.trim().toLowerCase();
    const filtered = SYNTHETIC_DEPENDENCIES.filter(
      (dependency) =>
        dependency.organization === organization &&
        (!query ||
          dependency.sourceKey.toLowerCase().includes(query) ||
          dependency.targetKey.toLowerCase().includes(query) ||
          dependency.relationship.toLowerCase().includes(query)),
    );
    return { count: filtered.length, rows: filtered.slice(0, 8) };
  }, [dependencySearch, organization]);

  const entityById = useMemo(
    () => new Map(SYNTHETIC_ENTITIES.map((entity) => [entity.id, entity])),
    [],
  );

  function nameForKey(key: string) {
    return (
      selectedOrganization.entities.find((entity) => entity.key === key)
        ?.name ?? key
    );
  }

  function entityName(id: string) {
    return entityById.get(id)?.name ?? "Synthetic entity";
  }

  function saveEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(true);
    setActiveStep("dependencies");
  }

  function chooseOrganization(value: DemoOrganization) {
    setOrganization(value);
    setSelectedResult(0);
    setDependencySearch("");
    setEventTitle(DEMO_ORGANIZATIONS[value].eventTitle);
    setSeverity(DEMO_ORGANIZATIONS[value].severity);
    setSaved(false);
    setMitigationEnabled(false);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Ripple Effect prototype home">
          <span className="brand-mark" aria-hidden="true">
            R
          </span>
          <span>Ripple Effect</span>
        </a>
        <div className="topbar-controls">
          <label className="organization-picker">
            <span>Demo organization</span>
            <select
              value={organization}
              onChange={(event) =>
                chooseOrganization(event.target.value as DemoOrganization)
              }
            >
              <option value="campus">North Campus Demo</option>
              <option value="transport">City Transport Demo</option>
            </select>
          </label>
          <span className="prototype-badge">Interactive prototype</span>
        </div>
      </header>

      <main>
        <section className="intro" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">
              EVENT → DEPENDENCIES → CONSEQUENCES → DECISIONS
            </p>
            <h1 id="page-title">Explore a synthetic ripple scenario</h1>
            <p className="intro-copy">
              A click-through concept for tracing a change through modeled
              relationships and comparing a hypothetical intervention.
            </p>
          </div>
          <div className="scale-card" aria-label="Synthetic dataset size">
            <span className="scale-label">Synthetic scale sample</span>
            <strong>{DEMO_SCALE.entities.toLocaleString()} entities</strong>
            <span>
              {DEMO_SCALE.dependencies.toLocaleString()} relationships
            </span>
          </div>
        </section>

        <aside className="integrity-banner" role="note">
          <strong>Synthetic prototype — not research evidence.</strong>
          <span>
            Records and result values are illustrative placeholders. Scores are
            mock estimates, not probabilities or output from the analysis
            engine. The organization selector is a demo control, not tenant
            isolation.
          </span>
        </aside>

        <nav className="step-nav" aria-label="Prototype journey">
          {steps.map((step) => (
            <button
              aria-current={activeStep === step.id ? "step" : undefined}
              className={
                activeStep === step.id ? "step-button active" : "step-button"
              }
              key={step.id}
              onClick={() => setActiveStep(step.id)}
              type="button"
            >
              {step.label}
            </button>
          ))}
        </nav>

        {activeStep === "events" && (
          <section aria-labelledby="events-title" className="content-card">
            <div className="section-heading">
              <div>
                <p className="section-kicker">STEP 1 · EVENT</p>
                <h2 id="events-title">Describe the change</h2>
                <p>
                  This example is based on the brief’s synthetic{" "}
                  {selectedOrganization.label} scenario.
                </p>
              </div>
              <span className="status-pill">Draft event</span>
            </div>
            <form className="event-form" onSubmit={saveEvent}>
              <label>
                Event title
                <input
                  maxLength={120}
                  onChange={(event) => {
                    setEventTitle(event.target.value);
                    setSaved(false);
                  }}
                  required
                  value={eventTitle}
                />
              </label>
              <label>
                Severity (illustrative, 0–100)
                <input
                  max={100}
                  min={0}
                  onChange={(event) => {
                    setSeverity(Number(event.target.value));
                    setSaved(false);
                  }}
                  required
                  type="number"
                  value={severity}
                />
              </label>
              <div className="read-only-field">
                <span>Trigger entity</span>
                <strong>
                  {selectedOrganization.triggerKey} ·{" "}
                  {nameForKey(selectedOrganization.triggerKey)}
                </strong>
              </div>
              <div className="read-only-field">
                <span>Example start time</span>
                <strong>2026-11-07 09:00 UTC · synthetic fixture</strong>
              </div>
              <div className="form-actions">
                {saved && (
                  <p className="success-message" role="status">
                    Event saved in this page’s temporary prototype state only.
                  </p>
                )}
                <button className="primary-button" type="submit">
                  Save and continue to dependencies
                </button>
                <button
                  className="secondary-button"
                  onClick={() => setActiveStep("dependencies")}
                  type="button"
                >
                  Skip to dependencies
                </button>
              </div>
            </form>
          </section>
        )}

        {activeStep === "dependencies" && (
          <section
            aria-labelledby="dependencies-title"
            className="content-card"
          >
            <div className="section-heading">
              <div>
                <p className="section-kicker">STEP 2 · DEPENDENCIES</p>
                <h2 id="dependencies-title">Review modeled relationships</h2>
                <p>
                  Direction means a change in the source may affect the target.
                </p>
              </div>
              <span className="status-pill">
                {selectedOrganization.entities.length} named examples
              </span>
            </div>
            {saved && (
              <p className="success-message" role="status">
                Event saved in this page’s temporary prototype state only.
              </p>
            )}
            <label className="search-field">
              Search the synthetic graph
              <input
                onChange={(event) => setDependencySearch(event.target.value)}
                placeholder="Try SESSION or affects"
                type="search"
                value={dependencySearch}
              />
            </label>
            <p className="table-caption">
              Showing {dependencyRows.rows.length} of{" "}
              {dependencyRows.count.toLocaleString()} matching relationships in
              this demo organization.
            </p>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Source</th>
                    <th scope="col">Relationship</th>
                    <th scope="col">Target</th>
                    <th scope="col">Weight</th>
                    <th scope="col">Review</th>
                  </tr>
                </thead>
                <tbody>
                  {dependencyRows.rows.map((dependency) => (
                    <tr key={dependency.id}>
                      <td>{entityName(dependency.sourceId)}</td>
                      <td>{dependency.relationship}</td>
                      <td>{entityName(dependency.targetId)}</td>
                      <td>{dependency.weight.toFixed(2)}</td>
                      <td>{dependency.reviewStatus}</td>
                    </tr>
                  ))}
                  {dependencyRows.rows.length === 0 && (
                    <tr>
                      <td className="empty-cell" colSpan={5}>
                        No synthetic relationships match that search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="section-actions">
              <button
                className="primary-button"
                onClick={() => setActiveStep("analysis")}
                type="button"
              >
                Review example analysis
              </button>
            </div>
          </section>
        )}

        {activeStep === "analysis" && (
          <section aria-labelledby="analysis-title" className="content-card">
            <div className="section-heading">
              <div>
                <p className="section-kicker">STEP 3 · CONSEQUENCES</p>
                <h2 id="analysis-title">Inspect the illustrative result</h2>
                <p>
                  Example event: <strong>{eventTitle}</strong>
                </p>
              </div>
              <span className="status-pill">Mock result</span>
            </div>
            <div className="estimate-callout" role="note">
              These values are illustrative mock estimates, not probabilities
              and not produced by the Ripple Effect engine.
            </div>
            <div className="analysis-layout">
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Entity</th>
                      <th scope="col">Mock score</th>
                      <th scope="col">Illustrative level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {organizationResults.map((result, index) => (
                      <tr
                        aria-selected={selectedResult === index}
                        className={
                          selectedResult === index ? "selected-row" : undefined
                        }
                        key={result.key}
                      >
                        <td>
                          <button
                            aria-pressed={selectedResult === index}
                            className="table-link"
                            onClick={() => setSelectedResult(index)}
                            type="button"
                          >
                            {nameForKey(result.key)}
                          </button>
                        </td>
                        <td>{result.score}</td>
                        <td>{result.level}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <aside className="detail-panel" aria-live="polite">
                <p className="section-kicker">SELECTED ENTITY</p>
                <h3>{nameForKey(selectedImpact.key)}</h3>
                <p>
                  Mock dependency-review confidence: <strong>0.72</strong>
                  <br />
                  This illustrative value is not a probability.
                </p>
                <h4>Example path</h4>
                <ol className="path-list">
                  {selectedImpact.path.map((key) => (
                    <li key={key}>{nameForKey(key)}</li>
                  ))}
                </ol>
                <p className="muted-copy">
                  A production result would include its run configuration,
                  provenance, alternatives, and data-quality assumptions.
                </p>
              </aside>
            </div>
            <div className="section-actions">
              <button
                className="primary-button"
                onClick={() => setActiveStep("scenario")}
                type="button"
              >
                Explore a hypothetical intervention
              </button>
            </div>
          </section>
        )}

        {activeStep === "scenario" && (
          <section aria-labelledby="scenario-title" className="content-card">
            <div className="section-heading">
              <div>
                <p className="section-kicker">STEP 4 · DECISIONS</p>
                <h2 id="scenario-title">Compare a hypothetical scenario</h2>
                <p>
                  Baseline and scenario values below are illustrative mock
                  figures.
                </p>
              </div>
              <span className="status-pill">Scenario v1 · unsaved</span>
            </div>
            <div className="scenario-notice" role="note">
              <strong>Hypothetical only — live data unchanged.</strong>
              <span>
                This control changes temporary prototype values only. It does
                not create or modify a real event, dependency, or analysis run.
              </span>
            </div>
            <label className="toggle-row">
              <input
                checked={mitigationEnabled}
                onChange={(event) => setMitigationEnabled(event.target.checked)}
                type="checkbox"
              />
              <span>
                Apply a mock mitigation to {nameForKey(selectedImpact.key)}
              </span>
            </label>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Entity</th>
                    <th scope="col">Baseline mock score</th>
                    <th scope="col">Scenario mock score</th>
                    <th scope="col">Illustrative change</th>
                  </tr>
                </thead>
                <tbody>
                  {organizationResults
                    .filter(
                      (result, index) =>
                        index < 3 || result.key === selectedImpact.key,
                    )
                    .map((result) => {
                      const scenarioScore =
                        result.key === selectedImpact.key && mitigationEnabled
                          ? Math.max(0, result.score - 20)
                          : result.score;
                      return (
                        <tr key={result.key}>
                          <td>{nameForKey(result.key)}</td>
                          <td>{result.score}</td>
                          <td>{scenarioScore}</td>
                          <td>
                            {scenarioScore === result.score
                              ? "No change"
                              : `${scenarioScore - result.score} mock points`}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
            <div className="section-actions">
              <button
                className="secondary-button"
                onClick={() => setActiveStep("events")}
                type="button"
              >
                Restart journey
              </button>
            </div>
          </section>
        )}
      </main>

      <footer className="page-footer">
        <span>Ripple Effect · UX prototype</span>
        <span>
          Synthetic scale sample for interaction exploration; not a benchmark.
        </span>
      </footer>
    </div>
  );
}

export default App;
