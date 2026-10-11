import { useState } from "react";
import { AlertTriangle, BarChart3, Copy, FileText, Share2 } from "lucide-react";
import Reveal from "../components/Reveal";

const menu = [
  { icon: FileText, label: "Clause Extraction", caption: "Finds the key clauses and obligations in the contract." },
  { icon: AlertTriangle, label: "Contradiction Detection", caption: "Flags clauses that conflict with each other." },
  { icon: Copy, label: "Version Comparison", caption: "Shows what changed between two versions." },
  { icon: Share2, label: "Dependency Graph", caption: "Links clauses that rely on each other." },
  { icon: BarChart3, label: "Risk Report", caption: "Ranks every risk and explains why it matters." },
];

const tabs = ["Extracted Clauses", "Entities", "Risks"];

const clauses = [
  { name: "Clause 4.1 – Term", level: "High Risk", tone: "red", text: "This agreement shall remain in force for a period of 3 years unless terminated earlier ..." },
  { name: "Clause 7.3 – Termination", level: "Medium Risk", tone: "yellow", text: "Either party may terminate this agreement with 30 days written notice ..." },
  { name: "Clause 12.1 – Liability", level: "Low Risk", tone: "green", text: "The total liability shall not exceed the amount paid in the preceding 12 months ..." },
];

const entities = [
  { name: "Party A", level: "Organization", tone: "blue", text: "Service provider named in the agreement." },
  { name: "Party B", level: "Organization", tone: "blue", text: "Client receiving the services." },
  { name: "Notice period", level: "Duration", tone: "yellow", text: "30 days written notice for termination." },
];

const risks = [
  { name: "Term vs Termination", level: "High Risk", tone: "red", text: "Clause 4.1 (3 years) conflicts with the 30 day exit in Clause 7.3." },
  { name: "Liability cap", level: "Low Risk", tone: "green", text: "Liability is capped at 12 months of payments." },
  { name: "Version change", level: "Medium Risk", tone: "yellow", text: "Clause 7.3 was updated in the newer version." },
];

const data = { "Extracted Clauses": clauses, Entities: entities, Risks: risks };

export default function Demo() {
  const [active, setActive] = useState(0);
  const [tab, setTab] = useState(tabs[0]);

  return (
    <section className="lp-container lp-demo">
      <Reveal>
        <h2>See It In Action</h2>
        <p className="lp-sub">A quick look at how LegalPulse analyzes a contract and highlights potential risks.</p>
      </Reveal>

      <div className="lp-demo-grid">
        <Reveal className="lp-demo-menu">
          {menu.map((m, i) => (
            <button key={m.label} className={i === active ? "is-active" : ""} onClick={() => setActive(i)}>
              <m.icon size={18} /> {m.label}
            </button>
          ))}
        </Reveal>

        <Reveal delay={120} className="lp-demo-doc">
          <strong>Service Agreement</strong>
          <i className="line" style={{ width: "92%" }} />
          <i className="line" style={{ width: "80%" }} />
          <i className="line hl-red" style={{ width: "55%", marginLeft: "20%" }} />
          <i className="line" style={{ width: "88%" }} />
          <i className="line" style={{ width: "70%" }} />
          <i className="line hl-yellow" style={{ width: "50%" }} />
          <i className="line" style={{ width: "85%" }} />
          <i className="line hl-red" style={{ width: "45%", marginLeft: "35%" }} />
          <p className="lp-caption">{menu[active].caption}</p>
        </Reveal>

        <Reveal delay={240} className="lp-demo-panel">
          <div className="lp-tabs" role="tablist">
            {tabs.map((t) => (
              <button key={t} role="tab" className={t === tab ? "is-active" : ""} onClick={() => setTab(t)}>{t}</button>
            ))}
          </div>
          <ul>
            {data[tab].map((c) => (
              <li key={c.name}>
                <div className="lp-clause-top">
                  <b>{c.name}</b>
                  <span className={`lp-tag tone-${c.tone}`}>{c.level}</span>
                </div>
                <p>{c.text}</p>
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}