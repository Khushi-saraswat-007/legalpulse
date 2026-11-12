import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import { SEVERITY_ORDER, SEV_NODE, shortId } from "../lib/format";

// Clause dependency graph (Cytoscape). Used on the dashboard (compact) and on the graph page (full).
// Arrows point from a clause to the clause it relies on. Clauses that were deleted in the new version
// are not in the graph, so they are drawn as dashed "removed" nodes linked to the clauses that depended on them.
export default function DependencyGraph({ report, height = 480, compact = false }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!report || !ref.current) return;

    const nodeIds = new Set(report.graph.nodes.map((n) => n.id));

    // strongest severity per triggering clause
    const sevOf = {};
    for (const r of report.risks) {
      const cur = sevOf[r.trigger_clause];
      if (!cur || SEVERITY_ORDER.indexOf(r.severity) < SEVERITY_ORDER.indexOf(cur)) sevOf[r.trigger_clause] = r.severity;
    }
    const impacted = new Set(report.risks.flatMap((r) => r.impacted_clauses));

    const elements = [
      ...report.graph.nodes.map((n) => {
        const sev = sevOf[n.id];
        const role = sev ? "changed" : impacted.has(n.id) ? "impacted" : "normal";
        return { data: { id: n.id, label: n.label || shortId(n.id), role, sev: sev || "" } };
      }),
      ...report.graph.edges.map((e, i) => ({
        data: { id: `e${i}`, source: e.source, target: e.target, label: compact ? "" : e.type.replace("_", " ") },
      })),
    ];

    // ghost nodes for deleted clauses
    let g = 0;
    for (const r of report.risks) {
      if (nodeIds.has(r.trigger_clause)) continue;
      elements.push({ data: { id: r.trigger_clause, label: `${shortId(r.trigger_clause)} removed`, role: "removed", sev: r.severity } });
      for (const c of r.impacted_clauses) {
        if (nodeIds.has(c)) elements.push({ data: { id: `g${g++}`, source: c, target: r.trigger_clause, label: compact ? "" : "cites" } });
      }
    }

    const nodeStyle = (sev) => ({ "background-color": SEV_NODE[sev].bg, "border-color": SEV_NODE[sev].border });

    const cy = cytoscape({
      container: ref.current,
      elements,
      layout: { name: "breadthfirst", directed: true, direction: "rightward", padding: compact ? 16 : 40, spacingFactor: compact ? 1.25 : 1.7 },
      style: [
        {
          selector: "node",
          style: {
            shape: "round-rectangle", label: "data(label)", "text-valign": "center", "text-halign": "center",
            "font-family": "IBM Plex Mono, ui-monospace, monospace", "font-size": compact ? 10 : 11, "font-weight": 500, color: "#556070",
            width: "label", height: compact ? 26 : 30, padding: "9px", "text-wrap": "ellipsis", "text-max-width": compact ? "120px" : "170px",
            "background-color": "#ffffff", "border-width": 1, "border-color": "#b9bfca",
          },
        },
        { selector: 'node[role = "impacted"]', style: { "border-width": 2, "border-color": "#2745d8", color: "#0e1726" } },
        { selector: 'node[role = "changed"]', style: { "border-width": 1.5, color: "#0e1726", "font-weight": 600 } },
        { selector: 'node[role = "removed"]', style: { "border-style": "dashed", "border-width": 1.5, color: "#8a1228" } },
        ...SEVERITY_ORDER.map((s) => ({ selector: `node[role = "changed"][sev = "${s}"]`, style: nodeStyle(s) })),
        { selector: 'node[role = "removed"]', style: { "background-color": "#fbe9ec", "border-color": "#a61e36" } },
        {
          selector: "edge",
          style: {
            width: 1.5, "line-color": "#98a2b3", "target-arrow-color": "#98a2b3", "target-arrow-shape": "triangle", "curve-style": "bezier",
            label: "data(label)", "font-size": 9, "font-family": "IBM Plex Mono, ui-monospace, monospace", color: "#556070",
            "text-rotation": "autorotate", "text-margin-y": -8, "text-background-color": "#ffffff", "text-background-opacity": 1, "text-background-padding": 2,
          },
        },
      ],
    });

    return () => cy.destroy();
  }, [report, compact]);

  return <div ref={ref} className="graph-canvas" style={{ height }} role="img" aria-label="Clause dependency graph" />;
}

export function GraphLegend() {
  return (
    <ul className="legend">
      <li><i style={{ background: "#fbf3d9", border: "1.5px solid #8f6a00" }} /> Changed clause (coloured by severity)</li>
      <li><i style={{ background: "#fff", border: "2px solid #2745d8" }} /> Impacted clause</li>
      <li><i style={{ background: "#fbe9ec", border: "1.5px dashed #a61e36" }} /> Removed in the new version</li>
      <li><i style={{ background: "#fff", border: "1px solid #b9bfca" }} /> Unchanged clause</li>
    </ul>
  );
}
