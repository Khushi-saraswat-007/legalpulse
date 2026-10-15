import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Bell, FileText, GitCompare, LayoutDashboard, LogOut, Network, Upload } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { listAlerts } from "../api/alerts";

// A NavLink that also counts as active on the detail pages of its section (e.g. /report/12 for "Risk reports")
function Item({ to, also = [], icon: Icon, children, badge }) {
  const { pathname } = useLocation();
  const inSection = also.some((p) => pathname.startsWith(p));
  return (
    <NavLink to={to} className={({ isActive }) => (isActive || inSection ? "active" : "")}>
      <Icon size={16} /> <span>{children}</span>
      {badge > 0 && <span className="sb-badge">{badge}</span>}
    </NavLink>
  );
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [unseen, setUnseen] = useState(0);

  // keep the alert badge fresh after an upload or after "Mark seen"
  useEffect(() => {
    listAlerts()
      .then((list) => setUnseen(list.filter((a) => !a.seen).length))
      .catch(() => {});
  }, [pathname]);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const initial = user?.email ? user.email[0].toUpperCase() : "U";

  return (
    <aside className="sidebar">
      <NavLink to="/dashboard" className="sb-logo">
        <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
          <rect width="26" height="26" rx="6" fill="#FFFFFF" />
          <path d="M4 14h5l2-6 3 11 2-5h6" fill="none" stroke="#2745D8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        LegalPulse
      </NavLink>

      <span className="sb-label">Workspace</span>
      <nav className="sb-nav">
        <Item to="/dashboard" icon={LayoutDashboard}>Dashboard</Item>
        <Item to="/upload" icon={Upload}>Upload and analyse</Item>
        <Item to="/alerts" icon={Bell} badge={unseen}>Alerts</Item>
      </nav>

      <span className="sb-label">Explore analyses</span>
      <nav className="sb-nav">
        <Item to="/reports" also={["/report/"]} icon={FileText}>Risk reports</Item>
        <Item to="/changes" also={["/diff/"]} icon={GitCompare}>Changes</Item>
        <Item to="/graphs" also={["/graph/"]} icon={Network}>Dependency graphs</Item>
      </nav>

      <div className="sb-user">
        <div className="sb-user-row">
          <span className="sb-avatar">{initial}</span>
          <span className="sb-email">{user?.email}</span>
        </div>
        <button className="sb-logout" onClick={handleLogout}>
          <LogOut size={15} /> Log out
        </button>
      </div>
    </aside>
  );
}
