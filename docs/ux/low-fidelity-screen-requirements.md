# Low-fidelity screen requirements

> **Requirements for a human-created wireframe, not completed screens.** No wireframes or validated visual design are included in this repository yet.

## 1. Application shell

- Active organization selector is persistently visible.
- Account/session controls and clear page titles.
- Keyboard-accessible navigation and visible focus.
- Role-gated administration is reflected as presentation only; server authorization remains required.

## 2. Dashboard

- Open events and recent runs with empty/loading/error states.
- Show counts only when sourced from actual data.
- Avoid trend claims without measured history.
- Clear actions for creating an event or opening the dependency model.

## 3. Event manager and editor

- Search, stable sorting/filtering, status/severity indicators.
- Fields for title, description, severity, required start time, and optional duration.
- Trigger entity picker with optional rationale/exposure.
- Draft/open lifecycle actions and validation errors that preserve entered values.
- Explain duration is informational in v1.

## 4. Entity catalogue and detail

- Searchable table/list with name, type, status, exposure, mitigation, archive state.
- Detail view separates outbound “may affect” from inbound “requires/is hosted in” relationships.
- Avoid color-only status encoding.

## 5. Dependency editor

- Source and target selectors, relationship type, weight, review status, rationale, validity window, active state.
- Directional sentence preview: “A change in [source] may affect [target].”
- Inline errors for self-loop, duplicate pair, invalid values, and unauthorized operations.
- Graph/list alternative for browsing dependencies.

## 6. Ripple analysis

- Event and trigger review.
- Configuration for maximum depth, minimum edge weight, attenuation, and aggregation.
- Estimate-not-probability notice before execution and near results.
- Run status and summary counts.
- Impact level legend with labels/shapes as well as color.
- Incomplete-run warning that cannot be mistaken for completed analysis.

## 7. Entity result detail

- Estimated score/level, minimum depth, primary path length, and trigger provenance.
- Directed path, relationship labels, weights, review status, and alternatives.
- Confidence value/label with explanation that it describes dependency-data review quality.
- Assumptions, configuration, event/run metadata, and limits.
- When primary path is longer than minimum depth, display both and explain the difference.

## 8. Scenario lab and comparison

- Baseline run and scenario version visible.
- Intervention editor for mitigation, weight override, deactivation, or hypothetical dependency.
- Rationale and assumptions are required/visible.
- “Hypothetical only — live data unchanged” notice.
- Comparison table for changed, newly reached, and no-longer-reached entities.

## 9. Administration

- Members, roles, organization settings, and audit history.
- Confirm destructive membership changes; show permission errors without leaking other organizations' records.

## Shared interaction states

Provide low-fidelity examples of loading, empty, error, validation, success, disabled, permission denied, and incomplete analysis states. Use synthetic labels only.
