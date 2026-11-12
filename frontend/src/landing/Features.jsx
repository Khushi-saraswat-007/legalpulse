import Reveal from "../components/Reveal";

const Bar = ({ w, kind = "" }) => <i className={`lp-bar ${kind}`} style={{ width: `${w}%` }} />;

function Tile({ title, text, children, className = "", delay = 0 }) {
  return (
    <Reveal delay={delay} className={`lp-tile ${className}`}>
      <div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
      {children}
    </Reveal>
  );
}

export default function Features() {
  return (
    <section className="lp-features" id="features">
      <div className="lp-container">
        <Reveal>
          <span className="lp-eyebrow">Features</span>
          <h2 className="lp-lg">Everything you need to review a revision.</h2>
        </Reveal>

        <div className="lp-bento">
          <Tile className="lp-tile-light lp-w2" title="See exactly what changed" text="Modified, added, deleted, renumbered, split and merged clauses are all recognised and shown side by side.">
            <div className="lp-ill-diff" aria-hidden="true">
              <div><small>v1</small><Bar w={90} /><Bar w={70} /><Bar w={85} /><Bar w={60} /></div>
              <div><small>v2</small><Bar w={90} /><Bar w={70} kind="y" /><Bar w={85} /><Bar w={60} kind="r" /></div>
            </div>
          </Tile>

          <Tile delay={100} title="Know who depends on it" text="A graph links clauses that cite each other, so one change shows its full reach.">
            <svg className="lp-ill-net" viewBox="0 0 300 120" fill="none" aria-hidden="true">
              <g stroke="#8FA8FF" strokeWidth="2" strokeLinecap="round" opacity="0.7">
                <path d="M60 60L150 28M150 28L240 60M60 60L150 96M150 96L240 60M150 28L150 96" />
              </g>
              <circle cx="60" cy="60" r="12" fill="#2A3550" stroke="#8FA8FF" strokeWidth="2" />
              <circle cx="150" cy="28" r="12" fill="#FBF3D9" stroke="#8F6A00" strokeWidth="2" />
              <circle cx="240" cy="60" r="12" fill="#2A3550" stroke="#8FA8FF" strokeWidth="2" />
              <circle cx="150" cy="96" r="12" fill="#FDEFE3" stroke="#B9540B" strokeWidth="2" strokeDasharray="4 3" />
            </svg>
          </Tile>

          <Tile title="Understand every score" text="Each risk shows the parts behind its score: the change, its impact and any contradiction.">
            <div aria-hidden="true">
              <div className="lp-split"><i style={{ flex: 5 }} /><i style={{ flex: 3 }} /><i style={{ flex: 2 }} /></div>
              <div className="lp-split-key"><span>change</span><span>impact</span><span>contradiction</span></div>
            </div>
          </Tile>

          <Tile delay={100} title="Works with your files" text="Upload PDF, DOCX or plain text. Clauses are extracted for you.">
            <div className="lp-files" aria-hidden="true"><b>.PDF</b><b>.DOCX</b><b>.TXT</b></div>
          </Tile>

          <Tile delay={200} title="Get alerted" text="Risky changes raise an alert on your dashboard until you mark them seen.">
            <div className="lp-alert-ill" aria-hidden="true"><i /><span>High risk found in your latest upload</span></div>
          </Tile>
        </div>
      </div>
    </section>
  );
}
