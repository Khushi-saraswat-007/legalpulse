import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import cytoscape from "cytoscape";
import { getReport } from "../api/contracts";
import Loader from "../components/Loader";

export default function GraphView() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    getReport(id).then(setReport).catch(() => setError("Could not load the graph."));
  }, [id]);

  useEffect(() => {
    if (!report || !containerRef.current) return;

    const triggers = new Set(report.risks.map((r) => r.trigger_clause));
    const impacted = new Set(report.risks.flatMap((r) => r.impacted_clauses));

    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...report.graph.nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.label,
            role: triggers.has(n.id) ? "trigger" : impacted.has(n.id) ? "impacted" : "normal",
          },
        })),
        ...report.graph.edges.map((e, i) => ({
          data: { id: `e${i}`, source: e.source, target: e.target, label: e.type.replace("_", " ") },
        })),
      ],
      layout: { name: "breadthfirst", directed: true,direction:"rightward", padding: 50, spacingFactor: 2.2 },
      style: [
        { selector: "node", style: { label: "data(label)", "text-valign": "bottom", "text-margin-y": 10, "font-size": 14, "font-weight": 600, color: "#141a3a", "background-color": "#8A94A3", width: 34, height: 34 } },
        { selector: 'node[role = "trigger"]', style: { "background-color": "#C2410C", width: 44, height: 44 } },
        { selector: 'node[role = "impacted"]', style: { "background-color": "#B7791F" } },
        { selector: "edge", style: { width: 2, "line-color": "#B8BFC9", "target-arrow-color": "#B8BFC9", "target-arrow-shape": "triangle", "curve-style": "bezier", label: "data(label)", "font-size": 10, color: "#5B6573", "text-rotation": "autorotate", "text-margin-y": -10, "text-background-color": "#ffffff", "text-background-opacity": 1, "text-background-padding": 2 } },      ],
    });

    return () => cy.destroy();
  }, [report]);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <Loader text="Loading graph…" />;

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Clause dependencies</h1>
          <p className="muted">Arrows point from a clause to the clause it relies on.</p>
        </div>
        <Link className="btn" to={`/report/${id}`}>Back to report</Link>
      </div>
      <ul className="legend">
        <li><i style={{ background: "#C2410C" }} /> Triggering change</li>
        <li><i style={{ background: "#B7791F" }} /> Impacted clause</li>
        <li><i style={{ background: "#8A94A3" }} /> Other clause</li>
      </ul>
      <div ref={containerRef} className="graph-canvas" aria-label="Clause dependency graph" />
    </section>
  );
}
