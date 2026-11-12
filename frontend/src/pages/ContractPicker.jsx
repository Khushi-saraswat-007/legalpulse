import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { listContracts } from "../api/contracts";
import RiskBadge from "../components/RiskBadge";
import Loader from "../components/Loader";

const KINDS = {
  report: { title: "Risk reports", open: "Open report", path: (id) => `/report/${id}` },
  diff: { title: "Changes", open: "Open changes", path: (id) => `/diff/${id}` },
  graph: { title: "Dependency graphs", open: "Open graph", path: (id) => `/graph/${id}` },
};

const fmtDate = (iso) => {
  const d = iso ? new Date(iso) : null;
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "";
};

// "Which contract do you want to look at?"  Lists every analysis, newest first.
export default function ContractPicker({ kind }) {
  const k = KINDS[kind];
  const [contracts, setContracts] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    listContracts().then(setContracts).catch(() => setError("Something went wrong. Please try again."));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!contracts) return <Loader text="Loading your analyses…" />;

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="crumb">Explore analyses <span>/</span> {k.title}</p>
          <h1>{k.title}</h1>
          <p className="muted">Choose which analysed contract to open. The newest analysis is at the top.</p>
        </div>
      </div>

      <div className="grid-2">
        <section className="panel panel-wide light">
          <div className="panel-head">
            <div>
              <h2>Your analyses</h2>
              <p className="muted">{contracts.length} contract{contracts.length === 1 ? "" : "s"} · newest first</p>
            </div>
          </div>
          {contracts.length === 0 ? (
            <p className="panel-empty">Nothing analysed yet. <Link to="/upload">Upload and analyse</Link> two versions of a contract to get started.</p>
          ) : (
            <ul className="pick-list">
              {contracts.map((c, i) => (
                <li className="pick-row" key={c.id}>
                  <div className="pick-main">
                    <span className="pick-name">{c.name}{i === 0 && <span className="tag tag-latest">Latest</span>}</span>
                    <span className="mono muted">{c.versions}</span>
                  </div>
                  <span className="pick-date mono muted">{fmtDate(c.created_at)}</span>
                  <span className="pick-sev">{c.top_severity ? <RiskBadge severity={c.top_severity} /> : null}</span>
                  <Link className="btn btn-primary" to={k.path(c.id)}>{k.open} <ChevronRight size={15} /></Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          <div className="panel-head"><div><h2>How this works</h2></div></div>
          <div className="pick-side">
            <p>Pick any earlier analysis and it opens in full. Inside, a dropdown lets you jump to another contract.</p>
            <p className="muted">Risk reports, Changes and Dependency graphs in the sidebar all work this way.</p>
            <p className="muted">After you press <b>Analyse</b> on the upload page, the report for the contract you just uploaded opens straight away.</p>
          </div>
        </section>
      </div>
    </section>
  );
}
