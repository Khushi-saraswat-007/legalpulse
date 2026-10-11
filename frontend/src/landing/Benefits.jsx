import { Building2, Briefcase, Clock, Database, GraduationCap, ShieldAlert, TrendingUp } from "lucide-react";
import Reveal from "../components/Reveal";

const why = [
  { icon: Clock, tone: "indigo", title: "Faster Review", text: "Analyze long contracts in minutes." },
  { icon: ShieldAlert, tone: "red", title: "Early Risk Detection", text: "Catch issues before they become problems." },
  { icon: TrendingUp, tone: "blue", title: "Explainable Insights", text: "Understand why a clause is flagged." },
  { icon: Database, tone: "green", title: "Works with Your Data", text: "Supports JSON contracts and custom schemas." },
];

const who = [
  { icon: GraduationCap, title: "Students & Researchers", text: "Understand complex contracts and explore legal reasoning." },
  { icon: Building2, title: "Legal Teams", text: "Review contracts faster and reduce compliance risk." },
  { icon: Briefcase, title: "Businesses", text: "Analyze vendor agreements, partnerships and policies." },
];

export default function Benefits() {
  return (
    <>
      <section className="lp-container lp-why">
        <Reveal>
          <h2>Why LegalPulse</h2>
          <p className="lp-sub">Save time, reduce legal risk and get clear insights.</p>
        </Reveal>
        <div className="lp-card-row four">
          {why.map((w, i) => (
            <Reveal key={w.title} delay={i * 100} className={`lp-why-card tone-bg-${w.tone}`}>
              <span className={`lp-icon-plain tone-${w.tone}`}><w.icon size={26} /></span>
              <div>
                <h3>{w.title}</h3>
                <p>{w.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="lp-who" id="about">
        <div className="lp-container">
          <Reveal>
            <h2>Who Can Use It?</h2>
            <p className="lp-sub">Useful for students, researchers and legal teams working with contracts.</p>
          </Reveal>
          <div className="lp-card-row three">
            {who.map((w, i) => (
              <Reveal key={w.title} delay={i * 120} className="lp-who-card">
                <span className="lp-icon tone-indigo"><w.icon size={22} /></span>
                <div>
                  <h3>{w.title}</h3>
                  <p>{w.text}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}