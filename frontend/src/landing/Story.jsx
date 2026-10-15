import Reveal from "../components/Reveal";

const Eyebrow = ({ children }) => <span className="lp-eyebrow">{children}</span>;

const PROBLEMS = [
  ["A clause is reworded", "A number or a word changes, and nobody notices it sits inside a longer paragraph."],
  ["A deadline moves", "Another clause quietly relied on the old date, and now the two disagree."],
  ["A clause disappears", "Everything that referred to it is left pointing at nothing."],
];

export function Problem() {
  return (
    <section className="lp-problem">
      <div className="lp-container">
        <Reveal>
          <Eyebrow>The problem</Eyebrow>
          <h2 className="lp-xl">Contracts change quietly. <span>The risk hides in what depends on the change.</span></h2>
        </Reveal>
        <div className="lp-cols">
          {PROBLEMS.map(([t, d], i) => (
            <Reveal key={t} delay={i * 100} className="lp-col">
              <h3>{t}</h3>
              <p>{d}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

const STEPS = [
  ["01", "Upload two versions", "Drop in the earlier and the revised contract. PDF, DOCX and TXT all work."],
  ["02", "We compare and trace", "Clauses are matched across versions, and a dependency graph shows what relies on what."],
  ["03", "Read the ranked report", "Every change is scored and explained, so you know where to look first."],
];

export function How() {
  return (
    <section className="lp-how" id="how">
      <div className="lp-container">
        <Reveal>
          <Eyebrow>How it works</Eyebrow>
          <h2 className="lp-lg">Three steps, no setup.</h2>
        </Reveal>
        <div className="lp-cols lp-cols-steps">
          {STEPS.map(([n, t, d], i) => (
            <Reveal key={n} delay={i * 120} className="lp-step">
              <div className="lp-step-top"><span>{n}</span><i /></div>
              <h3>{t}</h3>
              <p>{d}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Band() {
  return (
    <section className="lp-band">
      <div className="lp-container">
        <Reveal>
          <h2>Nothing disappears without a trace.</h2>
          <p>Even a deleted clause stays in the graph, linked to every clause that relied on it, and ranked by how much it matters.</p>
        </Reveal>
      </div>
    </section>
  );
}

const WHO = [
  ["Students and researchers", "Study how contract language shifts between drafts, with every change explained."],
  ["Legal and compliance teams", "Spot the riskiest edits in a revision before the signing meeting."],
  ["Anyone signing a revision", "Understand what actually changed, without reading every page twice."],
];

export function Who() {
  return (
    <section className="lp-who">
      <div className="lp-container">
        <Reveal>
          <Eyebrow>Who it is for</Eyebrow>
          <h2 className="lp-lg">Made for anyone who reads revisions closely.</h2>
        </Reveal>
        <div className="lp-cols">
          {WHO.map(([t, d], i) => (
            <Reveal key={t} delay={i * 100} className="lp-who-item">
              <i />
              <h3>{t}</h3>
              <p>{d}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
