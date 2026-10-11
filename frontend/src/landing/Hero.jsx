import { Link } from "react-router-dom";
import { ArrowRight, FileText, GitFork, BarChart3, Settings, ShieldAlert, Sparkles } from "lucide-react";

const summary = [
  { color: "red", title: "Contradiction Detected", text: "Clauses 4.1 and 7.3" },
  { color: "yellow", title: "Version Change", text: "Clause updated in v2" },
  { color: "red", title: "High Impact Clause", text: "May cause financial risk" },
];

export default function Hero({ startTo, sampleTo }) {
  return (
    <section className="lp-hero lp-container" id="home">
      <div className="lp-hero-text">
        <span className="lp-pill lp-fade" style={{ animationDelay: "0ms" }}>
          <Sparkles size={14} /> AI-Powered Contract Risk Analysis
        </span>
        <h1 className="lp-fade" style={{ animationDelay: "100ms" }}>
          Sensing Risk <span className="lp-accent">Before It Becomes</span> a Problem
        </h1>
        <p className="lp-lead lp-fade" style={{ animationDelay: "200ms" }}>
          LegalPulse helps you analyze contracts, detect risks, compare versions and
          understand real-world impact with explainable AI.
        </p>
        <div className="lp-btn-row lp-fade" style={{ animationDelay: "300ms" }}>
          <Link to={startTo} className="lp-btn lp-btn-primary">
            Get Started <ArrowRight size={16} />
          </Link>
          <Link to={sampleTo} className="lp-btn lp-btn-outline">View Sample Report</Link>
        </div>
      </div>

      <div className="lp-hero-visual lp-fade" style={{ animationDelay: "250ms" }}>
        <div className="lp-mock lp-float">
          <div className="lp-mock-side">
            <FileText size={18} className="active" />
            <GitFork size={18} />
            <BarChart3 size={18} />
            <Settings size={18} />
          </div>
          <div className="lp-mock-doc">
            <strong>Contract.pdf</strong>
            <i className="line" style={{ width: "90%" }} />
            <i className="line" style={{ width: "75%" }} />
            <i className="line hl-red" style={{ width: "55%" }} />
            <i className="line" style={{ width: "85%" }} />
            <i className="line" style={{ width: "70%" }} />
            <i className="line hl-yellow" style={{ width: "60%" }} />
            <i className="line" style={{ width: "80%" }} />
            <i className="line hl-red" style={{ width: "50%", marginLeft: "30%" }} />
          </div>
          <div className="lp-mock-summary">
            <strong>Risk Summary</strong>
            <div className="lp-summary-top">
              <span className="lp-shield"><ShieldAlert size={22} /></span>
              <div>
                <b>3 High Risk Clauses</b>
                <small>View details →</small>
              </div>
            </div>
            {summary.map((s) => (
              <div className="lp-summary-row" key={s.title}>
                <span className={`dot ${s.color}`} />
                <div>
                  <b>{s.title}</b>
                  <small>{s.text}</small>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}