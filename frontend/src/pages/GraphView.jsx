import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/contracts";
import Loader from "../components/Loader";
import DependencyGraph, { GraphLegend } from "../components/DependencyGraph";
import ContractSwitcher from "../components/ContractSwitcher";
import { cleanName } from "../lib/format";

export default function GraphView() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getReport(id).then(setReport).catch(() => setError("Something went wrong. Please try again."));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <Loader text="Loading graph…" />;

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="crumb">Graph <span>/</span> <b className="mono">{cleanName(report.contract_id)}</b></p>
          <h1>Clause dependencies</h1>
          <p className="muted">
            {report.graph.nodes.length} clauses · {report.graph.edges.length} links · arrows point from a clause to the clause it relies on.
          </p>
        </div>
        <div className="actions">
          <ContractSwitcher current={id} to={(x) => `/graph/${x}`} />
          <Link className="btn" to={`/report/${id}`}>Back to report</Link>
        </div>
      </div>
      <div className="panel light">
        <div className="panel-body">
          <GraphLegend />
          <DependencyGraph report={report} height={560} />
        </div>
      </div>
    </section>
  );
}
