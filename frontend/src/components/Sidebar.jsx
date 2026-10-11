import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { FileText, GitCompare, LayoutDashboard, LogOut, Network, Scale, Upload } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { listContracts } from "../api/contracts";

const css = `
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap");

body:has(.sidebar) { background: #f7f8ff; }

.shell { display: grid; grid-template-columns: 260px minmax(0, 1fr); min-height: 100vh; }
.shell .page { width: 100%; max-width: 1160px; margin: 0 auto; padding: 2rem 2rem 4rem; }

.sidebar { position: sticky; top: 0; height: 100vh; display: flex; flex-direction: column; padding: 1.4rem 1rem; background: #fff; border-right: 1px solid #e3e6f3; font-family: "Plus Jakarta Sans", system-ui, "Segoe UI", sans-serif; }
.sb-logo { display: flex; align-items: center; gap: .55rem; padding: 0 .6rem 1.4rem; font-size: 1.3rem; font-weight: 800; letter-spacing: -0.02em; color: #141a3a; text-decoration: none; }
.sb-logo svg { color: #4350dc; }
.sb-label { margin: 1.2rem .6rem .5rem; font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #9aa0c0; }
.sb-nav { display: flex; flex-direction: column; gap: .25rem; }
.sb-nav a { display: flex; align-items: center; gap: .75rem; padding: .7rem .8rem; border-radius: 10px; color: #4a5170; text-decoration: none; font-size: .92rem; font-weight: 600; transition: background .2s, color .2s, transform .2s; }
.sb-nav a:hover { background: #f1f2ff; color: #4350dc; transform: translateX(3px); }
.sb-nav a.active { background: #4350dc; color: #fff; box-shadow: 0 6px 16px rgba(67, 80, 220, .25); }

.sb-user { margin-top: auto; padding: .9rem; border: 1px solid #e3e6f3; border-radius: 12px; background: #f7f8ff; }
.sb-user-row { display: flex; align-items: center; gap: .7rem; min-width: 0; }
.sb-avatar { flex: none; width: 38px; height: 38px; border-radius: 50%; background: #4350dc; color: #fff; display: grid; place-items: center; font-weight: 700; }
.sb-email { min-width: 0; font-size: .82rem; font-weight: 600; color: #141a3a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sb-logout { width: 100%; margin-top: .8rem; display: flex; align-items: center; justify-content: center; gap: .45rem; padding: .55rem; border: 1px solid #e3e6f3; border-radius: 8px; background: #fff; color: #141a3a; font: inherit; font-size: .85rem; font-weight: 600; cursor: pointer; transition: border-color .2s, color .2s; }
.sb-logout:hover { border-color: #4350dc; color: #4350dc; }

@media (max-width: 860px) {
  .shell { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; flex-direction: row; flex-wrap: wrap; align-items: center; gap: .5rem 1rem; padding: .8rem 1rem; border-right: 0; border-bottom: 1px solid #e3e6f3; }
  .sb-logo { padding: 0; }
  .sb-label { display: none; }
  .sb-nav { flex-direction: row; flex-wrap: wrap; }
  .sb-user { margin: 0 0 0 auto; padding: .4rem; border: 0; background: none; }
  .sb-email { display: none; }
  .sb-logout { margin: 0; width: auto; padding: .5rem .8rem; }
  .shell .page { padding: 1.5rem 1rem 3rem; }
}
`;

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [contractId, setContractId] = useState(null);

  useEffect(() => {
    listContracts()
      .then((list) => list.length > 0 && setContractId(list[0].id))
      .catch(() => {});
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const initial = user?.email ? user.email[0].toUpperCase() : "U";

  return (
    <aside className="sidebar">
      <style>{css}</style>
      <NavLink to="/dashboard" className="sb-logo">
        <Scale size={26} strokeWidth={1.8} /> LegalPulse
      </NavLink>

      <span className="sb-label">Menu</span>
      <nav className="sb-nav">
        <NavLink to="/dashboard"><LayoutDashboard size={18} /> Dashboard</NavLink>
        <NavLink to="/upload"><Upload size={18} /> Upload</NavLink>
      </nav>

      {contractId && (
        <>
          <span className="sb-label">Latest contract</span>
          <nav className="sb-nav">
            <NavLink to={`/report/${contractId}`}><FileText size={18} /> Risk report</NavLink>
            <NavLink to={`/diff/${contractId}`}><GitCompare size={18} /> Changes</NavLink>
            <NavLink to={`/graph/${contractId}`}><Network size={18} /> Dependency graph</NavLink>
          </nav>
        </>
      )}

      <div className="sb-user">
        <div className="sb-user-row">
          <span className="sb-avatar">{initial}</span>
          <span className="sb-email">{user?.email}</span>
        </div>
        <button className="sb-logout" onClick={handleLogout}>
          <LogOut size={16} /> Log out
        </button>
      </div>
    </aside>
  );
}