# Historical synthetic UX prototype

## Status and scope

This document records the agent-created, synthetic React concept built during
Phase 2. Phase 6 replaced the active frontend with an API-connected application;
the click-through prototype is not currently runnable from `frontend/src/App.tsx`.
It was not the human-owned Figma file, a validated design, or research evidence.
It contains no interview observations or usability results.

## Historical click-through scope

The prior concept allowed users to edit a temporary synthetic event, inspect
sample source → target dependencies, review a mock impact path, and toggle a
non-persistent hypothetical mitigation. Those controls were not connected to
the API or analysis engine.

The organization selector switches between the synthetic campus and transport examples. It is presentation-only and does not implement tenant isolation.

## Synthetic scale sample

The prior browser concept generated a deterministic graph in memory:

- 10,018 entities across two synthetic organizations.
- 30,017 directed relationships.
- 18 named fixture entities and 17 named fixture relationships from Appendix C.
- 10,000 additional generated entities, each with three generated relationships.
- Stable UUID-shaped identifiers and synthetic labels; no external or institutional data is used.

The interface renders only a small page of matching rows; counts describe the generated in-memory sample, not the number of records processed by a production engine. This is not a performance benchmark or evidence of “big data” scalability.

## Important limitations

- Event edits and scenario controls exist only in the current page state; nothing is persisted or sent to the API.
- Impact scores, confidence, paths, and scenario deltas are illustrative mock examples, not graph-engine calculations.
- The front-end organization selector is not authentication, authorization, or tenant isolation.
- The sample is synthetic and must not be described as real campus or transport data.
- This prototype does not replace interviews, consent, findings, usability tests, or the human-owned Figma deliverable required by Phase 2.
