import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactDiffViewer from "react-diff-viewer-continued";
import { getReport } from "../api/contracts";
import { mockClauses } from "../api/mockClauses";
import Loader from "../components/Loader";

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

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>What changed</h1>
          <p className="muted">{changes.length} clause change{changes.length === 1 ? "" : "s"} between versions</p>
        </div>
        <Link className="btn" to={`/report/${id}`}>Back to report</Link>
      </div>

      {changes.length === 0 && <p className="muted">These versions have no differences.</p>}

      {changes.map((c, i) => {
        const oldC = mockClauses[c.old_clause_id];
        const newC = mockClauses[c.new_clause_id];
        return (
          <article key={i} className="change">
            <h2>
              {c.change_type}
              <span className="muted" style={{ textTransform: "none" }}> · {c.old_clause_id || "—"} → {c.new_clause_id || "—"}</span>
            </h2>
            <p>{c.summary}</p>
            {oldC && newC && (
                            <>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", margin: "1rem 0 .4rem", fontSize: ".85rem", fontWeight: 600 }}>
                  <span>Previous version</span>
                  <span>New version</span>
                </div>
                <ReactDiffViewer
                  oldValue={oldC.text}
                  newValue={newC.text}
                  splitView
                  hideLineNumbers
                  styles={{ contentText: { fontSize: "14px", lineHeight: "1.7" } }}
                />
              </>
            )}
          </article>
        );
      })}
    </section>
  );
}
