import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Upload } from "lucide-react";
import { getReport, getStats, listContracts } from "../api/contracts";
import { listAlerts } from "../api/alerts";
import RiskBadge from "../components/RiskBadge";
import Loader from "../components/Loader";
import DependencyGraph, { GraphLegend } from "../components/DependencyGraph";
import { SEV_COLOR, SEVERITY_ORDER, countBySeverity, parseExplanation, shortId } from "../lib/format";

export default function Dashboard() {
  const [contracts, setContracts] = useState(null);
  const [report, setReport] = useState(null);
  const [totals, setTotals] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const list = await listContracts();
        setContracts(list);
        setTotals(await getStats());
        if (list.length > 0) setReport(await getReport(list[0].id));
        listAlerts().then(setAlerts).catch(() => {});
      } catch {
        setError("Something went wrong . Please try again .");
      }
    }
    load();
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!contracts) return <Loader text="Loading your dashboard…" />;

  if (contracts.length === 0) {
    return (
      <section>
        <div className="page-head">
          <div>
            <h1>Overview</h1>
            <p className="muted">Nothing analysed yet.</p>
          </div>
          <Link to="/upload" className="btn btn-primary"><Upload size={16} /> Upload and analyse</Link>
        </div>
        <div className="panel"><p className="panel-empty">Upload an earlier and a revised version of a contract to see its risks, changes and dependency graph here.</p></div>
      </section>
    );
  }

  const latest = contracts[0];
  const risks = report ? [...report.risks].sort((a, b) => a.rank - b.rank) : [];
  const counts = countBySeverity(risks);
  const highCount = counts.filter((c) => c.name === "high" || c.name === "critical").reduce((n, c) => n + c.value, 0);
  const changeCount = report ? report.changes.filter((c) => c.change_type !== "unchanged").length : 0;
  const clauseCount = report ? report.graph.nodes.length : 0;
  const unseen = alerts.filter((a) => !a.seen);
  const meta = report?.meta;

  const stats = [
    { label: "Contracts analysed", value: totals?.contracts ?? contracts.length, note: "all uploads" },
    { label: "High-risk issues", value: totals?.high_risk ?? highCount, note: "high or critical" },
    { label: "Changes detected", value: totals?.changes ?? changeCount, note: "between versions" },
    { label: "Clauses mapped", value: totals?.clauses ?? clauseCount, note: "in dependency graphs" },
  ];

  return (
    <div className="dash">
      <div className="page-head">
        <div>
          <p className="crumb">Dashboard <span>/</span> <b className="mono">{latest.name}</b></p>
          <h1>Overview</h1>
          <p className="muted">
            Latest analysis · <span className="mono">{latest.versions}</span>
            {meta?.embedder && <> · embedder: {meta.embedder}</>}
            {meta?.nli && <> · nli: {meta.nli.replace("cross-encoder/", "")}</>}
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary"><Upload size={16} /> Upload and analyse</Link>
      </div>

      <div className="stat-strip">
        {stats.map((s) => (
          <div className="stat" key={s.label}>
            <span className="label">{s.label}</span>
            <b className="mono">{s.value}</b>
            <small>{s.note}</small>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <section className="panel panel-wide light">
          <div className="panel-head">
            <div>
              <h2>Top risks</h2>
              <p className="muted">Latest analysis · ranked by score</p>
            </div>
            <Link to={`/report/${latest.id}`}>Open full report →</Link>
          </div>
          {risks.length === 0 ? (
            <p className="panel-empty">No risks found for the latest analysis.</p>
          ) : (
            <div className="table-wrap">
              <table className="tbl">
                <thead>
                  <tr><th>#</th><th>Severity</th><th>Change</th><th>Clause</th><th>Score</th><th className="num">Impacts</th></tr>
                </thead>
                <tbody>
                  {risks.slice(0, 5).map((r) => (
                    <tr key={r.rank}>
                      <td className="mono muted">{String(r.rank).padStart(2, "0")}</td>
                      <td><RiskBadge severity={r.severity} /></td>
                      <td>{parseExplanation(r.explanation).text}</td>
                      <td className="mono">{shortId(r.trigger_clause)}</td>
                      <td>
                        <span className="score">
                          <span className="mono">{(r.score ?? 0).toFixed(2)}</span>
                          <span className="score-bar"><span style={{ width: `${Math.min(100, (r.score ?? 0) * 100)}%` }} /></span>
                        </span>
                      </td>
                      <td className="mono num">{r.impacted_clauses.length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Risk breakdown</h2>
              <p className="muted">{risks.length} ranked risk{risks.length === 1 ? "" : "s"} in the latest analysis</p>
            </div>
          </div>
          <div className="panel-body">
            {risks.length === 0 ? (
              <p className="panel-empty">No risks yet.</p>
            ) : (
              <>
                <div className="stack-bar" role="img" aria-label="Risks by severity">
                  {counts.filter((c) => c.value > 0).map((c) => (
                    <span key={c.name} style={{ flex: c.value, background: SEV_COLOR[c.name] }} />
                  ))}
                </div>
                <ul className="brk">
                  {SEVERITY_ORDER.map((s) => {
                    const n = counts.find((c) => c.name === s).value;
                    return (
                      <li key={s}>
                        <i style={{ background: SEV_COLOR[s] }} />
                        <span>{s}</span>
                        <b className="mono">{n}</b>
                      </li>
                    );
                  })}
                </ul>
                {meta && (
                  <p className="muted foot">
                    Contradictions found: <span className="mono">{meta.contradictions ?? 0}</span>
                    {meta.contradictions_status === "experimental" && " · experimental, accuracy not yet measured"}
                  </p>
                )}
              </>
            )}
          </div>
        </section>
      </div>

      <div className="grid-2">
        <section className="panel panel-wide light">
          <div className="panel-head">
            <div>
              <h2>Dependency graph</h2>
              <p className="muted"><span className="mono">{latest.name}</span> · arrows point from a clause to the clause it relies on</p>
            </div>
            <Link to={`/graph/${latest.id}`}>Open full graph →</Link>
          </div>
          <div className="panel-body">
            {report ? (
              <>
                <GraphLegend />
                <DependencyGraph report={report} height={340} compact />
              </>
            ) : (
              <Loader text="Loading graph…" />
            )}
          </div>
        </section>

        <div className="stack">
          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Alerts</h2>
                <p className="muted">{unseen.length} unseen</p>
              </div>
              <Link to="/alerts">All alerts →</Link>
            </div>
            <div className="panel-body">
              {unseen.length === 0 ? (
                <p className="panel-empty">Nothing needs your attention.</p>
              ) : (
                <>
                  <p className="mono muted">{unseen[0].contract_key}</p>
                  <p>{unseen[0].message}</p>
                </>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Contracts</h2>
                <p className="muted">{contracts.length} analysis{contracts.length === 1 ? "" : "es"}</p>
              </div>
            </div>
            <ul className="contracts">
              {contracts.slice(0, 5).map((c) => (
                <li key={c.id}>
                  <div>
                    <b>{c.name}</b>
                    <span className="mono muted">{c.versions}</span>
                  </div>
                  <div className="chips">
                    <Link to={`/report/${c.id}`}>Report</Link>
                    <Link to={`/diff/${c.id}`}>Changes</Link>
                    <Link to={`/graph/${c.id}`}>Graph</Link>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
