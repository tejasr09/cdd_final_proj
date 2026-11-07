# ADR-003: Impact scoring heuristic

- Status: Accepted
- Date: 2026-11-07
- Decision owners: TODO(human)
- Source: `agent-brief.md`, D3

## Context

The impact estimate must account for event severity, trigger exposure, node mitigation, edge weights, and depth attenuation while remaining explainable.

## Decision

For a path of k edges starting at trigger t:

```text
S_eff = (severity / 100) * exposure_t * (1 - m_t)
path_score = S_eff * product(i=1..k, w_i * d * (1 - m_vi))
```

`w_i` is an edge weight, `d` is depth attenuation (default 0.8), and `m` is optional node mitigation (default 0). With no mitigation and exposure 1, this reduces to normalized severity times the product of edge weights and `d^k`. For severity 0.9, weights 0.8 and 0.7, and `d = 0.8`, the score is 0.32256, or 32.3 out of 100 when displayed.

The score is a configurable heuristic, not a probability or guaranteed prediction.

## Consequences

Results need to expose enough assumptions and path data to explain the estimate. The formula does not itself specify implementation technology or event semantics beyond the stated inputs.

## Alternatives considered

- Omitting exposure or node mitigation was rejected because D3 explicitly includes both.
- Treating the score as probability was rejected by the decision-support principle.

## Evidence

D3 in `agent-brief.md`, including the worked 0.32256 example. The decision was included in the previously approved bounded Phase 0.
