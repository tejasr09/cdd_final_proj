# Information architecture

> **Design proposal — not user-validated.** Structure follows the approved product and role requirements; validate labels and grouping with participants.

## Global application shell

- Organization selector with the active organization visibly identified.
- Account/session controls.
- Primary navigation:
  1. Dashboard
  2. Events
  3. Dependency model
     - Entities
     - Dependencies
  4. Ripple analysis and run history
  5. Scenario lab
  6. Administration (permission-gated)

Switching organization must refresh tenant-scoped content and clear stale cached records from the prior organization.

## Page hierarchy and key content

### Dashboard

- Open events and recent runs.
- Counts only when backed by actual tenant data.
- High/critical estimated results from completed runs.
- Quick actions and first-use empty states.

### Events

- Search/filter/list.
- Event detail and lifecycle.
- Trigger entity associations and rationale/exposure.
- Eligible analysis action for open events.

### Dependency model

- Entity catalogue and detail.
- Dependency list/editor with source → target phrasing.
- Inbound/outbound dependency views with reverse-language labels.
- Review status and validity information.

### Analysis

- Event selection and run configuration.
- Run status, result summary, filters, and accessible list alternative to graph.
- Entity detail with minimum depth, primary/contributing paths, confidence reason, assumptions, and limitations.
- Historical run details from the stored snapshot.

### Scenario lab

- Baseline run selection.
- Scenario metadata and version.
- Intervention/override list with rationale and assumptions.
- Scenario run and baseline comparison.
- Visible “hypothetical only — live data unchanged” notice.

### Administration

- Organization settings, members/roles, and audit history.
- Server-side authorization remains authoritative; navigation hiding is not security enforcement.

## Cross-cutting states

- Loading, empty, validation error, permission denied, unavailable, success, and incomplete-run states.
- Estimate-not-probability notice adjacent to analysis results.
- Visible run configuration, algorithm version, confidence meaning, and data-quality assumptions.

## Research questions

- Do participants group entities and dependencies together or separately?
- Which labels match their vocabulary?
- Where should run history and scenarios sit in the navigation?
- Which actions need confirmation or role-specific affordances?
