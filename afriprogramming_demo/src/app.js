import { aiMessages, auditLog, systems } from "./demoData.js";

const steps = [
  { id: "dashboard", label: "Dashboard" },
  { id: "drift", label: "Drift" },
  { id: "uml", label: "Design" },
  { id: "replay", label: "Replay" },
  { id: "contracts", label: "Contracts" },
  { id: "proposal", label: "Proposal" },
  { id: "governance", label: "Governance" },
  { id: "activation", label: "Activation" },
  { id: "runtime", label: "Resolved" },
];

let activeSystemId = "afriride";
let activeStep = "dashboard";

const app = document.getElementById("app");

function activeSystem() {
  return systems.find((system) => system.id === activeSystemId) || systems[0];
}

function goTo(stepId) {
  activeStep = stepId;
  render();
}

function switchSystem(systemId) {
  activeSystemId = systemId;
  activeStep = "dashboard";
  render();
}

function nextStep() {
  const index = steps.findIndex((step) => step.id === activeStep);
  goTo(steps[Math.min(index + 1, steps.length - 1)].id);
}

function render() {
  const system = activeSystem();
  app.innerHTML = `
    ${renderTopbar(system)}
    <section class="layout">
      <section class="main-panel page-enter">
        ${renderStepper()}
        ${renderScreen(system)}
      </section>
      <aside class="side-panel">
        ${renderAiPanel()}
        ${renderGlobalInsights()}
        ${renderAuditLog()}
      </aside>
    </section>
  `;
  bindEvents();
  revealAiMessages();
}

function renderTopbar(system) {
  return `
    <header class="topbar">
      <div>
        <p class="eyebrow">AfriProgramming investor demo</p>
        <h1>Verified AI software, governed by proof</h1>
      </div>
      <div class="system-switcher" aria-label="System switcher">
        ${systems
          .map(
            (candidate) => `
              <button class="system-chip ${candidate.id === system.id ? "active" : ""}" data-system="${candidate.id}">
                <span>${candidate.name}</span>
                <small>${candidate.domain}</small>
              </button>
            `,
          )
          .join("")}
      </div>
    </header>
  `;
}

function renderStepper() {
  return `
    <nav class="stepper" aria-label="Demo flow">
      ${steps
        .map(
          (step) => `
            <button class="step ${step.id === activeStep ? "active" : ""}" data-step="${step.id}">
              ${step.label}
            </button>
          `,
        )
        .join("")}
    </nav>
  `;
}

function renderScreen(system) {
  const screen = {
    dashboard: renderDashboard,
    drift: renderDrift,
    uml: renderUml,
    replay: renderReplay,
    contracts: renderContracts,
    proposal: renderProposal,
    governance: renderGovernance,
    activation: renderActivation,
    runtime: renderRuntime,
  }[activeStep];
  return screen(system);
}

function renderDashboard(system) {
  return `
    <section class="hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">${system.environment} / ${system.region} / ${system.version}</p>
        <h2>${system.name}: system overview</h2>
        <p class="lede">A controlled simulation showing drift detection, replay proof, governed proposals, and activation boundaries.</p>
        <div class="button-row">
          <button class="primary-action" data-next>View Drift</button>
          <button class="secondary-action" data-step="proposal">Jump to Proposal</button>
        </div>
      </div>
      <div class="metric-grid">
        ${metric("Validation", "PASS", "success")}
        ${metric("Contracts", "ACTIVE", "success")}
        ${metric("Drift Alerts", system.status === "STABLE" ? "0" : "1", system.status === "STABLE" ? "success" : "warning")}
        ${metric("Authority", "GOVERNED", "info")}
      </div>
    </section>
  `;
}

function renderDrift(system) {
  return `
    <section>
      <p class="eyebrow">Runtime verification agent</p>
      <h2>Contract drift detected</h2>
      <div class="focus-card alert pulse">
        <div class="split-row">
          <span>Drift ID</span><strong>${system.drift.id}</strong>
        </div>
        <div class="split-row">
          <span>Contract</span><strong>${system.drift.contract}</strong>
        </div>
        <div class="compare-grid">
          <div><span>Observed</span><strong class="danger">${system.drift.observed}</strong></div>
          <div><span>Expected</span><strong class="success">${system.drift.expected}</strong></div>
        </div>
        <div class="split-row">
          <span>Severity / Confidence</span><strong>${system.drift.severity} / ${system.drift.confidence}</strong>
        </div>
      </div>
      ${nextButton("Investigate Design")}
    </section>
  `;
}

function renderUml(system) {
  return `
    <section>
      <p class="eyebrow">Design intelligence layer</p>
      <h2>UML-derived state intent</h2>
      <div class="two-column">
        <div class="focus-card">
          <h3>${system.uml.entity}</h3>
          ${system.uml.fields.map((field) => `<p class="code-line">- ${field}</p>`).join("")}
          <p class="code-line">+ validateTransition()</p>
        </div>
        <div class="focus-card">
          <h3>State model</h3>
          <div class="node-flow">${system.uml.states.map((state) => `<span>${state}</span>`).join("<b>-></b>")}</div>
          <p class="muted">Design informs proposals. It is not executable truth.</p>
        </div>
      </div>
      ${nextButton("Generate Proof")}
    </section>
  `;
}

