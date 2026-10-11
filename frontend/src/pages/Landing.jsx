import { useAuth } from "../context/AuthContext";
import LandingNav from "../landing/LandingNav";
import Hero from "../landing/Hero";
import Features from "../landing/Features";
import Demo from "../landing/Demo";
import Benefits from "../landing/Benefits";
import Closing from "../landing/Closing";
import "../landing/landing.css";
import "../landing/landing2.css";

export default function Landing() {
  const { user } = useAuth();
  const startTo = user ? "/dashboard" : "/login";
  const sampleTo = user ? "/report/c001" : "/login";

  return (
    <div className="lp">
      <LandingNav startTo={startTo} />
      <Hero startTo={startTo} sampleTo={sampleTo} />
      <Features />
      <Demo />
      <Benefits />
      <Closing startTo={startTo} />
    </div>
  );
}