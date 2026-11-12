import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, CheckCircle2, Eye, EyeOff, Lock, Scale } from "lucide-react";
import { resetPassword } from "../api/auth";
import "./login.css";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    if (password !== confirm) return setError("The two passwords do not match.");
    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(typeof d === "string" ? d : "Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  const logo = (
    <Link to="/" className="auth-logo" style={{ color: "var(--ink)", marginBottom: "1.5rem" }}>
      <Scale size={26} strokeWidth={1.8} /> LegalPulse
    </Link>
  );

  return (
    <div className="auth" style={{ gridTemplateColumns: "1fr" }}>
      <main className="auth-form-side">
        <div className="auth-form-box">
          {logo}

          {!token ? (
            <>
              <h1>Invalid link</h1>
              <p className="auth-sub">This reset link is incomplete. Please ask for a new one.</p>
              <Link to="/forgot-password" className="auth-back">Request a new link</Link>
            </>
          ) : done ? (
            <>
              <h1><CheckCircle2 size={26} style={{ verticalAlign: "-4px", marginRight: ".4rem", color: "#35b27a" }} />Password updated</h1>
              <p className="auth-sub">You can now log in with your new password.</p>
              <Link to="/login" className="auth-submit" style={{ textDecoration: "none" }}>Log in <ArrowRight size={18} /></Link>
            </>
          ) : (
            <>
              <h1>Choose a new password</h1>
              <p className="auth-sub">Use at least 8 characters.</p>
              <form onSubmit={handleSubmit}>
                <label>
                  New password
                  <span className="auth-field">
                    <Lock size={18} />
                    <input type={show ? "text" : "password"} required placeholder="New password" value={password} onChange={(e) => setPassword(e.target.value)} />
                    <button type="button" className="auth-eye" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"}>
                      {show ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </span>
                </label>
                <label>
                  Confirm password
                  <span className="auth-field">
                    <Lock size={18} />
                    <input type={show ? "text" : "password"} required placeholder="Repeat the password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
                  </span>
                </label>
                <button className="auth-submit" type="submit" disabled={loading}>
                  {loading ? <span className="auth-spinner" /> : <>Update password <ArrowRight size={18} /></>}
                </button>
              </form>
              {error && <p className="auth-note" style={{ color: "#dc2626" }}>{error}</p>}
              <Link to="/login" className="auth-back">← Back to log in</Link>
            </>
          )}
        </div>
      </main>
    </div>
  );
}