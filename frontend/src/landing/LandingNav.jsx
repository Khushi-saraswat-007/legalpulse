import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Scale } from "lucide-react";

export default function LandingNav({ startTo, loggedIn }) {
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
          <Scale size={24} strokeWidth={1.8} /> LegalPulse
        </a>
        <nav className="lp-nav-links">
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#faq">FAQ</a>
          <Link to={startTo} className="lp-nav-login">{loggedIn ? "Dashboard" : "Log in"}</Link>
        </nav>
      </div>
    </header>
  );
}
