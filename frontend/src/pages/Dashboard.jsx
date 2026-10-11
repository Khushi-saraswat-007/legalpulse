import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { ArrowRight, FileText, GitCompare, Network, ShieldAlert, Upload } from "lucide-react";
import { getReport, listContracts } from "../api/contracts";
import { useAuth } from "../context/AuthContext";
import Reveal from "../components/Reveal";
import RiskBadge from "../components/RiskBadge";
import Loader from "../components/Loader";

const css = `
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

body:has(.dash) { background: #f7f8ff; }

.dash { font-family: "Plus Jakarta Sans", system-ui, "Segoe UI", sans-serif; color: #4a5170; }
.dash h1, .dash h2, .dash p { margin: 0; max-width: none; }
.page:has(.dash) { max-width: 1160px; }

/* Scroll reveal (same effect as the landing page) */
.dash .lp-reveal { opacity: 0; transform: translateY(24px); transition: opacity .6s ease, transform .6s ease; }
.dash .lp-reveal.is-in { opacity: 1; transform: none; }

.dash-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.6rem; }
.dash-head h1 { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; color: #141a3a; }
.dash-name { color: #4350dc; text-transform: capitalize; }
.dash-head p { margin-top: .3rem; }
.dash-btn { display: inline-flex; align-items: center; gap: .5rem; padding: .75rem 1.2rem; border-radius: 10px; background: #4350dc; color: #fff; font-weight: 600; font-size: .92rem; text-decoration: none; box-shadow: 0 6px 16px rgba(67, 80, 220, .28); transition: transform .2s, background .2s; }
.dash-btn:hover { background: #3640c0; transform: translateY(-2px); }

.dash-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.2rem; }
.dash-stat { display: flex; align-items: center; gap: .9rem; padding: 1.1rem 1.2rem; background: #fff; border: 1px solid #e3e6f3; border-radius: 14px; transition: transform .25s, box-shadow .25s; }
.dash-stat:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(20, 26, 58, .08); }
.dash-stat b { display: block; font-size: 1.7rem; line-height: 1.1; color: #141a3a; font-weight: 800; }
.dash-stat small { font-size: .82rem; }
.dash-icon { flex: none; width: 46px; height: 46px; border-radius: 12px; display: grid; place-items: center; }
.dash .tone-indigo { background: #eef0ff; color: #4350dc; }
.dash .tone-red { background: #ffe9ec; color: #ef5b6b; }
.dash .tone-blue { background: #e4f0ff; color: #2f7be0; }
.dash .tone-green { background: #e1f6ec; color: #35b27a; }

.dash-grid { display: grid; grid-template-columns: 1fr 1.6fr; gap: 1.2rem; margin-bottom: 1.2rem; }
.dash-panel { padding: 1.3rem 1.4rem; background: #fff; border: 1px solid #e3e6f3; border-radius: 14px; }
.dash-panel h2 { font-size: 1.05rem; font-weight: 700; color: #141a3a; margin-bottom: 1rem; }
.dash-panel-head { display: flex; justify-content: space-between; align-items: baseline; }
.dash-panel-head a { display: inline-flex; align-items: center; gap: .3rem; font-size: .85rem; font-weight: 600; color: #4350dc; text-decoration: none; }
.dash-empty { color: #8a91b4; }

.dash-chart { position: relative; height: 190px; }
.dash-chart-total { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none; }
.dash-chart-total b { font-size: 1.6rem; color: #141a3a; line-height: 1; }
.dash-chart-total small { font-size: .78rem; }
.dash-legend { list-style: none; margin: .8rem 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: .5rem 1.2rem; }
.dash-legend li { display: flex; align-items: center; gap: .4rem; font-size: .85rem; text-transform: capitalize; }
.dash-legend i { width: 10px; height: 10px; border-radius: 50%; }
.dash-legend b { color: #141a3a; }

.dash-risks { list-style: none; margin: 0; padding: 0; }
.dash-risk { display: flex; gap: 1rem; padding: .95rem 0 .95rem .9rem; border-left: 4px solid #e3e6f3; border-bottom: 1px solid #f0f1f8; }
.dash-risk:last-child { border-bottom: 0; }
.dash-risk.risk-low { border-left-color: #35b27a; }
.dash-risk.risk-medium { border-left-color: #f6c445; }
.dash-risk.risk-high { border-left-color: #f08a4b; }
.dash-risk.risk-critical { border-left-color: #d9374f; }
.dash-rank { font-size: 1.5rem; font-weight: 800; color: #b8bfd9; min-width: 1.5rem; }
.dash-risk p { margin: .35rem 0 .2rem; font-size: .92rem; color: #141a3a; line-height: 1.5; }
.dash-risk small { font-size: .8rem; }

.dash-contracts ul { list-style: none; margin: 0; padding: 0; }
.dash-contracts li { display: flex; align-items: center; gap: 1rem; padding: .9rem 0; border-top: 1px solid #f0f1f8; flex-wrap: wrap; }
.dash-contract-name { flex: 1; min-width: 160px; }
.dash-contract-name b { display: block; color: #141a3a; }
.dash-contract-name small { font-size: .82rem; }
.dash-links { display: flex; gap: .5rem; }
.dash-links a { padding: .4rem .9rem; border: 1px solid #e3e6f3; border-radius: 8px; font-size: .85rem; font-weight: 600; color: #4350dc; text-decoration: none; transition: background .2s, border-color .2s; }
.dash-links a:hover { background: #eef0ff; border-color: #4350dc; }

@media (max-width: 960px) {
  .dash-stats { grid-template-columns: 1fr 1fr; }
  .dash-grid { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .dash-stats { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .dash .lp-reveal { opacity: 1; transform: none; transition: none; }
}
`;

