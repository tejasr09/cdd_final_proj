import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ImpactPath } from "./api";
import ImpactGraph from "./ImpactGraph";

vi.mock("@xyflow/react", () => ({
  Background: () => null,
  Controls: () => null,
  MarkerType: { ArrowClosed: "arrowclosed" },
  ReactFlow: ({
    nodes,
    edges,
  }: {
    nodes: { id: string }[];
    edges: { source: string; target: string }[];
  }) => (
    <div data-testid="flow-canvas">
      {nodes.length} nodes and {edges.length} directed edges
    </div>
  ),
}));

const path: ImpactPath = {
  id: "path-id",
  run_id: "run-id",
  entity_id: "target-id",
  trigger_entity_id: "source-id",
  score: 18.4,
  edge_count: 1,
  is_primary: true,
  provenance: {
    entity_ids: ["source-id", "target-id"],
    entity_names: ["Source", "Target"],
    dependency_labels: ["requires"],
    dependency_types: ["requires"],
    weights: [0.8],
    review_statuses: ["reviewed"],
    steps: [
      {
        entity_id: "source-id",
        entity_name: "Source",
        entity_type: "resource",
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
        entity_id: "target-id",
        entity_name: "Target",
        entity_type: "activity",
        mitigation: 0,
        dependency_id: "dependency-id",
        relationship_type: "requires",
        relationship_label: "requires",
        weight: 0.8,
        review_status: "reviewed",
        rationale: "Resource enables activity",
        is_hypothetical: false,
      },
    ],
  },
};

describe("ImpactGraph", () => {
  it("keeps a keyboard-accessible source-to-target alternative in sync with the graph", () => {
    render(<ImpactGraph path={path} />);

    expect(screen.getByTestId("flow-canvas")).toHaveTextContent(
      "2 nodes and 1 directed edges",
    );
    expect(
      screen.getByRole("group", {
        name: "Directed impact graph: Source to Target",
      }),
    ).toBeInTheDocument();
    const pathList = screen.getByRole("list", {
      name: "Source-to-target impact path",
    });
    expect(pathList).toHaveTextContent(
      /Trigger\s*Source\s*requires →\s*Affected entity\s*Target/,
    );
  });

  it("explains when a result has no retained path", () => {
    render(<ImpactGraph path={null} />);

    expect(
      screen.getByText("No retained path is available for this result."),
    ).toBeInTheDocument();
  });
});
