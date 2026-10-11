import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Scale } from "lucide-react";

export default function LandingNav({ startTo }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`lp-nav ${scrolled ? "is-scrolled" : ""}`}>
      <div className="lp-container lp-nav-inner">
        <a href="#home" className="lp-logo">
          <Scale size={26} strokeWidth={1.8} /> LegalPulse
        </a>
        <nav className="lp-nav-links">
          <a href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#how">How it Works</a>
          <a href="#about">About</a>
        </nav>
        <Link to={startTo} className="lp-btn lp-btn-primary">
          Get Started <ArrowRight size={16} />
        </Link>
      </div>
    </header>
  );
}