import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/contracts";
import { mockClauses } from "../api/mockClauses";
import Loader from "../components/Loader";
import ContractSwitcher from "../components/ContractSwitcher";
import { cleanName, shortId } from "../lib/format";
import { wordDiff } from "../lib/wordDiff";

// Old and new wording side by side, with the words that changed highlighted.
function TextDiff({ oldText, newText }) {
  const { left, right } = wordDiff(oldText, newText);
  const render = (tokens, cls) => tokens.map((x, i) => (x.changed ? <mark key={i} className={cls}>{x.t}</mark> : <span key={i}>{x.t}</span>));
  return (
    <>
      <div className="diff-cols"><span>Previous version</span><span>New version</span></div>
      <div className="diff-pair">
        <p className="diff-col">{render(left, "del")}</p>
        <p className="diff-col">{render(right, "ins")}</p>
      </div>
    </>
  );
}

export default function DiffView() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getReport(id).then(setReport).catch(() => setError("Could not load the changes."));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!report) return <Loader text="Loading changes…" />;

  const changes = report.changes.filter((c) => c.change_type !== "unchanged");
  // clause text comes with the report (meta.clause_text); older saved reports fall back to the demo text
  const textOf = (clauseId) => (clauseId ? report.meta?.clause_text?.[clauseId] ?? mockClauses[clauseId]?.text : undefined);

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="crumb">Changes <span>/</span> <b className="mono">{cleanName(report.contract_id)}</b></p>
          <h1>What changed</h1>
          <p className="muted">{changes.length} clause change{changes.length === 1 ? "" : "s"} between versions</p>
        </div>
        <div className="actions">
          <ContractSwitcher current={id} to={(x) => `/diff/${x}`} />
          <Link className="btn" to={`/report/${id}`}>Back to report</Link>
        </div>
      </div>

      {changes.length === 0 && <div className="panel"><p className="panel-empty">These versions have no differences.</p></div>}

      {changes.map((c, i) => {
        const oldId = c.old_clause_id ?? c.old_clause_ids?.[0];
        const newId = c.new_clause_id ?? c.new_clause_ids?.[0];
        const oldText = textOf(oldId);
        const newText = textOf(newId);
        return (
          <article key={i} className="change">
            <header className="change-head">
              <span className={`tag tag-${c.change_type}`}>{c.change_type}</span>
              <span className="mono muted">{oldId ? shortId(oldId) : "—"} → {newId ? shortId(newId) : "—"}</span>
            </header>
            <p>{c.summary}</p>
            {c.semantic?.reasons?.length > 0 && (
              <p className="reasons">{c.semantic.reasons.map((r) => <span className="chip" key={r}>{r}</span>)}{c.match_basis === "structure" && <span className="chip">matched by position and heading</span>}</p>
            )}
            {oldText && newText && oldText !== newText && <TextDiff oldText={oldText} newText={newText} />}
            {oldText && !newText && <blockquote className="clause-text removed">{oldText}</blockquote>}
            {!oldText && newText && <blockquote className="clause-text added">{newText}</blockquote>}
          </article>
        );
      })}
    </section>
  );
}
