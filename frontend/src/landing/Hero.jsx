import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

// A bar standing in for a line of contract text. kind: "" | "r" (changed) | "y" (reworded)
const Bar = ({ w, kind = "" }) => <i className={`lp-bar ${kind}`} style={{ width: `${w}%` }} />;

function Sheet({ title, bars, tilt }) {
  return (
    <div className="lp-sheet" style={{ transform: `rotate(${tilt}deg)` }}>
      <span className="lp-sheet-title">{title}</span>
      {bars.map(([w, k], i) => <Bar key={i} w={w} kind={k} />)}
    </div>
  );
}

const V1 = [[92], [78], [55], [88], [70], [85], [62], [90], [48]];
const V2 = [[92], [78], [55, "y"], [88], [70, "r"], [85], [62, "y"], [90], [48]];

export default function Hero({ startTo, sampleTo }) {
  return (
    <section className="lp-hero" id="home">
      <div className="lp-container lp-hero-inner">
        <span className="lp-pill lp-fade" style={{ animationDelay: "0ms" }}>Contract risk analysis</span>
        <h1 className="lp-fade" style={{ animationDelay: "100ms" }}>
          Sensing risk before it becomes a <span className="lp-accent">problem.</span>
        </h1>
        <p className="lp-lead lp-fade" style={{ animationDelay: "200ms" }}>
          Compare two versions of a contract. See what changed, what depends on it, and what to read first.
        </p>
        <div className="lp-btn-row lp-fade" style={{ animationDelay: "300ms" }}>
          <Link to={startTo} className="lp-btn lp-btn-primary">Get started <ArrowRight size={16} /></Link>
          <Link to={sampleTo} className="lp-btn lp-btn-outline">View sample report</Link>
        </div>

        <div className="lp-hero-visual lp-fade" style={{ animationDelay: "450ms" }} aria-hidden="true">
          <Sheet title="Agreement · v1" bars={V1} tilt={-3} />
          <svg className="lp-flow" width="46" height="24" viewBox="0 0 46 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12h38M31 3l9 9-9 9" />
          </svg>
          <div className="lp-sheet-wrap">
            <Sheet title="Agreement · v2" bars={V2} tilt={2} />
            <div className="lp-chip">
              <b>HIGH RISK</b>
              <span>Clause 7 was removed</span>
              <small>3 clauses relied on it</small>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
