import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Check } from "lucide-react";
import { listAlerts, markAlertSeen } from "../api/alerts";
import Loader from "../components/Loader";

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
  if (!alerts) return <Loader text="Loading alerts…" />;

  const unseen = alerts.filter((a) => !a.seen).length;

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="crumb">Alerts</p>
          <h1>Alerts</h1>
          <p className="muted">{unseen} unseen · raised when an analysis finds a risk worth reviewing.</p>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="panel"><p className="panel-empty">No alerts yet. <Link to="/upload">Upload contract versions</Link> to get started.</p></div>
      ) : (
        <ul className="alert-list">
          {alerts.map((a) => (
            <li key={a.id} className={a.seen ? "seen" : ""}>
              <span className={`alert-dot ${a.seen ? "" : "on"}`} aria-hidden="true" />
              <div className="alert-body">
                <b className="mono">{a.contract_key}</b>
                <span>{a.message}</span>
              </div>
              {a.seen ? (
                <span className="muted">Seen</span>
              ) : (
                <button className="btn" onClick={() => markSeen(a.id)}><Check size={14} /> Mark seen</button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
