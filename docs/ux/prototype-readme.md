# Synthetic UX prototype

## Status and scope

This is an agent-created, interactive React concept for exploring the proposed task flow. It is not the human-owned Figma file, a validated design, or the production application. It contains no interview observations or usability results.

## Run it

From the repository root in PowerShell:

```powershell
Set-Location frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`.

## Click-through

1. Edit and save the synthetic event.
2. Search the dependency table and inspect source → target direction.
3. Select an example impact and review its illustrative path.
4. Toggle a hypothetical mitigation and compare mock baseline/scenario values.

The organization selector switches between the synthetic campus and transport examples. It is presentation-only and does not implement tenant isolation.

## Synthetic scale sample

The browser generates a deterministic graph in memory:

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
