import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Sidebar from "./components/Sidebar";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import ReportViewer from "./pages/ReportViewer";
import DiffView from "./pages/DiffView";
import GraphView from "./pages/GraphView";
import Alerts from "./pages/Alerts";
import ContractPicker from "./pages/ContractPicker";

function Protected({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { user } = useAuth();
  const { pathname } = useLocation();

  // The landing page and login page are public and have their own layouts
  if (pathname === "/") return <Landing />;
  if (pathname === "/login") return <Login />;

  return (
    <div className={user ? "shell" : ""}>
      {user && <Sidebar />}
      <main className="page">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/upload" element={<Protected><Upload /></Protected>} />
          <Route path="/reports" element={<Protected><ContractPicker kind="report" /></Protected>} />
          <Route path="/changes" element={<Protected><ContractPicker kind="diff" /></Protected>} />
          <Route path="/graphs" element={<Protected><ContractPicker kind="graph" /></Protected>} />
          <Route path="/report/:id" element={<Protected><ReportViewer /></Protected>} />
          <Route path="/diff/:id" element={<Protected><DiffView /></Protected>} />
          <Route path="/graph/:id" element={<Protected><GraphView /></Protected>} />
          <Route path="/alerts" element={<Protected><Alerts /></Protected>} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}