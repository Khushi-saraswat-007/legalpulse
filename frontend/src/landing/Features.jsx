import { AlertTriangle, ArrowRight, BarChart3, Copy, FileText, Share2, Upload } from "lucide-react";
import Reveal from "../components/Reveal";

const features = [
  { icon: FileText, tone: "indigo", title: "Extract Key Clauses", text: "Automatically identify entities, obligations and key terms." },
  { icon: AlertTriangle, tone: "red", title: "Detect Contradictions", text: "Find conflicting or missing clauses across documents." },
  { icon: Copy, tone: "blue", title: "Compare Versions", text: "See what changed and how it affects your risk." },
  { icon: Share2, tone: "green", title: "Trace Impact", text: "Visualize dependencies and generate an explainable risk report." },
];

const steps = [
  { icon: Upload, title: "1. Upload", text: "Upload your contract (JSON or PDF)." },
  { icon: FileText, title: "2. Analyze", text: "AI extracts clauses and detects contradictions." },
  { icon: Share2, title: "3. Build Graph", text: "Create a dependency graph and trace impact." },
  { icon: BarChart3, title: "4. Get Report", text: "Receive a ranked, explainable risk report." },
];

export default function Features() {
  return (
    <>
      <section className="lp-container lp-features" id="features">
        {features.map((f, i) => (
          <Reveal key={f.title} delay={i * 100} className="lp-feature">
            <span className={`lp-icon tone-${f.tone}`}><f.icon size={22} /></span>
            <div>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </div>
          </Reveal>
        ))}
      </section>

      <section className="lp-container" id="how">
        <Reveal className="lp-band">
          <div className="lp-band-title">
            <span className="lp-eyebrow">How it works</span>
            <h2>From Contract to Clarity</h2>
            <p>A simple pipeline to turn complex contracts into clear, actionable insights.</p>
          </div>
          <div className="lp-steps">
            {steps.map((s, i) => (
              <div className="lp-step" key={s.title}>
                <span className="lp-step-icon"><s.icon size={22} /></span>
                <b>{s.title}</b>
                <small>{s.text}</small>
                {i < steps.length - 1 && <ArrowRight className="lp-step-arrow" size={18} />}
              </div>
            ))}
          </div>
        </Reveal>
      </section>
    </>
  );
}