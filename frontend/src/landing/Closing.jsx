import { Link } from "react-router-dom";
import { ArrowRight, Scale, ShieldCheck } from "lucide-react";
import Reveal from "../components/Reveal";

export default function Closing({ startTo }) {
  return (
    <>
      <section className="lp-container">
        <Reveal className="lp-quote">
          <span className="lp-quote-icon"><ShieldCheck size={44} /></span>
          <blockquote>
            “LegalPulse gives a clear and structured view of contract risks with explanations,
            making legal analysis more accessible and reliable.”
            <cite>— Project Team</cite>
          </blockquote>
        </Reveal>

        <Reveal className="lp-cta">
          <div>
            <h2>Ready to Analyze Your Contracts?</h2>
            <p>Upload a contract and get an AI-powered risk report in minutes.</p>
          </div>
          <Link to={startTo} className="lp-btn lp-btn-primary">
            Get Started <ArrowRight size={16} />
          </Link>
        </Reveal>
      </section>

      <footer className="lp-container lp-footer">
        <div>
          <a href="#home" className="lp-logo"><Scale size={26} strokeWidth={1.8} /> LegalPulse</a>
          <small>Sensing Risk Before It Becomes a Problem.</small>
        </div>
        <nav>
          <a href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#how">How it Works</a>
          <a href="#about">About</a>
        </nav>
      </footer>
    </>
  );
}