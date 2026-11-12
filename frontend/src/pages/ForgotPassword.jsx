import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, MailCheck, Mail, Scale } from "lucide-react";
import { forgotPassword } from "../api/auth";
import "./login.css";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch {
      setError("Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="auth" style={{ gridTemplateColumns: "1fr" }}>
      <main className="auth-form-side">
        <div className="auth-form-box">
          <Link to="/" className="auth-logo" style={{ color: "var(--ink)", marginBottom: "1.5rem" }}>
            <Scale size={26} strokeWidth={1.8} /> LegalPulse
          </Link>

          {sent ? (
            <>
              <h1><MailCheck size={26} style={{ verticalAlign: "-4px", marginRight: ".4rem", color: "var(--p)" }} />Check your email</h1>
              <p className="auth-sub">
                If <b>{email}</b> is registered, we have sent a link to reset your password. The link works once and expires in 30 minutes.
              </p>
              <Link to="/login" className="auth-back">← Back to log in</Link>
            </>
          ) : (
            <>
              <h1>Forgot your password?</h1>
              <p className="auth-sub">Enter your email and we will send you a link to choose a new one.</p>
              <form onSubmit={handleSubmit}>
                <label>
                  Email
                  <span className="auth-field">
                    <Mail size={18} />
                    <input type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
                  </span>
                </label>
                <button className="auth-submit" type="submit" disabled={loading}>
                  {loading ? <span className="auth-spinner" /> : <>Send reset link <ArrowRight size={18} /></>}
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