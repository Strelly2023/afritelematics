const docs = [
  "NTS v1",
  "SDK Guide",
  "Federation",
  "Certification",
  "Public Trust Portal",
];

const capabilities = [
  "Policy-as-code",
  "Governance receipts",
  "Certificate chains",
  "Continuous assurance",
  "Federated trust graph",
  "Public verification",
];

const certification = [
  ["Level 1", "NovaScript Verified", "Produces verifiable artifacts"],
  ["Level 2", "NovaScript Trusted", "Demonstrates production evidence"],
  ["Level 3", "NovaScript Certified", "Meets high trust and auditability standards"],
];

export default function App() {
  return (
    <main>
      <header className="nav">
        <a className="brand" href="#home">NovaScript</a>
        <nav aria-label="Primary navigation">
          <a href="#docs">Docs</a>
          <a href="#network">Trust Network</a>
          <a href="#certification">Certification</a>
          <a href="#demo">Demo</a>
          <a href="#enterprise">Enterprise</a>
        </nav>
      </header>

      <section className="hero" id="home">
        <div className="hero-copy">
          <p className="eyebrow">Proof-Governed Engineering Intelligence</p>
          <h1>NovaScript: The Trust Layer for AI-Generated Software</h1>
          <p className="hero-text">
            Generate, govern, verify, and prove software trust across organizations.
          </p>
          <div className="actions">
            <a href="#demo" className="primary-action">Verify an artifact</a>
            <a href="#docs" className="secondary-action">Read the standard</a>
          </div>
        </div>
        <TrustScene />
      </section>

      <section className="band problem">
        <div className="section-inner">
          <p className="eyebrow">Problem</p>
          <h2>AI can generate software. Organizations still need proof.</h2>
          <div className="three-col">
            <Statement label="Trust" text="Can the artifact be independently verified?" />
            <Statement label="Compliance" text="Was the decision governed by policy?" />
            <Statement label="Audit" text="Can evidence survive external review?" />
          </div>
        </div>
      </section>

      <section className="band solution">
        <div className="section-inner">
          <p className="eyebrow">Solution</p>
          <h2>NovaScript turns AI output into verifiable trust artifacts.</h2>
          <div className="capability-grid">
            {capabilities.map((item) => (
              <div className="capability" key={item}>{item}</div>
            ))}
          </div>
        </div>
      </section>

      <section className="band lifecycle">
        <div className="section-inner">
          <p className="eyebrow">How it works</p>
          <h2>Prompt to public verification</h2>
          <div className="pipeline" aria-label="NovaScript lifecycle">
            {["Prompt", "Policy", "Receipt", "Certificate", "Assurance", "Verification"].map((step) => (
              <span key={step}>{step}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="band docs" id="docs">
        <div className="section-inner split">
          <div>
            <p className="eyebrow">Docs</p>
            <h2>Built as a standard, not a feature list.</h2>
          </div>
          <ul className="doc-list">
            {docs.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>

      <section className="band network" id="network">
        <div className="section-inner">
          <p className="eyebrow">Trust Network</p>
          <h2>Organizations exchange trust without exposing internal systems.</h2>
          <div className="network-map">
            <span>Org A</span>
            <span>Trust Exchange</span>
            <span>Org B</span>
            <span>Federation Validation</span>
            <span>Public Verification</span>
          </div>
        </div>
      </section>

      <section className="band certification" id="certification">
        <div className="section-inner">
          <p className="eyebrow">Certification</p>
          <h2>Clear trust levels for adopting organizations.</h2>
          <div className="cert-table">
            {certification.map(([level, label, meaning]) => (
              <div className="cert-row" key={level}>
                <strong>{level}</strong>
                <span>{label}</span>
                <p>{meaning}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="band demo" id="demo">
        <div className="section-inner split">
          <div>
            <p className="eyebrow">Demo</p>
            <h2>Paste a receipt ID. Validate a package. Inspect a certificate chain.</h2>
          </div>
          <form className="verify-form">
            <label htmlFor="receipt">Receipt ID</label>
            <input id="receipt" placeholder="rcpt-..." />
            <button type="button">Verify</button>
          </form>
        </div>
      </section>

      <section className="band enterprise" id="enterprise">
        <div className="section-inner">
          <p className="eyebrow">Enterprise</p>
          <h2>Risk dashboards, compliance mapping, audit readiness, and integration options.</h2>
          <div className="cta-row">
            <a href="mailto:partners@novascript.example" className="primary-action">Join the Trust Network</a>
            <a href="#docs" className="secondary-action">View API and SDK</a>
          </div>
        </div>
      </section>
    </main>
  );
}

function Statement({ label, text }) {
  return (
    <div className="statement">
      <strong>{label}</strong>
      <p>{text}</p>
    </div>
  );
}

function TrustScene() {
  return (
    <div className="trust-scene" aria-label="Trust graph visualization">
      <div className="node node-a">Org A</div>
      <div className="node node-b">Org B</div>
      <div className="node node-c">Auditor</div>
      <div className="node node-d">Public Portal</div>
      <div className="line line-ab" />
      <div className="line line-bc" />
      <div className="line line-bd" />
      <div className="artifact receipt">Receipt</div>
      <div className="artifact cert">Certificate</div>
      <div className="artifact assure">Assurance</div>
    </div>
  );
}