const COLORS = { low: "#35b27a", medium: "#f6c445", high: "#f08a4b", critical: "#d9374f" };

export default function Dashboard() {
  const { user } = useAuth();
  const [contracts, setContracts] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const list = await listContracts();
        setContracts(list);
        if (list.length > 0) setReport(await getReport(list[0].id));
      } catch {
        setError("Could not load your dashboard. Is the backend running?");
      }
    }
    load();
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!contracts) return <Loader text="Loading your dashboard…" />;

  const risks = report ? [...report.risks].sort((a, b) => a.rank - b.rank) : [];
  const highCount = risks.filter((r) => r.severity === "high" || r.severity === "critical").length;
  const changeCount = report ? report.changes.filter((c) => c.change_type !== "unchanged").length : 0;
  const clauseCount = report ? report.graph.nodes.length : 0;

  const breakdown = ["critical", "high", "medium", "low"]
    .map((s) => ({ name: s, value: risks.filter((r) => r.severity === s).length }))
    .filter((d) => d.value > 0);

  const name = user?.email ? user.email.split("@")[0].replace(/[._-]+/g, " ") : "there";

  const stats = [
    { icon: FileText, tone: "indigo", label: "Contracts analyzed", value: contracts.length },
    { icon: ShieldAlert, tone: "red", label: "High-risk issues", value: highCount },
    { icon: GitCompare, tone: "blue", label: "Changes detected", value: changeCount },
    { icon: Network, tone: "green", label: "Clauses mapped", value: clauseCount },
  ];

  return (
    <div className="dash">
      <style>{css}</style>
      <Reveal className="dash-head">
        <div>
          <h1>Welcome back, <span className="dash-name">{name}</span></h1>
          <p>Here is what is happening across your contracts.</p>
        </div>
        <Link to="/upload" className="dash-btn"><Upload size={16} /> Upload contract versions</Link>
      </Reveal>

      <div className="dash-stats">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={i * 90} className="dash-stat">
            <span className={`dash-icon tone-${s.tone}`}><s.icon size={22} /></span>
            <div>
              <b>{s.value}</b>
              <small>{s.label}</small>
            </div>
          </Reveal>
        ))}
      </div>

      <div className="dash-grid">
        <Reveal delay={100} className="dash-panel">
          <h2>Risk breakdown</h2>
          {breakdown.length === 0 ? (
            <p className="dash-empty">No risks found yet.</p>
          ) : (
            <>
              <div className="dash-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={breakdown} dataKey="value" nameKey="name" innerRadius={55} outerRadius={80} paddingAngle={3} stroke="none">
                      {breakdown.map((d) => <Cell key={d.name} fill={COLORS[d.name]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="dash-chart-total"><b>{risks.length}</b><small>risks</small></div>
              </div>
              <ul className="dash-legend">
                {breakdown.map((d) => (
                  <li key={d.name}><i style={{ background: COLORS[d.name] }} />{d.name}<b>{d.value}</b></li>
                ))}
              </ul>
            </>
          )}
        </Reveal>

        <Reveal delay={200} className="dash-panel">
          <div className="dash-panel-head">
            <h2>Top risks</h2>
            {report && <Link to={`/report/${report.contract_id}`}>View full report <ArrowRight size={14} /></Link>}
          </div>
          {risks.length === 0 ? (
            <p className="dash-empty">Upload a contract to see its risks here.</p>
          ) : (
            <ul className="dash-risks">
              {risks.slice(0, 3).map((r) => (
                <li key={r.rank} className={`dash-risk risk-${r.severity}`}>
                  <span className="dash-rank">{r.rank}</span>
                  <div>
                    <RiskBadge severity={r.severity} />
                    <p>{r.explanation}</p>
                    <small>Triggered by clause {r.trigger_clause}</small>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Reveal>
      </div>

      <Reveal delay={100} className="dash-panel dash-contracts">
        <h2>Your contracts</h2>
        {contracts.length === 0 ? (
          <p className="dash-empty">No contracts yet. Upload an old and a new version to get started.</p>
        ) : (
          <ul>
            {contracts.map((c) => (
              <li key={c.id}>
                <span className="dash-icon tone-indigo"><FileText size={20} /></span>
                <div className="dash-contract-name">
                  <b>{c.name}</b>
                  <small>{c.versions}</small>
                </div>
                <div className="dash-links">
                  <Link to={`/report/${c.id}`}>Report</Link>
                  <Link to={`/diff/${c.id}`}>Changes</Link>
                  <Link to={`/graph/${c.id}`}>Graph</Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Reveal>
    </div>
  );
}