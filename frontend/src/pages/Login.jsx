import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowRight, Eye, EyeOff, GitFork, Lock, Mail, Scale, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import "./login.css";

const cards = [
  { icon: AlertTriangle, tone: "red", title: "Contradiction detected", text: "Clauses 4.1 and 7.3 conflict" },
  { icon: GitFork, tone: "yellow", title: "Version change", text: "Clause 12 updated in v2" },
  { icon: ShieldCheck, tone: "green", title: "Impact traced", text: "3 clauses affected, ranked by risk" },
];

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    // TODO: call POST /auth/login when the backend implements it
    setTimeout(() => {
      login(email);
      navigate("/dashboard");
    }, 700);
  };

  return (
    <div className="auth">
      <aside className="auth-brand">
        <span className="auth-orb orb-a" />
        <span className="auth-orb orb-b" />
        <Link to="/" className="auth-logo"><Scale size={28} strokeWidth={1.8} /> LegalPulse</Link>

        <div className="auth-brand-body">
          <h2>Sensing risk before it becomes a problem.</h2>
          <p>Compare contract versions, trace the impact of every change and get a ranked, explainable risk report.</p>
          <div className="auth-cards">
            {cards.map((c, i) => (
              <div className="auth-card" key={c.title} style={{ animationDelay: `${i * 150 + 200}ms` }}>
                <span className={`auth-card-icon tone-${c.tone}`}><c.icon size={18} /></span>
                <div>
                  <b>{c.title}</b>
                  <small>{c.text}</small>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <main className="auth-form-side">
        <div className="auth-form-box">
          <Link to="/" className="auth-logo auth-logo-mobile"><Scale size={26} strokeWidth={1.8} /> LegalPulse</Link>
          <h1>Welcome back</h1>
          <p className="auth-sub">Log in to analyze your contracts.</p>

          <form onSubmit={handleSubmit}>
            <label>
              Email
              <span className="auth-field">
                <Mail size={18} />
                <input type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
              </span>
            </label>
            <label>
              Password
              <span className="auth-field">
                <Lock size={18} />
                <input type={show ? "text" : "password"} required placeholder="Enter your password" value={password} onChange={(e) => setPassword(e.target.value)} />
                <button type="button" className="auth-eye" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"}>
                  {show ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>
            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? <span className="auth-spinner" /> : <>Log in <ArrowRight size={18} /></>}
            </button>
          </form>

          <p className="auth-note">Demo mode: any email and password will work for now.</p>
          <Link to="/" className="auth-back">← Back to home</Link>
        </div>
      </main>
    </div>
  );
}