function renderReplay(system) {
  return `
    <section>
      <p class="eyebrow">Deterministic replay synthesis</p>
      <h2>Replay proves the valid baseline</h2>
      <div class="focus-card timeline">
        ${system.replayTrace.map((item, index) => `<div class="timeline-row" style="animation-delay:${index * 220}ms"><span>${index + 1}</span><strong>${item}</strong><em>PASS</em></div>`).join("")}
      </div>
      <p class="boundary-note">Synthetic replay is a design-time proof aid, not production truth.</p>
      ${nextButton("View Contracts")}
    </section>
  `;
}

function renderContracts(system) {
  return `
    <section>
      <p class="eyebrow">Candidate contract inference</p>
      <h2>Replay-checked contract candidates</h2>
      <div class="card-list">
        ${system.contracts.map((contract) => `<div class="focus-card compact"><strong>${contract}</strong><span class="badge success">Replay verified</span></div>`).join("")}
      </div>
      ${nextButton("Generate Proposal")}
    </section>
  `;
}

function renderProposal(system) {
  return `
    <section>
      <p class="eyebrow">ToolingProposal</p>
      <h2>${system.drift.proposal}: governance-ready, blocked by default</h2>
      <div class="two-column">
        <div class="focus-card">
          <h3>Artifacts</h3>
          <p>Replay trace</p>
          <p>Contract validation</p>
          <p>Rollback plan</p>
        </div>
        <div class="focus-card">
          <h3>Validation</h3>
          ${statusLine("Replay", "PASS")}
          ${statusLine("Contracts", "PASS")}
          ${statusLine("Rollback", "READY")}
          ${statusLine("Governance", "REQUIRED")}
          ${statusLine("Activation", "BLOCKED")}
        </div>
      </div>
      <p class="boundary-note">Activation remains blocked until governance approval and activation-gate validation complete.</p>
      ${nextButton("Send to Governance")}
    </section>
  `;
}

function renderGovernance() {
  return `
    <section>
      <p class="eyebrow">Governance boundary</p>
      <h2>Approval is explicit</h2>
      <div class="focus-card">
        ${statusLine("Validation", "PASS")}
        ${statusLine("Replay", "VERIFIED")}
        ${statusLine("Rollback", "READY")}
        ${statusLine("Runtime mutation", "DENIED")}
      </div>
      <div class="button-row">
        <button class="primary-action" data-next>Approve</button>
        <button class="secondary-action" data-step="dashboard">Reject</button>
      </div>
    </section>
  `;
}

function renderActivation() {
  return `
    <section>
      <p class="eyebrow">Activation gate</p>
      <h2>Controlled activation checks</h2>
      <div class="focus-card checklist">
        ${statusLine("Validation complete", "YES")}
        ${statusLine("Governance approved", "YES")}
        ${statusLine("Replay consistency", "CONFIRMED")}
        ${statusLine("Hidden mutation path", "NONE")}
      </div>
      <p class="boundary-note">Runtime mutation is allowed only through this gate after explicit governance approval.</p>
      ${nextButton("Activate")}
    </section>
  `;
}

function renderRuntime(system) {
  return `
    <section>
      <p class="eyebrow">Runtime verification</p>
      <h2>System stable in the controlled simulation</h2>
      <div class="focus-card resolved">
        ${statusLine("Drift", "RESOLVED")}
        ${statusLine("Contracts", "ENFORCED")}
        ${statusLine("Replay", "CONSISTENT")}
        ${statusLine("Authority boundary", "PRESERVED")}
      </div>
      <p class="boundary-note">Classification remains controlled-pilot-ready, not production-proven.</p>
      <button class="secondary-action" data-step="dashboard">Restart Demo</button>
    </section>
  `;
}

function renderAiPanel() {
  return `
    <section class="ai-panel">
      <div class="panel-heading">
        <span>AI Assistant</span>
        <small>Non-authoritative</small>
      </div>
      <div id="aiMessages" class="ai-messages"></div>
      <p class="microcopy">Suggestions require validators, replay, and governance.</p>
    </section>
  `;
}

function renderGlobalInsights() {
  const activeDrifts = systems.filter((system) => system.status !== "STABLE").length;
  return `
    <section class="mini-card">
      <h3>Global insights</h3>
      ${statusLine("Systems monitored", String(systems.length))}
      ${statusLine("Active drift alerts", String(activeDrifts))}
      ${statusLine("Consensus signals", "1")}
    </section>
  `;
}

function renderAuditLog() {
  return `
    <section class="mini-card">
      <h3>Audit log</h3>
      ${auditLog.map((line) => `<p class="log-line">${line}</p>`).join("")}
    </section>
  `;
}

function metric(label, value, tone) {
  return `<div class="metric ${tone}"><span>${label}</span><strong>${value}</strong></div>`;
}

function statusLine(label, value) {
  return `<div class="split-row"><span>${label}</span><strong>${value}</strong></div>`;
}

function nextButton(label) {
  return `<button class="primary-action" data-next>${label}</button>`;
}

function bindEvents() {
  document.querySelectorAll("[data-next]").forEach((button) => {
    button.addEventListener("click", nextStep);
  });
  document.querySelectorAll("[data-step]").forEach((button) => {
    button.addEventListener("click", () => goTo(button.dataset.step));
  });
  document.querySelectorAll("[data-system]").forEach((button) => {
    button.addEventListener("click", () => switchSystem(button.dataset.system));
  });
}

function revealAiMessages() {
  const container = document.getElementById("aiMessages");
  const messages = aiMessages[activeStep] || [];
  messages.forEach((message, index) => {
    window.setTimeout(() => {
      const row = document.createElement("p");
      row.textContent = message;
      row.className = "ai-message";
      container.appendChild(row);
    }, index * 450);
  });
}

render();
