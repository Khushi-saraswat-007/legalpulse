import { useAuth } from "../context/AuthContext";
import LandingNav from "../landing/LandingNav";
import Hero from "../landing/Hero";
import { Problem, How, Band, Who } from "../landing/Story";
import Features from "../landing/Features";
import Faq from "../landing/Faq";
import Closing from "../landing/Closing";
import "../landing/landing.css";

export default function Landing() {
  const { user } = useAuth();
  const startTo = user ? "/dashboard" : "/login";
  const sampleTo = user ? "/dashboard" : "/login";
  return (
    <div className="lp">
      <LandingNav startTo={startTo} loggedIn={!!user} />
      <Hero startTo={startTo} sampleTo={sampleTo} />
      <Problem />
      <How />
      <Features />
      <Band />
      <Who />
      <Faq />
      <Closing startTo={startTo} />
    </div>
  );
}
