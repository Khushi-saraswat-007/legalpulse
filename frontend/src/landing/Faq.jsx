import Reveal from "../components/Reveal";

const FAQS = [
  ["Which files can I upload?", "PDF, DOCX and plain text. Scanned PDFs without selectable text are not supported yet."],
  ["How is the risk score calculated?", "Each change is scored from the kind of change (50%), how many clauses depend on it (30%) and whether it contradicts another clause (20%). On top of that, what the change means adds up to 0.2: a number moving, a cap being removed, an obligation turning into a permission. Every part is shown in the report."],
  ["Are contradictions reliable?", "They are marked experimental. Their accuracy has not been measured on real labelled contracts yet, so treat them as hints, not findings."],
  ["What happens to a deleted clause?", "It is ranked as a risk and kept in the dependency graph as a dashed node, linked to the clauses that relied on it."],
];

export default function Faq() {
  return (
    <section className="lp-faq" id="faq">
      <div className="lp-container lp-faq-inner">
        <Reveal className="lp-faq-title">
          <span className="lp-eyebrow">FAQ</span>
          <h2 className="lp-lg">Questions, answered.</h2>
        </Reveal>
        <div className="lp-faq-list">
          {FAQS.map(([q, a], i) => (
            <Reveal key={q} delay={i * 80} className="lp-faq-item">
              <h3>{q}</h3>
              <p>{a}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
