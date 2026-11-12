import { Link } from "react-router-dom";
import { ArrowRight, Scale } from "lucide-react";
import Reveal from "../components/Reveal";

export default function Closing({ startTo }) {
  return (
    <>
      <section className="lp-cta">
        <div className="lp-container">
          <Reveal>
            <h2>Upload two versions. See what changed.</h2>
            <p>Create an account and analyse your first contract in a minute.</p>
            <Link to={startTo} className="lp-btn lp-btn-primary">Get started <ArrowRight size={16} /></Link>
          </Reveal>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-container lp-footer-inner">
          <a href="#home" className="lp-logo"><Scale size={22} strokeWidth={1.8} /> LegalPulse</a>
          <span className="lp-foot-note">Contract risk analysis · compare versions, trace impact, rank risk</span>
          <nav>
            <a href="#how">How it works</a>
            <a href="#faq">FAQ</a>
            <Link to={startTo}>Log in</Link>
          </nav>
        </div>
      </footer>
    </>
  );
}
