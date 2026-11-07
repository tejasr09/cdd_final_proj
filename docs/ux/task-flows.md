# Task flows

> **Design proposal — not observed behavior.** Flows are derived from the required journeys. Validate sequencing, labels, and failure recovery with participants.

## A. Register an event

```mermaid
flowchart TD
  A[Open Events] --> B[Create event]
  B --> C[Enter title, severity, start time]
  C --> D[Select trigger entities]
  D --> E[Add rationale and optional exposure]
  E --> F{Valid and authorized?}
  F -- No --> G[Show field errors; preserve input]
  G --> C
  F -- Yes --> H[Save as draft or open]
  H --> I[Show saved event and status]
```

Questions: who may open an event; can a draft be previewed; what makes a trigger required?

## B. Maintain a dependency

```mermaid
flowchart TD
  A[Open dependency model] --> B[Select source and target]
  B --> C[Choose relationship and weight]
  C --> D[Set review status, rationale, validity]
  D --> E[Preview: source may affect target]
  E --> F{Valid pair and permitted?}
  F -- No --> G[Explain duplicate, self-loop, or permission error]
  F -- Yes --> H[Save dependency]
  H --> I[Show in directional graph and list]
```

Questions: how are duplicate relationships noticed; who reviews a draft dependency; how are temporal changes handled?

## C. Run and inspect analysis

```mermaid
flowchart TD
  A[Choose open event] --> B[Review trigger entities]
  B --> C[Set depth, edge threshold, attenuation, aggregation]
  C --> D[Review estimate-not-probability notice]
  D --> E[Run analysis]
  E --> F{Run status}
  F -- Failed --> G[Show safe error and retry guidance]
  F -- Completed with limits --> H[Show incomplete warning]
  F -- Completed --> I[Show summary and impact levels]
  H --> I
  I --> J[Select entity]
  J --> K[Inspect path, assumptions, confidence, alternatives]
```

Questions: which configuration values should be defaults; which result details need explanation first?

## D. Create and compare a scenario

```mermaid
flowchart TD
  A[Select completed baseline run] --> B[Create scenario]
  B --> C[Add intervention and rationale]
  C --> D[Review hypothetical-only notice]
  D --> E[Run scenario overlay]
  E --> F[Compare entities and score deltas]
  F --> G[Inspect assumptions and changed paths]
  G --> H[Discard or archive scenario]
  H --> I[Confirm live data unchanged]
```

Questions: how should users identify scenario versions; which differences need emphasis; what retention behavior is expected?
