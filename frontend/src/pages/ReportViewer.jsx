import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/contracts";
import RiskBadge from "../components/RiskBadge";
import Loader from "../components/Loader";
import ContractSwitcher from "../components/ContractSwitcher";
import { cleanName, parseExplanation, shortId } from "../lib/format";

export default function ReportViewer() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getReport(id).then(setReport).catch(() => setError("Something went wrong. Please try again."));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <Loader text="Loading report…" />;

  const risks = [...report.risks].sort((a, b) => a.rank - b.rank);
  const high = risks.filter((r) => r.severity === "high" || r.severity === "critical").length;
  const changed = report.changes.filter((c) => c.change_type !== "unchanged").length;
  const meta = report.meta;

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="crumb">Report <span>/</span> <b className="mono">{cleanName(report.contract_id)}</b></p>
          <h1>Risk report</h1>
          <p className="muted">
            {risks.length} ranked risk{risks.length === 1 ? "" : "s"}
            {meta?.embedder && <> · embedder: {meta.embedder}</>}
            {meta?.nli && <> · nli: {meta.nli.replace("cross-encoder/", "")}</>}
          </p>
        </div>
        <div className="actions">
          <ContractSwitcher current={id} to={(x) => `/report/${x}`} />
          <Link className="btn" to={`/diff/${id}`}>View changes</Link>
          <Link className="btn" to={`/graph/${id}`}>View dependency graph</Link>
        </div>
      </div>

      <div className="stat-strip">
        <div className="stat"><span className="label">Ranked risks</span><b className="mono">{risks.length}</b><small>sorted by score</small></div>
        <div className="stat"><span className="label">High or critical</span><b className="mono">{high}</b><small>need review first</small></div>
        <div className="stat"><span className="label">Clause changes</span><b className="mono">{changed}</b><small>between versions</small></div>
        <div className="stat">
          <span className="label">Contradictions</span><b className="mono">{meta?.contradictions ?? 0}</b>
          <small>{meta?.contradictions_status === "experimental" ? "experimental" : "in the new version"}</small>
        </div>
      </div>

      {risks.length === 0 ? (
        <div className="panel"><p className="panel-empty">No risks found for this contract.</p></div>
      ) : (
        <section className="panel light">
          <div className="table-wrap">
            <table className="tbl tbl-report">
              <thead>
                <tr><th>#</th><th>Severity</th><th>What changed</th><th>Clause</th><th>Score</th></tr>
              </thead>
              <tbody>
                {risks.map((r) => {
                  const ex = parseExplanation(r.explanation);
                  return (
                    <tr key={r.rank}>
                      <td className="mono muted">{String(r.rank).padStart(2, "0")}</td>
                      <td><RiskBadge severity={r.severity} /></td>
                      <td>
                        <p className="risk-explain">{ex.text}</p>
                        {r.impacted_clauses.length > 0 && (
                          <p className="muted">Affects {r.impacted_clauses.map((c) => <span className="chip mono" key={c}>{shortId(c)}</span>)}</p>
                        )}
                        {ex.parts && (
                          <p className="parts mono">
                            change {ex.parts.change?.toFixed(2)} · impact {ex.parts.impact?.toFixed(2)} · contradiction {ex.parts.contradiction ? "yes" : "no"}
                          </p>
                        )}
                      </td>
                      <td className="mono">{shortId(r.trigger_clause)}</td>
                      <td>
                        <span className="score">
                          <span className="mono">{(r.score ?? 0).toFixed(2)}</span>
                          <span className="score-bar"><span style={{ width: `${Math.min(100, (r.score ?? 0) * 100)}%` }} /></span>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </section>
  );
}
