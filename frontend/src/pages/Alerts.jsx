import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bell, CheckCheck } from "lucide-react";
import { listAlerts, markAlertSeen } from "../api/alerts";
import Loader from "../components/Loader";

const css = `
.al h1 { margin: 0 0 .3rem; }
.al-sub { margin: 0 0 1.4rem; color: #6b7294; }
.al-item { display: flex; align-items: flex-start; gap: .9rem; padding: 1rem 1.1rem; margin-bottom: .7rem; background: #fff; border: 1px solid #e3e6f3; border-left: 4px solid #f08a4b; border-radius: 12px; }
.al-item.seen { opacity: .55; border-left-color: #c9cde6; }
.al-body { flex: 1; min-width: 0; }
.al-body b { display: block; margin-bottom: .2rem; color: #141a3a; }
.al-body span { color: #4a5170; font-size: .92rem; }
.al-btn { display: inline-flex; align-items: center; gap: .4rem; padding: .45rem .8rem; border: 1px solid #e3e6f3; border-radius: 8px; background: #fff; color: #141a3a; font: inherit; font-size: .82rem; font-weight: 600; cursor: pointer; }
.al-btn:hover { border-color: #4350dc; color: #4350dc; }
.al-empty { padding: 2rem; text-align: center; color: #6b7294; background: #fff; border: 1px dashed #e3e6f3; border-radius: 12px; }
`;

export default function Alerts() {
  const [alerts, setAlerts] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    listAlerts()
      .then(setAlerts)
      .catch(() => setError("Could not load alerts. Is the backend running?"));
  }, []);

  const markSeen = async (id) => {
    try {
      await markAlertSeen(id);
      setAlerts((list) => list.map((a) => (a.id === id ? { ...a, seen: true } : a)));
    } catch {
      setError("Could not update the alert.");
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (!alerts) return <Loader text="Loading alerts..." />;

  const unseen = alerts.filter((a) => !a.seen).length;

  return (
    <div className="al">
      <style>{css}</style>
      <h1><Bell size={26} style={{ verticalAlign: "-4px" }} /> Alerts</h1>
      <p className="al-sub">{unseen} unseen &middot; raised when an analysis finds a risk worth reviewing.</p>

      {alerts.length === 0 ? (
        <div className="al-empty">No alerts yet. <Link to="/upload">Upload contract versions</Link> to get started.</div>
      ) : (
        alerts.map((a) => (
          <div key={a.id} className={`al-item ${a.seen ? "seen" : ""}`}>
            <div className="al-body">
              <b>{a.contract_key}</b>
              <span>{a.message}</span>
            </div>
            {!a.seen && (
              <button className="al-btn" onClick={() => markSeen(a.id)}>
                <CheckCheck size={14} /> Mark seen
              </button>
            )}
          </div>
        ))
      )}
    </div>
  );
}