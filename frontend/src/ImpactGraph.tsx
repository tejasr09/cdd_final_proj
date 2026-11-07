import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { ImpactPath } from "./api";

type ImpactGraphProps = {
  path: ImpactPath | null;
};

function pathNodes(path: ImpactPath): Node[] {
  const { entity_ids: entityIds, entity_names: entityNames } = path.provenance;
  const steps = path.provenance.steps;
  return entityIds.map((id, index) => {
    const step = steps.find((candidate) => candidate.entity_id === id);
    const label = step?.entity_name ?? entityNames[index] ?? id;
    return {
      id,
      type:
        index === 0
          ? "input"
          : index === entityIds.length - 1
            ? "output"
            : "default",
      data: { label },
      position: { x: index * 205, y: 70 },
      ariaLabel: `${index === 0 ? "Trigger" : "Affected entity"}: ${label}`,
    };
  });
}

function pathEdges(path: ImpactPath): Edge[] {
  const ids = path.provenance.entity_ids;
  const steps = path.provenance.steps;
  return ids.slice(1).map((targetId, index) => {
    const step = steps.find((candidate) => candidate.entity_id === targetId);
    const relation =
      step?.relationship_label ?? step?.relationship_type ?? "affects";
    const weight =
      typeof step?.weight === "number"
        ? ` · weight ${step.weight.toFixed(2)}`
        : "";
    return {
      id: `${ids[index]}-${targetId}-${index}`,
      source: ids[index],
      target: targetId,
      label: `${relation}${weight}`,
      markerEnd: { type: MarkerType.ArrowClosed },
      ariaLabel: `${relation}${weight}`,
    };
  });
}

export default function ImpactGraph({ path }: ImpactGraphProps) {
  if (!path) {
    return (
      <p className="empty-state">
        No retained path is available for this result.
      </p>
    );
  }

  const nodes = pathNodes(path);
  const edges = pathEdges(path);
  const steps = path.provenance.steps;
  const entityNames = nodes.map((node) => String(node.data.label));

  return (
    <section className="graph-section" aria-labelledby="graph-title">
      <div className="section-heading compact-heading">
        <div>
          <h3 id="graph-title">Primary impact path</h3>
          <p>Arrows point from the dependency source to the affected target.</p>
        </div>
        {path.is_primary && <span className="status-pill">Primary path</span>}
      </div>
      <div
        className="flow-canvas"
        role="group"
        aria-label={`Directed impact graph: ${entityNames.join(" to ")}`}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          fitViewOptions={{ padding: 0.18 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          defaultEdgeOptions={{ type: "smoothstep" }}
          minZoom={0.45}
          maxZoom={1.5}
        >
          <Background />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <div className="accessible-path">
        <h4>Keyboard-accessible path details</h4>
        <ol aria-label="Source-to-target impact path">
          {nodes.map((node, index) => {
            const nextNode = nodes[index + 1];
            const step = steps.find(
              (candidate) => candidate.entity_id === nextNode?.id,
            );
            const relation =
              step?.relationship_label ?? step?.relationship_type;
            return (
              <li key={node.id}>
                <span className="path-role">
                  {index === 0
                    ? "Trigger"
                    : index === nodes.length - 1
                      ? "Affected entity"
                      : `Step ${index + 1}`}
                </span>
                <strong>{String(node.data.label)}</strong>
                {index < nodes.length - 1 && (
                  <span className="path-edge">
                    {relation ? `${relation} →` : "affects →"}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
