import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/contracts";
import RiskBadge from "../components/RiskBadge";
import Loader from "../components/Loader";

export default function ReportViewer() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getReport(id).then(setReport).catch(() => setError("Could not load this report. Is the backend running?"));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <Loader text="Loading report…" />;

  const risks = [...report.risks].sort((a, b) => a.rank - b.rank);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Risk report</h1>
          <p className="muted">Contract {report.contract_id} · {risks.length} ranked risk{risks.length === 1 ? "" : "s"}</p>
        </div>
        <div className="actions">
          <Link className="btn" to={`/diff/${id}`}>View changes</Link>
          <Link className="btn" to={`/graph/${id}`}>View dependency graph</Link>
        </div>
      </div>

      {risks.length === 0 && <p className="muted">No risks found for this contract.</p>}

      <ol className="risk-list">
        {risks.map((r) => (
          <li key={r.rank} className={`risk risk-${r.severity}`}>
            <span className="risk-rank">{r.rank}</span>
            <div className="risk-body">
              <div className="risk-top">
                <RiskBadge severity={r.severity} />
                {r.score !== undefined && <span className="muted">score {r.score.toFixed(2)}</span>}
              </div>
              <p className="risk-explain">{r.explanation}</p>
              <p className="muted">
                Triggered by clause <strong>{r.trigger_clause}</strong>
                {r.impacted_clauses.length > 0 && <> · affects {r.impacted_clauses.join(", ")}</>}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
