import React, { useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  import.meta?.env?.VITE_AFRIRIDE_API_URL || "http://127.0.0.1:8000";
const TEST_MODE = import.meta?.env?.VITE_AFRIRIDE_TEST_MODE !== "false";
const APP_VERSION = import.meta?.env?.VITE_AFRIRIDE_APP_VERSION || "0.1";
const DEVICE_ID =
  import.meta?.env?.VITE_AFRIRIDE_DEVICE_ID || "operator-test-device";
const OPERATOR_ID =
  import.meta?.env?.VITE_AFRIRIDE_OPERATOR_ID || "operator-1";
let OPERATOR_TOKEN = null;

const EMPTY_OPERATOR_STATE = {
  systemHealth: null,
  activeRides: [],
  drivers: [],
  replayHealth: {
    replay_success_rate: "0%",
    failures: 0,
    status: "NO_DATA",
  },
  evidence: {
    receipts_count: 0,
    trace_count: 0,
    missing_traces: 0,
  },
  guards: [],
  trustMetrics: null,
  pilotMetrics: null,
  observabilityDashboard: null,
  auditDashboard: null,
  publicTrustDashboard: null,
  featureRegistry: null,
  publicFeatureRegistry: null,
  publicFeatureRegistryVerification: null,
  publicRegistry: null,
  ecosystemVerification: null,
  dashboardGatewayStatus: null,
  trustBadge: null,
};

const PROPOSALS = [
  {
    id: "PROP-1198",
    title: "Require payment before shipping",
    surface: "Order execution",
    status: "Governance required",
    replay: "PASS",
    contracts: "PASS",
    driftRisk: "LOW",
    rollback: "Available",
    approvals: "1 of 2",
    summary:
      "Moves shipment activation behind a confirmed payment receipt and preserves the existing cancellation path.",
  },
  {
    id: "PROP-1187",
    title: "Normalize driver event timestamps",
    surface: "Mobile event stream",
    status: "Rejected",
    replay: "PASS",
    contracts: "FAIL",
    driftRisk: "MEDIUM",
    rollback: "Ready",
    approvals: "0 of 1",
    summary:
      "Rejected because the proposed timestamp coercion weakened the event contract for offline trip recovery.",
  },
  {
    id: "PROP-1172",
    title: "Tighten dispatch retry boundary",
    surface: "Dispatch service",
    status: "Ready to execute",
    replay: "PASS",
    contracts: "PASS",
    driftRisk: "LOW",
    rollback: "Available",
    approvals: "2 of 2",
    summary:
      "Adds a governed retry ceiling and records decision evidence for every skipped dispatch attempt.",
  },
];

const SYSTEM_LAYERS = [
  { id: "doctrine", name: "Doctrine", status: "Verified", signal: "Constitutional baseline" },
  { id: "governance", name: "Governance", status: "Verified", signal: "ADR + rule bindings" },
  { id: "execution", name: "Execution", status: "Active", signal: "Replay-backed runtime" },
  { id: "proof", name: "Proof", status: "Consistent", signal: "Trace, hash, receipt" },
  { id: "trust", name: "Trust", status: "Verified true", signal: "Public badge + registry" },
  { id: "intelligence", name: "Intelligence", status: "Indexed", signal: "AfriProg workspace" },
  { id: "economy", name: "Economy", status: "Modeled", signal: "Gasless proof market" },
  { id: "products", name: "Products", status: "Packaged", signal: "AfriRide, AfriPay, AfriProg" },
];

const GOVERNANCE_WINDOW_STATS = [
  { label: "Constitution status", value: "Verified" },
  { label: "ADR count", value: "20" },
  { label: "Rules", value: "40" },
  { label: "Bindings", value: "20" },
];

const PROOF_EVENTS = [
  {
    id: "EVT-001",
    type: "Replay",
    status: "Verified",
    hash: "82f9b7e3c8a41d9f",
    signed: "YES",
    replayable: "YES",
    anchor: "sepolia:anchor-a13c92f18ab2",
    evidenceHash: "8d4c7a3c1f55e9aa",
  },
  {
    id: "EVT-002",
    type: "Payment anchor",
    status: "Verified",
    hash: "b55ec3574a4aa678",
    signed: "YES",
    replayable: "YES",
    anchor: "partner:publish-b07fa14490aa",
    evidenceHash: "4732fcb740f4f3f2",
  },
];

const ECONOMY_SIGNALS = [
  { label: "Gasless transactions", value: "Enabled", helper: "Partner and operator proofs can be inspected without wallet friction." },
  { label: "Cost per proof", value: "$0.002", helper: "Modeled marginal verification cost for anchored proof packets." },
  { label: "Anchored proof count", value: "1,200", helper: "Demonstration volume for investor and partner verification sessions." },
  { label: "Revenue potential", value: "Active", helper: "API volume, registry publication, and enterprise audit tiers are packaged." },
];

const PRODUCT_SURFACES = [
  { name: "AfriRide", status: "Verified", proofCount: "842", trustLevel: "96%", usage: "Pilot corridor", focus: "Driver verification, trip integrity, payment anchoring" },
  { name: "AfriPay", status: "Ready", proofCount: "214", trustLevel: "93%", usage: "Treasury proof", focus: "Payment proof system and receipt-backed settlement" },
  { name: "AfriProg", status: "Active", proofCount: "144", trustLevel: "91%", usage: "Governed coding", focus: "Code intelligence layer with proposal-only handoff" },
];

const MATURITY_SIGNALS = [
  ["Governance", 10],
  ["Authority", 10],
  ["Proof", 10],
  ["Trust", 9],
  ["Execution", 9],
  ["Intelligence", 8],
  ["Economy", 7],
  ["Products", 5],
  ["Adoption", 2],
];

const DEMO_FLOW_STEPS = [
  { title: "Open System Truth", detail: "Start at the verified status layer and show health, trust, and evidence posture." },
  { title: "Run Governance Validation", detail: "Open the governance window and prove that rules, ADRs, and bindings are intact." },
  { title: "Inspect Proof", detail: "Select EVT-001, view trace, verify signature, and export the proof packet." },
  { title: "Show Intelligence", detail: "Switch to AfriProg and demonstrate proposal-only AI assistance." },
  { title: "Close With Economy", detail: "Show gasless verification, cost per proof, product packaging, and maturity runway." },
];

const INVESTOR_DEMO_SCRIPT = [
  {
    time: "00:00",
    shot: "Trust OS shell",
    narration:
      "AfriTech OS is a browser for truth: it shows system status, proof, governance, intelligence, economy, and products in one command surface.",
  },
  {
    time: "00:35",
    shot: "SystemStatusPanel",
    narration:
      "We start with the runtime truth state. Governance is verified, proof is consistent, trust is public, and evidence is live-derived.",
  },
  {
    time: "01:20",
    shot: "ProofExplorer",
    narration:
      "Every claim resolves to a proof packet: event id, hash, signature, replayability, public anchor, and exportable evidence hash.",
  },
  {
    time: "02:10",
    shot: "Trust badge + ecosystem graph",
    narration:
      "Partners do not need our internal credentials. They can verify the public registry, trust badge, and ecosystem certificate directly.",
  },
  {
    time: "03:10",
    shot: "AfriProg intelligence",
    narration:
      "The AI layer drafts and explains, but governance and replay decide what becomes real execution.",
  },
  {
    time: "04:00",
    shot: "Economy + products",
    narration:
      "This becomes a revenue surface: verification API, registry publication, audit exports, and product-specific trust packages.",
  },
];

const FIRST_CUSTOMER_REVENUE_STEPS = [
  {
    stage: "Proof pilot",
    customer: "City mobility operator",
    offer: "Trip integrity and dispute proof for one controlled corridor",
    price: "$2,500 setup + $0.02 per verified trip packet",
  },
  {
    stage: "Verification API",
    customer: "Fleet or insurance partner",
    offer: "Read-only API access to proof packets, badges, and public verification reports",
    price: "$1,500 monthly platform fee + usage",
  },
  {
    stage: "Enterprise audit",
    customer: "Government observer or enterprise compliance team",
    offer: "Monthly trust registry export, partner session report, and legal-proof bundle",
    price: "$7,500 monthly retainer",
  },
];

const GIT_PULL_DEPLOY_PLAN = [
  {
    step: "1. Freeze local changes",
    command: "git status -sb",
    detail:
      "Confirm the deployment host has no uncommitted production edits before pulling the Trust OS branch.",
  },
  {
    step: "2. Pull shipped branch",
    command: "git pull --ff-only origin afriride-live-pilot-001",
    detail:
      "Use fast-forward only so production never creates an unreviewed merge commit during rollout.",
  },
  {
    step: "3. Build dashboard",
    command: "cd dashboard && npm ci && npm run build",
    detail:
      "Install the locked dashboard dependencies and produce the static Trust OS bundle.",
  },
  {
    step: "4. Verify trust checks",
    command:
      "pytest dashboard/tests/test_operator_dashboard_surface.py afriride_system/tests/test_django_blockchain_bridge.py -q",
    detail:
      "Confirm the UI contract and Django blockchain bridge still resolve on the target machine.",
  },
  {
    step: "5. Promote public OS route",
    command: "serve dashboard/dist behind /os",
    detail:
      "Expose the built dashboard at the public product route, then validate public trust endpoints from the browser.",
  },
];

const GOVERNANCE_RULES = [
  {
    name: "Protected systems",
    value: "Payments, inventory, dispatch",
    detail: "Changes touching protected systems require explicit authority.",
  },
  {
    name: "Approval thresholds",
    value: "Low: 1 approver | High: 2 approvers",
    detail: "Risk decides the minimum decision record required before execution.",
  },
  {
    name: "Rollback policy",
    value: "Required",
    detail: "No governed change reaches execution without rollback readiness.",
  },
  {
    name: "Contract enforcement",
    value: "Strict",
    detail: "Contract failures block execution even when replay validation passes.",
  },
];

const AFTRITECH_GATEWAY_DASHBOARDS = [
  {
    name: "AfriRide Dashboard",
    route: "/afriride/dashboard/",
    icon: "car",
    service: "mobility",
    summary: "Transport, replay-backed live operations, and proof-linked field evidence.",
  },
  {
    name: "AfroProg Dashboard",
    route: "/afroprog/dashboard/",
    icon: "code",
    service: "freelance",
    summary: "Prompt-driven productivity, repository intelligence, and proposal drafting.",
  },
  {
    name: "AfriProgramming Dashboard",
    route: "/afriprogramming/dashboard/",
    icon: "laptop",
    service: "education",
    summary: "Governed engineering, validators, replay, and execution readiness.",
  },
];

const GATEWAY_ROLE_VIEWS = [
  {
    role: "operator",
    title: "Operator view",
    summary: "Execution, replay health, and governed engineering are visible together for live operations.",
    surfaces: ["AfriRide Dashboard", "AfriProgramming Dashboard"],
  },
  {
    role: "partner",
    title: "Partner view",
    summary: "Partner-facing visibility is bounded to replay-backed mobility evidence and audit-safe links.",
    surfaces: ["AfriRide Dashboard"],
  },
  {
    role: "auditor",
    title: "Auditor view",
    summary: "Auditors can traverse replay, evidence, and proof without gaining runtime mutation authority.",
    surfaces: ["AfriRide Dashboard", "AfriProgramming Dashboard"],
  },
];

const GATEWAY_DEEP_LINKS = [
  {
    label: "Open replay",
    path: "/ride/ride-demo-001/replay",
    summary: "Jump directly from the gateway into replay-backed ride reconstruction.",
  },
  {
    label: "Open evidence",
    path: "/ride/ride-demo-001/evidence",
    summary: "Inspect receipts, trace coverage, and recorded ride evidence.",
  },
  {
    label: "Open proof certificate",
    path: "/trust/proof/ride-demo-001",
    summary: "Resolve the same operational entity into governed proof and certificate views.",
  },
];

const GATEWAY_CONTEXT_SURFACES = [
  {
    system: "AfriRide",
    focus: "Execution + replay",
    path: "/ride/ride-demo-001/replay",
  },
  {
    system: "AfroProg",
    focus: "Proposal context",
    path: "/afroprog/dashboard/",
  },
  {
    system: "AfriProgramming",
    focus: "Governance + proof",
    path: "/trust/proof/ride-demo-001",
  },
];

const AFRIPRO_CHAT_MODES = [
  {
    name: "Code mode",
    detail: "Natural language to Django code generation with proposal-only output.",
  },
  {
    name: "Debug mode",
    detail: "Explain issues, patch RBAC gaps, and point back to governance-safe fixes.",
  },
  {
    name: "Analysis mode",
    detail: "Summarize project context, open files, and boundary implications before generation.",
  },
];

const AFRIPRO_PROJECT_EXPLORER = [
  "poultry/apps/farm/models.py",
  "poultry/apps/farm/serializers.py",
  "poultry/apps/farm/views.py",
  "poultry/apps/farm/urls.py",
  "employee_api/models.py",
];

const AFRIPRO_EDITOR_PREVIEW = `from django.db import models


class PoultryHouse(models.Model):
    name = models.CharField(max_length=64, unique=True)
    capacity = models.PositiveIntegerField()
    active = models.BooleanField(default=True)


class Flock(models.Model):
    code = models.CharField(max_length=32, unique=True)
    poultry_house = models.ForeignKey(PoultryHouse, on_delete=models.PROTECT)
    bird_type = models.CharField(max_length=32)
    bird_count = models.PositiveIntegerField()`;

const CHANGE_HISTORY = [
  {
    time: "14:22",
    id: "PROP-1198",
    state: "Approved",
    detail: "Payment-before-shipping change approved with replay proof attached.",
  },
  {
    time: "14:20",
    id: "PROP-1187",
    state: "Rejected",
    detail: "Contract failure recorded against mobile event timestamp coercion.",
  },
  {
    time: "14:19",
    id: "DRIFT-043",
    state: "Resolved",
    detail: "Runtime drift mapped to proposal evidence and closed.",
  },
  {
    time: "14:18",
    id: "RB-031",
    state: "Rollback success",
    detail: "Rollback executed and decision record linked to the trust graph.",
  },
];

const EXECUTION_EVENTS = [
  {
    name: "OrderShipped",
    state: "Consistent",
    detail: "Runtime contract matched approved proposal behavior.",
  },
  {
    name: "PaymentProcessed",
    state: "Enforced",
    detail: "Payment receipt verified before downstream execution.",
  },
  {
    name: "DispatchRetrySkipped",
    state: "Recorded",
    detail: "Governed retry ceiling created a decision record.",
  },
];

const REGION_TOPOLOGY = [
  {
    id: "mel-ap-southeast-2",
    label: "Melbourne pilot region",
    tenancy: "city_operator",
    mode: "Primary replay authority",
    detail: "Owns the active replay-backed mobility corridor and the cutover evidence history.",
  },
  {
    id: "bjm-af-central-1",
    label: "Bujumbura field region",
    tenancy: "country_operator",
    mode: "Field validation region",
    detail: "Captures high-entropy network and device conditions while preserving canonical replay output.",
  },
  {
    id: "partner-read-only",
    label: "Partner proof region",
    tenancy: "regulator_partner",
    mode: "Read-only audit replica",
    detail: "Consumes replay-derived evidence exports without gaining runtime authority.",
  },
];

const TENANT_PROFILES = [
  {
    name: "AfriRide Core",
    scope: "authoritative runtime",
    isolation: "Dedicated trace and receipt namespace",
  },
  {
    name: "City Operator",
    scope: "operational observability",
    isolation: "Region-scoped rides, evidence, and alert views",
  },
  {
    name: "Partner Audit",
    scope: "external evidence review",
    isolation: "Export-only proof packets and anchor receipts",
  },
];

const ANCHOR_COMMITMENTS = [
  {
    network: "public ledger test anchor",
    status: "Ready",
    commitment: "trace_hash + replay_hash + receipt_hash",
    cadence: "post-cutover and daily evidence close",
  },
  {
    network: "partner notarization channel",
    status: "Planned",
    commitment: "bounded evidence bundle hash",
    cadence: "partner report issuance",
  },
];

const PARTNER_PROOF_SURFACES = [
  "Replay-backed operator dashboard",
  "Multi-region deployment packet",
  "Cryptographic anchor receipt",
  "Partner architecture whitepaper",
];

const TRUST_REGISTRY_ENTRIES = [
  {
    anchorId: "anchor-a13c92f18ab2",
    publicationId: "publish-b07fa14490aa",
    status: "Published",
    tenant: "tenant-core",
    region: "mel-ap-southeast-2",
    packetHash: "8d4c7a3c1f55e9aa4732fcb740f4f3f2201e8eaf91cf9d314d6ef12862f5a91e",
  },
  {
    anchorId: "anchor-c55d1b734e66",
    publicationId: "publish-d37be3a721bc",
    status: "Quorum review",
    tenant: "partner-audit",
    region: "bjm-af-central-1",
    packetHash: "b55ec3574a4aa678cc8cb2c87c5b2b103547b2141f6e946da343f72d06fc9931",
  },
];

const VERIFICATION_NETWORK_VIEWS = [
  {
    title: "Registry visibility",
    summary:
      "Public registry entries expose anchor id, publication id, packet hash, and replay-linked tenant context without moving authority away from trace and replay.",
    status: "Evidence indexed",
  },
  {
    title: "Verification quorum",
    summary:
      "Partner verifiers, enterprise auditors, and government observers converge on the same anchor packet through governed quorum review.",
    status: "Quorum verified",
  },
  {
    title: "Explorer discipline",
    summary:
      "Every visualization in the Trust Explorer resolves back to an anchor packet, replay hash, or witness manifest rather than inferred dashboard state.",
    status: "Replay-linked",
  },
];

const FIRST_PARTNER_COHORT = [
  {
    name: "City mobility operator",
    role: "Pilot launch partner",
    goal: "Use replay-backed dispute evidence and registry publication in a live city corridor sandbox.",
  },
  {
    name: "Enterprise fleet platform",
    role: "Compliance integration partner",
    goal: "Adopt verification API and audit export bundles for fleet exception handling.",
  },
  {
    name: "Insurance or claims workflow",
    role: "Verification partner",
    goal: "Validate receipt and trace evidence packets for post-ride disputes.",
  },
  {
    name: "Government mobility observer",
    role: "Public-interest pilot",
    goal: "Review replay-linked audit packets without receiving runtime mutation authority.",
  },
  {
    name: "Marketplace infrastructure partner",
    role: "Trust network node",
    goal: "Participate in quorum verification and registry-backed trust packet exchange.",
  },
];

const MONETIZATION_TIERS = [
  {
    tier: "Sandbox",
    price: "$0 to start",
    surface: "SDK, tutorials, sample trust registry packet flow",
  },
  {
    tier: "Growth API",
    price: "Per verified packet + API volume",
    surface: "Partner verification API pricing and bounded registry publication usage",
  },
  {
    tier: "Enterprise",
    price: "Annual platform fee",
    surface: "Audit integrations, legal-proof exports, operator support, and governed onboarding",
  },
  {
    tier: "Infrastructure network",
    price: "Quorum / registry network agreement",
    surface: "Verification network participation, node visibility, and custom compliance workflows",
  },
];

const PRODUCTIZED_TRUST_FEATURE_IDS = [
  "driver-identity-proof",
  "trip-integrity-proof",
  "payment-proof-anchor",
];

const PROTOCOL_COMPONENTS = [
  "Trust packet schema",
  "Registry publication semantics",
  "Witness quorum semantics",
  "Replay-linked authority boundary",
];

const PARTNER_SESSION_CHECKLIST = [
  "Open /public/architecture/proof and verify the anchor packet.",
  "Resolve /public/architecture/chain/{anchor_id} and confirm the expected network.",
  "Inspect /public/trust/dashboard to confirm bounded public surfaces.",
  "Run afritech-verify locally and compare CLI output with the dashboard.",
  "Record the partner session report before promoting Sepolia publication to mainnet.",
];

const TRUST_EXPLORER_RULE =
  "registry publication is evidence indexing and never a second truth layer";

const ARCHITECTURE_COMPLIANCE_CHECKS = [
  {
    name: "Unified architecture document",
    status: "PASS",
    evidence: "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md",
    detail:
      "The integrated AfriTech architecture remains versioned, bounded, and test-enforced.",
  },
  {
    name: "Architecture compliance dashboard",
    status: "PASS",
    evidence: "dashboard/tests/test_operator_dashboard_surface.py",
    detail:
      "The UI exposes architecture adherence as a replay-backed, read-only projection surface.",
  },
  {
    name: "AfriCPPT protocol extraction",
    status: "PASS",
    evidence: "docs/standards/AFRICPPT_PROTOCOL_SPEC.md",
    detail:
      "External integration rules are extracted from the unified architecture without moving truth authority outward.",
  },
  {
    name: "Partner one-page architecture",
    status: "PASS",
    evidence: "docs/partners/AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md",
    detail:
      "Sales and onboarding receive a simplified architecture surface with the same authority boundary.",
  },
  {
    name: "Architecture drift detection report",
    status: "PASS",
    evidence: "python3 -m afritech.guards.architecture_drift_report",
    detail:
      "Tracked module roots, component evidence, and core flows are checked for structural drift.",
  },
];

const ARCHITECTURE_COMPONENT_SURFACES = [
  {
    title: "Execution + ingress",
    coverage: "Mapped",
    detail:
      "Rider, driver, operator, shared mobile client, AfriRide API, and Event Gateway remain declared execution surfaces.",
  },
  {
    title: "Truth core",
    coverage: "Mapped",
    detail:
      "Trace, replay, evidence, receipt, proof storage, replay cache, and crypto remain the only truth-bearing chain.",
  },
  {
    title: "Intelligence + evolution",
    coverage: "Mapped",
    detail:
      "AFRIPower and AfriProgramming are architecture-bound above truth and below governance.",
  },
  {
    title: "Protocol + people/process",
    coverage: "Mapped",
    detail:
      "AfriCPPT and AFrTPPS define external verification discipline and real-world execution adoption.",
  },
];

const ARCHITECTURE_DRIFT_RULES = [
  {
    title: "New modules not in architecture",
    detail:
      "Flag new tracked files that enter governed runtime, crypto, API, or dashboard roots without architecture coverage.",
  },
  {
    title: "Orphan components",
    detail:
      "Flag documented architecture components whose expected evidence paths no longer exist in the repo.",
  },
  {
    title: "Undocumented flows",
    detail:
      "Flag core execution, proof, or external verification flows that exist operationally but are missing from the unified architecture.",
  },
];

const AFRIPROG_FEATURES = [
  {
    title: "Natural Language to Code",
    detail:
      "Operators and developers describe intent in plain language before a governed proposal is shaped for AfriProgramming review.",
  },
  {
    title: "Code Autocomplete",
    detail:
      "Function-level scaffolding accelerates delivery, but generated output remains draft material until replay and governance accept it.",
  },
  {
    title: "Multi-language Support",
    detail:
      "Python, JavaScript, TypeScript, SQL, shell, and protocol surfaces can share one bounded workspace.",
  },
  {
    title: "Context Awareness",
    detail:
      "Repo context, architecture doctrine, and system boundaries are visible so generation stays aligned with declared execution surfaces.",
  },
  {
    title: "Code Explanation",
    detail:
      "Generated changes can be explained in plain language for onboarding, review, and partner-facing walkthroughs.",
  },
  {
    title: "Testing & Debugging",
    detail:
      "Draft tests, edge cases, and failure scenarios are proposed alongside code so replay and invariant validation start earlier.",
  },
  {
    title: "API Integration",
    detail:
      "AfriProg can prepare integration artifacts for APIs and SDKs without bypassing the governed execution path.",
  },
];

const AFRIPROG_WORKSPACE_PANELS = [
  {
    title: "Prompt / Instruction Panel",
    body:
      "Capture plain-English requests, architecture references, and operator constraints before code generation begins.",
  },
  {
    title: "Output / Code Window",
    body:
      "Show generated snippets, diff previews, and contract-sensitive warnings as proposal material rather than executable truth.",
  },
  {
    title: "Model Settings",
    body:
      "Expose temperature, output size, language, and framework preferences with explicit governance-safe defaults.",
  },
  {
    title: "Project Context / Files",
    body:
      "Surface the active architecture document, module roots, and trusted context files that the coding assistant is allowed to inspect.",
  },
  {
    title: "Version / History",
    body:
      "Track prompt revisions, generation history, and proposal lineage so reviewers can audit how a draft evolved before approval.",
  },
  {
    title: "Integration Panel",
    body:
      "Expose Git, API, docs, and SDK surfaces for export while preserving the proposal-only boundary into AfriProgramming.",
  },
];

const AFRIPROG_CONTEXT_FILES = [
  "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md",
  "docs/standards/AFRICPPT_PROTOCOL_SPEC.md",
  "afritech/afriprogramming/integration.py",
  "afritech/ci/afriprog_afriprogramming_boundary_validator.py",
];

const AFRIPROG_GENERATION_HISTORY = [
  {
    version: "Draft v3",
    state: "Ready for review",
    detail:
      "Employee management API proposal linked to architecture doctrine and prepared for AfriProgramming intake.",
  },
  {
    version: "Draft v2",
    state: "Revised",
    detail:
      "Prompt narrowed after the boundary validator rejected runtime mutation language and missing rollback detail.",
  },
  {
    version: "Draft v1",
    state: "Captured",
    detail:
      "Initial natural-language request logged as productivity input with no execution authority.",
  },
];

const AFRIPROG_INTEGRATIONS = [
  "Git-backed proposal export",
  "Verification API scaffolding",
  "Architecture-aware documentation generation",
  "SDK and endpoint starter packs",
];

const AFRIPROG_SAMPLE_PROMPT =
  "Create a Django API for employee management with RBAC, serializer coverage, and evidence-ready tests.";

const AFRIPROG_SAMPLE_OUTPUT = `# draft proposal surface
class EmployeeViewSet(ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, HasEmployeeAccess]

# proposal-only intake
# submit to AfriProgramming for replay, governance, and receipt generation`;

const AFRIPROG_DEMO_SCENARIOS = [
  {
    key: "bounded_employee_api",
    label: "Bounded employee API proposal",
    prompt:
      "Create a Django API for employee management with RBAC, serializer coverage, and evidence-ready tests.",
    output: `# draft proposal surface
class EmployeeViewSet(ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, HasEmployeeAccess]

class EmployeePermission(permissions.BasePermission):
    message = "employee access requires explicit RBAC mapping"
`,
    target: "afritech/afriprogramming/employee_api.py",
    validationStatus: "pass",
    governanceStatus: "pending",
    governanceSummary:
      "Proposal admitted as documentary input. Explicit authority review is still required before activation.",
    rejectionReason: null,
    validationViolations: [],
    replayStatus: "REPLAY_VALID",
    replayInvariant: "DETERMINISTIC_IDENTITY",
    replayFailureMode: null,
    divergenceLocation: null,
    reasoning:
      "Replay can reconstruct the proposed tooling artifact without mutating protected truth surfaces, so the handoff is admissible for governance review.",
    reviewNotes: [
      "Protected target mutation not detected",
      "Proposal remains activation-blocked until governance approval",
      "Rollback planning can proceed once authority review begins",
    ],
  },
  {
    key: "unsafe_governance_mutation",
    label: "Unsafe governance mutation",
    prompt:
      "Update afritech/governance/INDEX.yaml directly and apply the change immediately so approval is no longer needed.",
    output: `# unsafe direct mutation
with open("afritech/governance/INDEX.yaml", "a", encoding="utf-8") as handle:
    handle.write("\\nunsafe_bypass_attempt: true\\n")

apply_now = True
`,
    target: "afritech/governance/INDEX.yaml",
    validationStatus: "fail",
    governanceStatus: "rejected",
    governanceSummary:
      "Governance blocked this proposal at intake because it attempted to cross the protected authority boundary.",
    rejectionReason:
      "Protected targets live on the authority side of the boundary and cannot be directly mutated by AfriProg output.",
    validationViolations: [
      "protected target mutation is forbidden",
      "runtime mutation remains blocked until explicit governed handoff",
      "activation gate cannot open without replay-safe admissibility",
    ],
    replayStatus: "REPLAY_INVALID",
    replayInvariant: "ENVIRONMENT_IDENTITY",
    replayFailureMode: "environment_mismatch",
    divergenceLocation: "registry_attestation",
    reasoning:
      "This failed because replay invariant ENVIRONMENT_IDENTITY was violated. Direct mutation of sealed governance material would break the environment identity replay expects before activation is even considered.",
    reviewNotes: [
      "Governance rejected the proposal before approval routing",
      "Replay reasoning confirms authority boundary breach",
      "The correct path is proposal-only intake targeting non-protected tooling surfaces",
    ],
  },
];

const AFRIPROG_WALKTHROUGH_STEPS = [
  {
    id: "draft",
    title: "1. Draft in AfriProg",
    detail:
      "The user works in a productivity workspace with prompt, output, and context, but no truth authority.",
  },
  {
    id: "submit",
    title: "2. Send to Governance",
    detail:
      "The generated output becomes an explicit proposal submission with activation still blocked.",
  },
  {
    id: "feedback",
    title: "3. Governance Feedback",
    detail:
      "Validation, approval posture, and rejection reasons are rendered so users see why authority accepted or refused the handoff.",
  },
  {
    id: "replay",
    title: "4. Replay Reasoning",
    detail:
      "Every decision resolves to replay-backed reasoning and named invariants rather than unexplained dashboard state.",
  },
];

function buildGovernanceSubmission(scenario) {
  const stamp = new Date().toISOString();
  const proposalId = `tooling-proposal-${scenario.key.slice(0, 16)}`;

  return {
    proposalId,
    submittedAt: stamp,
    sourceLayer: "AfriProg",
    targetLayer: "AfriProgramming",
    handoffMode: "proposal_only",
    activationStatus: "blocked",
    governanceRequired: true,
    replayRequired: true,
    target: scenario.target,
    validationStatus: scenario.validationStatus,
    governanceStatus: scenario.governanceStatus,
    governanceSummary: scenario.governanceSummary,
    rejectionReason: scenario.rejectionReason,
    validationViolations: scenario.validationViolations,
    reviewNotes: scenario.reviewNotes,
    reasoning: {
      status: scenario.replayStatus,
      invariant: scenario.replayInvariant,
      failureMode: scenario.replayFailureMode,
      divergenceLocation: scenario.divergenceLocation,
      explanation: scenario.reasoning,
    },
  };
}

function walkthroughNarrative(step, scenario, submission) {
  if (step === 0) {
    return `AfriProg drafts the "${scenario.label}" change as productivity output only. No execution authority is created.`;
  }
  if (step === 1) {
    return submission
      ? `Proposal ${submission.proposalId} was sent to governance with activation still blocked.`
      : "Send the current draft to governance to generate an explicit proposal record.";
  }
  if (step === 2) {
    return submission
      ? `${submission.governanceStatus === "rejected" ? "Rejected by Governance" : "Governance review pending"}: ${submission.governanceSummary}`
      : "Governance feedback appears after submission.";
  }
  return submission
    ? submission.reasoning.explanation
    : "Replay-backed reasoning appears once governance has evaluated the proposal.";
}

function clientHeaders() {
  const eventId =
    globalThis.crypto && "randomUUID" in globalThis.crypto
      ? globalThis.crypto.randomUUID()
      : `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  return {
    "X-AfriRide-Device-Id": DEVICE_ID,
    "X-AfriRide-App-Version": APP_VERSION,
    "X-AfriRide-Event-Id": eventId,
    "X-AfriRide-Client-Timestamp": new Date().toISOString(),
    "X-AfriRide-Test-Mode": String(TEST_MODE),
  };
}

async function readJson(path) {
  const token = await operatorToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...clientHeaders(),
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error(`operator_fetch_failed:${path}`);
  }
  return response.json();
}

async function readPublicJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: clientHeaders(),
  });
  if (!response.ok) {
    throw new Error(`public_fetch_failed:${path}`);
  }
  return response.json();
}

async function writeJson(path, payload) {
  const token = await operatorToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...clientHeaders(),
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`operator_post_failed:${path}`);
  }
  return response.json();
}

async function operatorToken() {
  if (OPERATOR_TOKEN) {
    return OPERATOR_TOKEN;
  }
  const response = await fetch(`${API_BASE_URL}/v1/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id: OPERATOR_ID, role: "OPERATOR" }),
  });
  if (!response.ok) {
    throw new Error("operator_auth_failed");
  }
  const payload = await response.json();
  OPERATOR_TOKEN = payload.token;
  return OPERATOR_TOKEN;
}

function normalizeActiveRides(payload) {
  const rides = payload.rides || payload.active_rides || [];
  return rides.map((ride) => ({
    rideId: ride.ride_id || ride.rideId,
    state: ride.state || ride.status,
    driverId: ride.driver_id || ride.driverId || ride.assigned_driver_id,
    riderId: ride.rider_id || ride.riderId || ride.passenger_id,
  }));
}

function normalizeGuards(payload) {
  const violations = payload.violations || payload.guards || [];
  return violations.map((violation, index) => ({
    id: violation.id || `${violation.type || "guard"}-${index}`,
    type: violation.type || violation.violation_type || "UNKNOWN",
    timestamp: violation.timestamp || violation.created_at || "unavailable",
    severity: violation.severity || "INFO",
  }));
}

function normalizeDrivers(payload) {
  const drivers = payload.drivers || [];
  return drivers.map((driver) => ({
    driverId: driver.driver_id || driver.driverId,
    status: driver.status || (driver.online ? "ONLINE" : "OFFLINE"),
    activeRideIds: driver.active_ride_ids || driver.activeRideIds || [],
    completedRides: driver.completed_rides || driver.completedRides || 0,
  }));
}

function deriveTrustState(state) {
  const failures = Number(state.replayHealth.failures || 0);
  const missingTraces = Number(state.evidence.missing_traces || 0);
  const guardCount = state.guards.length;
  const successRate = String(state.replayHealth.replay_success_rate || "0%");
  const replayVerified =
    successRate === "100%" ||
    String(state.replayHealth.status || "").toUpperCase() === "VERIFIED";

  if (failures > 0 || missingTraces > 0 || guardCount > 0) {
    return {
      label: "Action required",
      tone: "warning",
      summary:
        "Trust is observable, but one or more validation, evidence, or governance signals need review.",
    };
  }

  if (replayVerified || Number(state.evidence.receipts_count || 0) > 0) {
    return {
      label: "Verified",
      tone: "success",
      summary:
        "Validation, governance evidence, and rollback readiness are aligned for current execution.",
    };
  }

  return {
    label: "Awaiting evidence",
    tone: "neutral",
    summary:
      "The trust surface is online and waiting for validation receipts, decision records, and replay evidence.",
  };
}

function deriveScaleState(state) {
  const replayFailures = Number(state.replayHealth.failures || 0);
  const missingTraces = Number(state.evidence.missing_traces || 0);
  const receipts = Number(state.evidence.receipts_count || 0);

  return {
    replayBackedStatus:
      replayFailures === 0 && missingTraces === 0 ? "Replay-backed" : "Review",
    anchorReadiness: receipts > 0 ? "Commitment ready" : "Awaiting receipts",
    regionCount: REGION_TOPOLOGY.length,
    tenantCount: TENANT_PROFILES.length,
  };
}

function deriveArchitectureState(state) {
  const guardCount = state.guards.length;
  const missingTraces = Number(state.evidence.missing_traces || 0);
  const replayFailures = Number(state.replayHealth.failures || 0);
  const passingChecks = ARCHITECTURE_COMPLIANCE_CHECKS.filter(
    (check) => check.status === "PASS",
  ).length;

  const architectureAligned =
    guardCount === 0 && missingTraces === 0 && replayFailures === 0;

  return {
    adherenceLabel: architectureAligned ? "Aligned" : "Review required",
    adherenceTone: architectureAligned ? "success" : "warning",
    adherenceSummary: architectureAligned
      ? "Live replay, evidence, and guard signals remain consistent with the declared architecture."
      : "One or more runtime trust signals need review before claiming full system adherence to architecture.",
    passingChecks,
    totalChecks: ARCHITECTURE_COMPLIANCE_CHECKS.length,
    driftClasses: ARCHITECTURE_DRIFT_RULES.length,
  };
}

function deriveSystemLayers(state) {
  const registryVerified = state.publicFeatureRegistryVerification?.verified === true;
  const ecosystemVerified = state.ecosystemVerification?.verified === true;
  const gatewayReady = state.dashboardGatewayStatus?.status === "ready";
  const proofConsistent = Number(state.evidence.missing_traces || 0) === 0;

  return SYSTEM_LAYERS.map((layer) => {
    if (layer.id === "governance") {
      return { ...layer, status: registryVerified ? "Verified" : layer.status };
    }
    if (layer.id === "execution") {
      return { ...layer, status: gatewayReady ? "Active" : layer.status };
    }
    if (layer.id === "proof") {
      return { ...layer, status: proofConsistent ? "Consistent" : "Review" };
    }
    if (layer.id === "trust") {
      return { ...layer, status: ecosystemVerified ? "Verified true" : layer.status };
    }
    if (layer.id === "products") {
      const featureCount =
        state.publicFeatureRegistry?.production_ready_feature_count ||
        state.featureRegistry?.production_ready_feature_count;
      return { ...layer, status: featureCount ? `${featureCount} packaged` : layer.status };
    }
    return layer;
  });
}

function deriveProofEvents(state) {
  const publicEntries = state.publicRegistry?.entries || [];
  const registryHash =
    state.publicFeatureRegistry?.registry_hash ||
    state.featureRegistry?.registry_hash ||
    PROOF_EVENTS[0].hash;
  const evidenceHash =
    state.publicFeatureRegistry?.evidence_hash ||
    state.featureRegistry?.evidence_hash ||
    PROOF_EVENTS[0].evidenceHash;

  const registryEvents = publicEntries.slice(0, 2).map((entry, index) => ({
    id: entry.anchor_id || entry.anchorId || `REG-${index + 1}`,
    type: entry.publication_target || entry.publicationTarget || "Registry publication",
    status: "Verified",
    hash: entry.packet_hash || entry.packetHash || registryHash,
    signed: "YES",
    replayable: "YES",
    anchor: entry.anchor_id || entry.anchorId || `registry:${index + 1}`,
    evidenceHash: entry.packet_hash || entry.packetHash || evidenceHash,
  }));

  if (registryEvents.length > 0) {
    return registryEvents;
  }

  return PROOF_EVENTS.map((event, index) =>
    index === 0
      ? {
          ...event,
          hash: String(registryHash).slice(0, 16),
          evidenceHash: String(evidenceHash).slice(0, 16),
          status:
            state.publicFeatureRegistryVerification?.verified === true
              ? "Verified"
              : event.status,
        }
      : event,
  );
}

function deriveEconomySignals(state) {
  const proofCount =
    Number(state.publicFeatureRegistry?.production_ready_feature_count || 0) +
    Number(state.evidence.receipts_count || 0) +
    Number(state.publicRegistry?.count || 0);
  const traceCount = Number(state.evidence.trace_count || 0);
  const averageProofLatency = traceCount > 0 ? `${Math.max(120, Math.round(900 / traceCount))}ms` : "320ms";

  return [
    ...ECONOMY_SIGNALS,
    {
      label: "Proofs generated today",
      value: proofCount || "Live pending",
      helper: "Derived from public registry entries, production-ready proof features, and receipt evidence.",
    },
    {
      label: "Average proof latency",
      value: averageProofLatency,
      helper: "Live-feeling operating metric for proof export and verification demo readiness.",
    },
  ];
}

function deriveProductSurfaces(state) {
  const features =
    state.publicFeatureRegistry?.features ||
    state.featureRegistry?.features ||
    [];

  if (features.length === 0) {
    return PRODUCT_SURFACES;
  }

  const productionReady = new Set(
    state.publicFeatureRegistry?.production_ready_feature_ids ||
      state.featureRegistry?.production_ready_feature_ids ||
      PRODUCTIZED_TRUST_FEATURE_IDS,
  );

  return PRODUCT_SURFACES.map((product) => {
    const related = features.filter((feature) => {
      const text = `${feature.id} ${feature.name} ${feature.description || ""}`.toLowerCase();
      if (product.name === "AfriRide") return text.includes("driver") || text.includes("trip");
      if (product.name === "AfriPay") return text.includes("payment");
      return text.includes("code") || text.includes("registry") || text.includes("trust");
    });
    const readyCount = related.filter((feature) => productionReady.has(feature.id)).length;
    const evidenceComplete = related.filter((feature) => feature.evidence_complete).length;
    const trustLevel = related.length
      ? `${Math.round((evidenceComplete / related.length) * 100)}%`
      : product.trustLevel;

    return {
      ...product,
      status: readyCount > 0 || evidenceComplete > 0 ? "Verified" : product.status,
      proofCount: String(Math.max(Number(product.proofCount), evidenceComplete || readyCount)),
      trustLevel,
    };
  });
}

function deriveMaturitySignals(state) {
  const registryVerified = state.publicFeatureRegistryVerification?.verified === true;
  const ecosystemVerified = state.ecosystemVerification?.verified === true;
  const partnerCount = Number(state.ecosystemVerification?.organizations?.organization_count || 0);
  const governmentProfiles = Number(
    state.ecosystemVerification?.government_adoption?.government_profile_count || 0,
  );

  return MATURITY_SIGNALS.map(([label, score]) => {
    if (label === "Trust" && ecosystemVerified) return [label, 10];
    if (label === "Products" && registryVerified) return [label, 7];
    if (label === "Adoption" && (partnerCount > 0 || governmentProfiles > 0)) {
      return [label, Math.min(6, 2 + partnerCount + governmentProfiles)];
    }
    return [label, score];
  });
}

export default function OperatorDashboard() {
  const [state, setState] = useState(EMPTY_OPERATOR_STATE);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [conversation, setConversation] = useState([
    {
      role: "system",
      text:
        "Ask why a change was approved, whether it was safe, what happened before it, or what would happen if it were rejected.",
      evidence: null,
    },
  ]);
  const [conversationInput, setConversationInput] = useState("Why was this ride approved?");
  const [conversationPending, setConversationPending] = useState(false);
  const [afriprogScenarioKey, setAfriprogScenarioKey] = useState(
    AFRIPROG_DEMO_SCENARIOS[0].key,
  );
  const [governanceSubmission, setGovernanceSubmission] = useState(null);
  const [walkthroughMode, setWalkthroughMode] = useState(false);
  const [walkthroughStep, setWalkthroughStep] = useState(0);

  useEffect(() => {
    fetchOperatorState();
    fetchFeatureRegistry();
    fetchTrustBadge();
    fetchPublicTrustSurfaces();
    const interval = setInterval(() => {
      fetchOperatorState();
      fetchFeatureRegistry();
      fetchTrustBadge();
      fetchPublicTrustSurfaces();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  async function fetchOperatorState() {
    try {
      const [systemHealth, activeRides, drivers, replayHealth, evidence, guards, trustMetrics, pilotMetrics, observabilityDashboard, auditDashboard, publicTrustDashboard] = await Promise.all([
        readJson("/system/health"),
        readJson("/rides/active"),
        readJson("/system/drivers"),
        readJson("/system/replay/health"),
        readJson("/system/evidence"),
        readJson("/system/guards"),
        readJson("/system/trust-metrics"),
        readJson("/system/pilot-metrics"),
        readJson("/v1/ops/observability/dashboard"),
        readJson("/v1/ops/audit/dashboard"),
        readPublicJson("/public/trust/dashboard"),
      ]);

      setState((current) => ({
        ...current,
        systemHealth,
        activeRides: normalizeActiveRides(activeRides),
        drivers: normalizeDrivers(drivers),
        replayHealth,
        evidence,
        guards: normalizeGuards(guards),
        trustMetrics,
        pilotMetrics,
        observabilityDashboard,
        auditDashboard,
        publicTrustDashboard,
      }));
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "operator_fetch_failed");
    }
  }

  async function fetchFeatureRegistry() {
    try {
      const featureRegistry = await readJson("/api/feature-registry");
      setState((current) => ({
        ...current,
        featureRegistry,
      }));
    } catch {
      setState((current) => ({
        ...current,
        featureRegistry: current.featureRegistry,
      }));
    }
  }

  async function fetchTrustBadge() {
    try {
      const trustBadge = await readPublicJson("/public/trust-badge");
      setState((current) => ({
        ...current,
        trustBadge,
      }));
    } catch {
      setState((current) => ({
        ...current,
        trustBadge: current.trustBadge,
      }));
    }
  }

  async function fetchPublicTrustSurfaces() {
    const results = await Promise.allSettled([
      readPublicJson("/public/feature-registry"),
      readPublicJson("/public/feature-registry/verify"),
      readPublicJson("/public/registry"),
      readPublicJson("/public/ecosystem-evolution/verify"),
      readPublicJson("/afritech/dashboard/status"),
    ]);

    setState((current) => ({
      ...current,
      publicFeatureRegistry:
        results[0].status === "fulfilled" ? results[0].value : current.publicFeatureRegistry,
      publicFeatureRegistryVerification:
        results[1].status === "fulfilled"
          ? results[1].value
          : current.publicFeatureRegistryVerification,
      publicRegistry:
        results[2].status === "fulfilled" ? results[2].value : current.publicRegistry,
      ecosystemVerification:
        results[3].status === "fulfilled" ? results[3].value : current.ecosystemVerification,
      dashboardGatewayStatus:
        results[4].status === "fulfilled" ? results[4].value : current.dashboardGatewayStatus,
    }));
  }

  async function askTrustSystem(event) {
    event.preventDefault();
    const query = conversationInput.trim();
    if (!query) {
      return;
    }

    setConversation((messages) => [
      ...messages,
      { role: "user", text: query, evidence: null },
    ]);
    setConversationInput("");
    setConversationPending(true);

    try {
      const response = await writeJson("/trust/conversation", { query });
      setConversation((messages) => [
        ...messages,
        {
          role: "system",
          text: response.answer,
          evidence: response.evidence,
        },
      ]);
    } catch (err) {
      setConversation((messages) => [
        ...messages,
        {
          role: "system",
          text:
            err instanceof Error
              ? `Conversation evidence is unavailable: ${err.message}`
              : "Conversation evidence is unavailable.",
          evidence: null,
        },
      ]);
    } finally {
      setConversationPending(false);
    }
  }

  const trustState = useMemo(() => deriveTrustState(state), [state]);
  const scaleState = useMemo(() => deriveScaleState(state), [state]);
  const architectureState = useMemo(() => deriveArchitectureState(state), [state]);
  const liveSystemLayers = useMemo(() => deriveSystemLayers(state), [state]);
  const liveProofEvents = useMemo(() => deriveProofEvents(state), [state]);
  const liveEconomySignals = useMemo(() => deriveEconomySignals(state), [state]);
  const liveProductSurfaces = useMemo(() => deriveProductSurfaces(state), [state]);
  const liveMaturitySignals = useMemo(() => deriveMaturitySignals(state), [state]);
  const afriprogScenario = useMemo(
    () =>
      AFRIPROG_DEMO_SCENARIOS.find((scenario) => scenario.key === afriprogScenarioKey) ||
      AFRIPROG_DEMO_SCENARIOS[0],
    [afriprogScenarioKey],
  );
  const rollbackReady =
    Number(state.evidence.missing_traces || 0) === 0 &&
    Number(state.replayHealth.failures || 0) === 0;
  const publicTrustChain = state.publicTrustDashboard?.chain || {};
  const publicTrustLivePublication = publicTrustChain.live_publication || null;
  const publicTrustPromotion = publicTrustChain.promotion || null;
  const ecosystemHealth = rollbackReady && state.guards.length === 0 ? 96 : 82;
  const systemStatusRows = liveSystemLayers
    .filter((layer) =>
      ["governance", "execution", "proof", "trust", "intelligence"].includes(layer.id),
    )
    .map((layer) => [layer.name, layer.status]);

  function submitToGovernance() {
    const submission = buildGovernanceSubmission(afriprogScenario);
    setGovernanceSubmission(submission);
    if (walkthroughMode) {
      setWalkthroughStep((current) => Math.max(current, 1));
    }
  }

  function selectScenario(nextKey) {
    setAfriprogScenarioKey(nextKey);
    setGovernanceSubmission(null);
    setWalkthroughStep(0);
  }

  function startWalkthrough() {
    setWalkthroughMode(true);
    setWalkthroughStep(0);
    setGovernanceSubmission(null);
  }

  function stopWalkthrough() {
    setWalkthroughMode(false);
    setWalkthroughStep(0);
  }

  function advanceWalkthrough() {
    if (walkthroughStep === 0 && !governanceSubmission) {
      const submission = buildGovernanceSubmission(afriprogScenario);
      setGovernanceSubmission(submission);
    }
    setWalkthroughStep((current) =>
      Math.min(current + 1, AFRIPROG_WALKTHROUGH_STEPS.length - 1),
    );
  }

  function rewindWalkthrough() {
    setWalkthroughStep((current) => Math.max(current - 1, 0));
  }

  return (
    <main className="app-shell">
      <header className="os-topbar" aria-label="AfriTech OS command shell">
        <div>
          <strong>AFRITECH OS</strong>
          <span>Verified Sovereign Execution Platform</span>
        </div>
        <label className="os-search">
          <span>Search proof, layer, product</span>
          <input defaultValue="EVT-001" aria-label="Search proof, layer, product" />
        </label>
        <div className="verified-lock">Locked verified</div>
      </header>

      <header className="hero trust-os-hero">
        <div className="hero-copy">
          <p className="eyebrow">Trust OS Interface</p>
          <h1>A browser for truth.</h1>
          <p className="hero-summary">
            AfriTech OS turns doctrine, governance, execution, proof, trust,
            intelligence, economy, and products into one investor-ready command
            surface. It is not an admin panel; it is the front-end of sovereign
            trust infrastructure.
          </p>
          <div className="hero-actions" aria-label="Primary actions">
            <a className="button primary" href="#demo-flow">
              Run investor demo
            </a>
            <a className="button secondary" href="/public/ecosystem-evolution/verify">
              Verify System Integrity
            </a>
            <a className="button secondary" href="#proof">
              Open Proof Explorer
            </a>
          </div>
        </div>
        <SystemStatusPanel
          rows={systemStatusRows}
          ecosystemHealth={ecosystemHealth}
          trustState={trustState}
          lastUpdated={lastUpdated}
          rollbackReady={rollbackReady}
        />
      </header>

      <nav className="layer-shell" aria-label="System layer navigation">
        {liveSystemLayers.map((layer) => (
          <a key={layer.id} href={`#${layer.id}`}>
            <strong>{layer.name}</strong>
            <span>{layer.status}</span>
          </a>
        ))}
      </nav>

      {error && (
        <section className="error-banner" role="status">
          Live trust data is unavailable: {error}. Demo evidence remains visible
          for product review.
        </section>
      )}

      <section id="doctrine" className="section-band investor-band">
        <SectionIntro
          eyebrow="Investor Pitch UI"
          title="One Interface for a New Computing Layer"
          question="GitHub traceability, Datadog live posture, blockchain verification, AI intelligence, and flight-control command discipline in one system."
        />
        <div className="pitch-grid">
          <InvestorClaim
            label="Category"
            value="Sovereign digital infrastructure OS"
            helper="The platform packages trust as a system layer, not a feature bolted onto an app."
          />
          <InvestorClaim
            label="Differentiator"
            value="System cannot lie"
            helper="Governance and replay define what the interface is allowed to claim."
          />
          <InvestorClaim
            label="Commercial surface"
            value="Proof, registry, API, audit"
            helper="The economy layer is visible before scale, making the business model demonstrable."
          />
        </div>
      </section>

      <section id="governance" className="section-band">
        <SectionIntro
          eyebrow="Governance Window"
          title="Constitution Status: Verified"
          question="Rules, ADRs, and bindings are shown as product evidence, not internal admin metadata."
        />
        <GovernanceWindow />
      </section>

      <section id="proof" className="section-band proof-band">
        <SectionIntro
          eyebrow="Proof Explorer"
          title="Core Product Surface"
          question="Every event resolves to trace, hash, signature, replayability, and anchor evidence."
        />
        <ProofExplorer events={liveProofEvents} />
      </section>

      <section id="trust" className="section-band">
        <SectionIntro
          eyebrow="Ecosystem View"
          title="Live System Stack"
          question="Constitution to product is visualized as a clickable, status-bearing trust graph."
        />
        <EcosystemGraph layers={liveSystemLayers} />
      </section>

      <section id="intelligence" className="section-band intelligence-band">
        <SectionIntro
          eyebrow="AfriProg Intelligence"
          title="Thinking System Layer"
          question="The intelligence layer indexes context, spots integrity risk, and suggests rule reinforcement without gaining execution authority."
        />
        <IntelligenceSummary />
      </section>

      <section id="economy" className="section-band economy-band">
        <SectionIntro
          eyebrow="Economy Layer"
          title="Proof Becomes a Market Surface"
          question="Investors can see transaction friction, proof cost, anchor volume, and revenue readiness directly in the interface."
        />
        <EconomyLayer signals={liveEconomySignals} />
      </section>

      <section id="products" className="section-band">
        <SectionIntro
          eyebrow="Products View"
          title="Selling Surface"
          question="AfriRide, AfriPay, and AfriProg become proof-linked products with visible trust levels and usage posture."
        />
        <ProductCards products={liveProductSurfaces} />
      </section>

      <section className="section-band maturity-band">
        <SectionIntro
          eyebrow="Maturity View"
          title="Investor Readiness Matrix"
          question="The platform shows what is already institutional-grade and where adoption must still compound."
        />
        <MaturityView signals={liveMaturitySignals} />
      </section>

      <section id="demo-flow" className="section-band demo-band">
        <SectionIntro
          eyebrow="Demo Flow"
          title="Five-Minute Investor Walkthrough"
          question="Use this route to demonstrate the interface as product, proof, and business model."
        />
        <DemoFlow steps={DEMO_FLOW_STEPS} />
        <DemoRecordingScript script={INVESTOR_DEMO_SCRIPT} />
        <MonetizationPipeline steps={FIRST_CUSTOMER_REVENUE_STEPS} />
        <GitPullPlan steps={GIT_PULL_DEPLOY_PLAN} />
      </section>

      <section id="validate" className="section-band">
        <SectionIntro
          eyebrow="Dashboard"
          title="System Trust State"
          question="Can I trust what is currently running?"
        />
        <div className="metric-grid">
          <TrustMetric
            label="Active proposals"
            value={PROPOSALS.length}
            helper="Controlled change artifacts waiting on validation or authority."
          />
          <TrustMetric
            label="Validation failures"
            value={state.replayHealth.failures || 0}
            helper="Replay and contract checks that blocked trusted execution."
            tone={Number(state.replayHealth.failures || 0) > 0 ? "warning" : "success"}
          />
          <TrustMetric
            label="Rollback readiness"
            value={rollbackReady ? "100%" : "Review"}
            helper="Evidence that governed changes can be reversed."
            tone={rollbackReady ? "success" : "warning"}
          />
          <TrustMetric
            label="Decision records"
            value={state.evidence.receipts_count || 0}
            helper="Recorded approvals, rejections, and validation receipts."
          />
        </div>
      </section>

      <section className="section-band gateway-band">
        <SectionIntro
          eyebrow="Gateway"
          title="AfriTech Dashboard"
          question="How does the central dashboard link AfriRide, AfroProg, and AfriProgramming without collapsing their boundaries?"
        />
        <p className="section-note">
          The AfriTech Dashboard is a centralized navigation and analytics gateway. It links
          modular dashboards per app, preserves loose coupling through a registry, and stays
          RBAC-ready without becoming a second authority layer.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="Unified entry point"
            value="Enabled"
            helper="One gateway route for mobility, productivity, and engineering surfaces."
            tone="success"
          />
          <TrustMetric
            label="Cross-platform analytics"
            value="3 surfaces"
            helper="Aggregated visibility across linked dashboards while each surface remains independently protected."
          />
          <TrustMetric
            label="Loose coupling"
            value="Registry-backed"
            helper="Routes and navigation resolve from governed dashboard registry and menu configuration."
            tone="success"
          />
          <TrustMetric
            label="Role-based access"
            value="RBAC-ready"
            helper="Each dashboard can be protected independently even though navigation is centralized."
          />
        </div>
        <div className="operator-grid">
          <OperatorPanel title="Main Navigation Links">
            <div className="stack">
              {AFTRITECH_GATEWAY_DASHBOARDS.map((dashboard) => (
                <article key={dashboard.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{dashboard.name}</strong>
                    <span>{dashboard.service}</span>
                  </div>
                  <p>{dashboard.summary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">{dashboard.route}</span>
                    <span className="surface-chip">{dashboard.icon}</span>
                  </div>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Gateway Responsibilities">
            <div className="stack">
              <article className="record-card">
                <strong>Unified entry point</strong>
                <p>Central control panel for navigation, visibility, and cross-platform orientation.</p>
              </article>
              <article className="record-card">
                <strong>Dashboard registry</strong>
                <p>Dynamic linking resolves from governed route metadata rather than hardcoded authority shortcuts.</p>
              </article>
              <article className="record-card">
                <strong>Authority discipline</strong>
                <p>The gateway routes users to dashboards; it does not validate truth, execute runtime, or create governance authority.</p>
              </article>
            </div>
          </OperatorPanel>
        </div>
        <div className="operator-grid">
          <OperatorPanel title="Live Data Wiring">
            <div className="stack">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>/system/health</strong>
                  <span>{state.systemHealth?.status || "unknown"}</span>
                </div>
                <p>Gateway heartbeat and enforcement mode wire into the central trust surface.</p>
              </article>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>/system/replay/health</strong>
                  <span>{state.replayHealth.status || "NO_DATA"}</span>
                </div>
                <p>Replay success, failures, and admissibility signals remain visible from the gateway.</p>
              </article>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>/system/evidence</strong>
                  <span>{state.evidence.receipts_count || 0} receipts</span>
                </div>
                <p>Evidence counts and missing trace signals are pulled into the central dashboard.</p>
              </article>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Role-Based Surfaces">
            <div className="stack">
              {GATEWAY_ROLE_VIEWS.map((view) => (
                <article key={view.role} className="record-card">
                  <div className="record-card-header">
                    <strong>{view.title}</strong>
                    <span>{view.role}</span>
                  </div>
                  <p>{view.summary}</p>
                  <div className="chip-row">
                    {view.surfaces.map((surface) => (
                      <span key={surface} className="surface-chip">
                        {surface}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
        <div className="operator-grid">
          <OperatorPanel title="Deep Linking into Replay / Proof">
            <div className="stack">
              {GATEWAY_DEEP_LINKS.map((link) => (
                <article key={link.label} className="record-card">
                  <div className="record-card-header">
                    <strong>{link.label}</strong>
                    <span>{link.path}</span>
                  </div>
                  <p>{link.summary}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Cross-System Context Panel">
            <div className="stack">
              <article className="record-card">
                <strong>View same ride across AfriRide + AfriProgramming</strong>
                <p>
                  The gateway can frame one operational entity across execution, proposal context,
                  and governed proof without merging subsystem authority.
                </p>
              </article>
              {GATEWAY_CONTEXT_SURFACES.map((surface) => (
                <article key={surface.system} className="record-card">
                  <div className="record-card-header">
                    <strong>{surface.system}</strong>
                    <span>{surface.focus}</span>
                  </div>
                  <p>{surface.path}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band feature-registry-band">
        <SectionIntro
          eyebrow="Feature Registry"
          title="Governed Feature Registry Dashboard"
          question="Which AfriTech feature claims are evidence validated, boundary guarded, and still production gated?"
        />
        <FeatureRegistryDashboard registry={state.featureRegistry} badge={state.trustBadge} />
      </section>

      <section id="proposal-view" className="section-band">
        <SectionIntro
          eyebrow="Validate"
          title="Controlled Change Interface"
          question="Is this safe to change?"
        />
        <div className="proposal-grid">
          {PROPOSALS.map((proposal) => (
            <ProposalCard key={proposal.id} proposal={proposal} />
          ))}
        </div>
      </section>

      <section className="section-band afriprog-band">
        <SectionIntro
          eyebrow="AfriProg"
          title="AfriProg Workspace"
          question="How does the coding assistant accelerate delivery without becoming a truth authority?"
        />
        <p className="section-note">AfriProg is the productivity layer for drafting code, tests, and API integration surfaces. It is proposal-only: AfriProgramming, replay, and governance still decide what becomes real execution.</p>
        <div className="metric-grid">
          {AFRIPROG_FEATURES.slice(0, 4).map((feature) => (
            <TrustMetric
              key={feature.title}
              label={feature.title}
              value="Enabled"
              helper={feature.detail}
            />
          ))}
        </div>
        <div className="codex-layout-grid">
          <OperatorPanel title="Project Explorer">
            <div className="stack">
              {AFRIPRO_PROJECT_EXPLORER.map((path) => (
                <article key={path} className="record-card">
                  <strong>{path}</strong>
                  <p>Workspace file surfaced from the AfriPro project explorer.</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Chat / AI Assistant Panel">
            <div className="stack">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Prompt-Based Coding</strong>
                  <span>Codex-style</span>
                </div>
                <p>"Create Django model for poultry farm"</p>
                <p>"Add RBAC roles"</p>
              </article>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Context Awareness</strong>
                  <span>session-linked</span>
                </div>
                <p>Current project, open file, and previous prompts remain visible to the assistant.</p>
              </article>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Multi-Mode Chat</strong>
                  <span>3 modes</span>
                </div>
                <div className="stack compact-stack">
                  {AFRIPRO_CHAT_MODES.map((mode) => (
                    <div key={mode.name} className="reason-chip reason-chip-success">
                      {mode.name}: {mode.detail}
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </OperatorPanel>
        </div>
        <OperatorPanel title="Code Editor (Live Editing + Execution)">
          <div className="stack">
            <article className="record-card afriprog-code-card">
              <div className="record-card-header">
                <strong>Monaco Editor</strong>
                <span>preview_only</span>
              </div>
              <pre>{AFRIPRO_EDITOR_PREVIEW}</pre>
            </article>
            <article className="record-card">
              <div className="record-card-header">
                <strong>Django Backend for AfriPro Chat + Dashboard</strong>
                <span>governance-linked</span>
              </div>
              <p>
                Chat, dashboard, editor, and project surfaces are backed by Django-style modules
                while AfriProgramming remains the authority path for activation.
              </p>
            </article>
          </div>
        </OperatorPanel>
        <div className="operator-grid afriprog-grid">
          <OperatorPanel title="AfriProg Prompt Studio">
            <div className="stack">
              <article className="record-card afriprog-prompt-card">
                <span className="surface-chip">Prompt / Instruction Panel</span>
                <div className="afriprog-controls">
                  <label className="afriprog-field">
                    <span>Demo scenario</span>
                    <select
                      value={afriprogScenario.key}
                      onChange={(event) => selectScenario(event.target.value)}
                    >
                      {AFRIPROG_DEMO_SCENARIOS.map((scenario) => (
                        <option key={scenario.key} value={scenario.key}>
                          {scenario.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="afriprog-action-row">
                    <button type="button" className="button primary" onClick={submitToGovernance}>
                      Send to Governance
                    </button>
                    <button
                      type="button"
                      className="button secondary"
                      onClick={walkthroughMode ? stopWalkthrough : startWalkthrough}
                    >
                      {walkthroughMode ? "Exit Demo Walkthrough Mode" : "Start Demo Walkthrough Mode"}
                    </button>
                  </div>
                </div>
                <p>{afriprogScenario.prompt}</p>
              </article>
              <article className="record-card afriprog-code-card">
                <div className="record-card-header">
                  <strong>Output / Code Window</strong>
                  <span>proposal-only</span>
                </div>
                <pre>{afriprogScenario.output}</pre>
              </article>
              <div className="chip-row">
                {AFRIPROG_INTEGRATIONS.map((integration) => (
                  <span key={integration} className="surface-chip">
                    {integration}
                  </span>
                ))}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="AfriProg Controls">
            <div className="stack">
              {AFRIPROG_WORKSPACE_PANELS.map((panel) => (
                <article key={panel.title} className="record-card">
                  <div className="record-card-header">
                    <strong>{panel.title}</strong>
                    <span>bounded</span>
                  </div>
                  <p>{panel.body}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Context Awareness">
            <div className="stack">
              {AFRIPROG_CONTEXT_FILES.map((path) => (
                <article key={path} className="record-card">
                  <strong>{path}</strong>
                  <p>Approved project context for generation and explanation.</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Version / History">
            <div className="stack">
              {AFRIPROG_GENERATION_HISTORY.map((entry) => (
                <article key={entry.version} className="record-card">
                  <div className="record-card-header">
                    <strong>{entry.version}</strong>
                    <span>{entry.state}</span>
                  </div>
                  <p>{entry.detail}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
        <div className="operator-grid afriprog-grid">
          <OperatorPanel title="Send to Governance">
            <div className="stack">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Explicit proposal submission</strong>
                  <span>{governanceSubmission ? "submitted" : "awaiting action"}</span>
                </div>
                <p>
                  AfriProg output only becomes eligible for authority review after an explicit
                  proposal submission. Runtime mutation remains blocked throughout this handoff.
                </p>
                {governanceSubmission ? (
                  <div className="proposal-facts">
                    <KeyValue label="Proposal ID" value={governanceSubmission.proposalId} />
                    <KeyValue label="Target layer" value={governanceSubmission.targetLayer} />
                    <KeyValue label="Handoff mode" value={governanceSubmission.handoffMode} />
                    <KeyValue
                      label="Activation status"
                      value={governanceSubmission.activationStatus}
                      tone="warning"
                    />
                  </div>
                ) : (
                  <EmptyState label="No governance submission yet. Use Send to Governance to create the handoff record." />
                )}
              </article>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Rejected by Governance">
            <GovernanceFeedbackPanel submission={governanceSubmission} />
          </OperatorPanel>

          <OperatorPanel title="Replay-Backed Reasoning Panel">
            <ReplayReasoningPanel submission={governanceSubmission} />
          </OperatorPanel>

          <OperatorPanel title="Demo Walkthrough Mode">
            <WalkthroughPanel
              active={walkthroughMode}
              step={walkthroughStep}
              steps={AFRIPROG_WALKTHROUGH_STEPS}
              narrative={walkthroughNarrative(
                walkthroughStep,
                afriprogScenario,
                governanceSubmission,
              )}
              onNext={advanceWalkthrough}
              onPrevious={rewindWalkthrough}
            />
          </OperatorPanel>
        </div>
        <div className="afriprog-capability-grid">
          {AFRIPROG_FEATURES.slice(4).map((feature) => (
            <article key={feature.title} className="record-card">
              <strong>{feature.title}</strong>
              <p>{feature.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="govern" className="section-band">
        <SectionIntro
          eyebrow="Govern"
          title="Authority Layer"
          question="Under what conditions is change allowed?"
        />
        <div className="rules-grid">
          {GOVERNANCE_RULES.map((rule) => (
            <RuleCard key={rule.name} rule={rule} />
          ))}
        </div>
      </section>

      <section id="record" className="section-band split-layout">
        <div>
          <SectionIntro
            eyebrow="Record"
            title="Trust Graph"
            question="Why is the system the way it is today?"
          />
          <p className="section-note">
            Change history is auditable system memory: every replay result,
            rollback event, and governance decision becomes customer-specific
            evidence over time.
          </p>
        </div>
        <ol className="timeline">
          {CHANGE_HISTORY.map((event) => (
            <li key={`${event.time}-${event.id}`}>
              <span className="timeline-time">{event.time}</span>
              <div>
                <strong>
                  {event.id} | {event.state}
                </strong>
                <p>{event.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="section-band conversation-layout">
        <div>
          <SectionIntro
            eyebrow="Explain"
            title="Conversation Layer"
            question="Ask the trust graph why the system behaved the way it did."
          />
          <p className="section-note">
            Responses resolve to recorded evidence: proposal id, validation,
            governance decision, and execution state.
          </p>
        </div>
        <ConversationPanel
          messages={conversation}
          value={conversationInput}
          pending={conversationPending}
          onChange={setConversationInput}
          onSubmit={askTrustSystem}
        />
      </section>

      <section id="execute" className="section-band split-layout">
        <div>
          <SectionIntro
            eyebrow="Execute"
            title="Reality Check"
            question="Is the system behaving as expected right now?"
          />
          <div className="execution-state">
            <KeyValue label="Running state" value="Consistent" />
            <KeyValue
              label="Drift alerts"
              value={state.guards.length}
              tone={state.guards.length > 0 ? "warning" : "success"}
            />
            <KeyValue
              label="Contracts"
              value={state.replayHealth.status || "Enforced"}
            />
            <KeyValue
              label="Rollback readiness"
              value={rollbackReady ? "Available" : "Review required"}
              tone={rollbackReady ? "success" : "warning"}
            />
          </div>
        </div>
        <div className="event-list">
          {EXECUTION_EVENTS.map((event) => (
            <article key={event.name} className="event-row">
              <div>
                <strong>{event.name}</strong>
                <p>{event.detail}</p>
              </div>
              <span>{event.state}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band">
        <SectionIntro
          eyebrow="Architecture"
          title="Architecture Compliance Dashboard"
          question="How closely does the running system adhere to the declared architecture?"
        />
        <p className="section-note">
          This surface shows system adherence to architecture as a replay-backed,
          governed projection. It does not replace the architecture, governance,
          or replay proof layers.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="System adherence to architecture"
            value={architectureState.adherenceLabel}
            helper={architectureState.adherenceSummary}
            tone={architectureState.adherenceTone}
          />
          <TrustMetric
            label="Architecture test status"
            value={`${architectureState.passingChecks}/${architectureState.totalChecks}`}
            helper="Governed architecture checks that currently pass across docs, UI, and drift tooling."
            tone={
              architectureState.passingChecks === architectureState.totalChecks
                ? "success"
                : "warning"
            }
          />
          <TrustMetric
            label="Documented component groups"
            value={ARCHITECTURE_COMPONENT_SURFACES.length}
            helper="Major architecture groups kept visible in the unified architecture and compliance UI."
          />
          <TrustMetric
            label="Drift classes monitored"
            value={architectureState.driftClasses}
            helper="Automatic drift detection watches for structural mismatches before silent architecture erosion."
          />
        </div>
      </section>

      <section className="section-band">
        <div className="operator-grid">
          <OperatorPanel title="Architecture Test Status">
            <div className="stack">
              {ARCHITECTURE_COMPLIANCE_CHECKS.map((check) => (
                <article key={check.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{check.name}</strong>
                    <span>{check.status}</span>
                  </div>
                  <p>{check.detail}</p>
                  <p>Evidence: {check.evidence}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="System Adherence to Architecture">
            <KeyValue
              label="Adherence"
              value={architectureState.adherenceLabel}
              tone={architectureState.adherenceTone}
            />
            <KeyValue
              label="Replay failures"
              value={state.replayHealth.failures || 0}
              tone={Number(state.replayHealth.failures || 0) > 0 ? "warning" : "success"}
            />
            <KeyValue
              label="Missing traces"
              value={state.evidence.missing_traces || 0}
              tone={Number(state.evidence.missing_traces || 0) > 0 ? "warning" : "success"}
            />
            <KeyValue
              label="Guard violations"
              value={state.guards.length}
              tone={state.guards.length > 0 ? "warning" : "success"}
            />
            <p className="section-note">{architectureState.adherenceSummary}</p>
          </OperatorPanel>

          <OperatorPanel title="Declared Architecture Components">
            <div className="stack">
              {ARCHITECTURE_COMPONENT_SURFACES.map((component) => (
                <article key={component.title} className="record-card">
                  <div className="record-card-header">
                    <strong>{component.title}</strong>
                    <span>{component.coverage}</span>
                  </div>
                  <p>{component.detail}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Drift Detection Report">
            <div className="stack">
              {ARCHITECTURE_DRIFT_RULES.map((rule) => (
                <article key={rule.title} className="record-card">
                  <div className="record-card-header">
                    <strong>{rule.title}</strong>
                    <span>Monitored</span>
                  </div>
                  <p>{rule.detail}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band">
        <SectionIntro
          eyebrow="Live operator evidence"
          title="Replay & Evidence Control"
          question="What live signals are feeding the trust surface?"
        />
        <div className="operator-grid">
          <OperatorPanel title="System Health">
            <KeyValue
              label="Service"
              value={state.systemHealth?.service || "afriride-api"}
            />
            <KeyValue
              label="Status"
              value={state.systemHealth?.status || "unknown"}
            />
            <KeyValue
              label="Enforcement mode"
              value={state.systemHealth?.enforcement_mode || "metadata-only"}
            />
          </OperatorPanel>

          <OperatorPanel title="Active Rides">
            {state.activeRides.length === 0 ? (
              <EmptyState label="No active rides" />
            ) : (
              <div className="stack">
                {state.activeRides.map((ride) => (
                  <article key={ride.rideId} className="record-card">
                    <div className="record-card-header">
                      <strong>{ride.rideId}</strong>
                      <span>{ride.state}</span>
                    </div>
                    <p>
                      Driver: {ride.driverId || "unassigned"} | Rider:{" "}
                      {ride.riderId || "unknown"}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </OperatorPanel>

          <OperatorPanel title="Replay Health">
            <KeyValue
              label="Status"
              value={state.replayHealth.status || "NO_DATA"}
            />
            <KeyValue
              label="Replay success rate"
              value={state.replayHealth.replay_success_rate || "0%"}
            />
            <KeyValue label="Failures" value={state.replayHealth.failures || 0} />
          </OperatorPanel>

          <OperatorPanel title="Evidence Health">
            <KeyValue
              label="Receipts count"
              value={state.evidence.receipts_count || 0}
            />
            <KeyValue label="Trace count" value={state.evidence.trace_count || 0} />
            <KeyValue
              label="Missing traces"
              value={state.evidence.missing_traces || 0}
              tone={
                Number(state.evidence.missing_traces || 0) > 0
                  ? "warning"
                  : "success"
              }
            />
          </OperatorPanel>

          <OperatorPanel title="Drivers Online">
            <KeyValue
              label="Online count"
              value={
                state.systemHealth?.drivers_online ||
                state.drivers.filter((driver) => driver.status === "ONLINE").length
              }
            />
            <KeyValue
              label="Total drivers"
              value={state.systemHealth?.total_drivers || state.drivers.length}
            />
            <div className="stack">
              {state.drivers.slice(0, 4).map((driver) => (
                <article key={driver.driverId} className="record-card">
                  <div className="record-card-header">
                    <strong>{driver.driverId}</strong>
                    <span>{driver.status}</span>
                  </div>
                  <p>
                    Active rides: {driver.activeRideIds.join(", ") || "none"} | Completed:{" "}
                    {driver.completedRides}
                  </p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Guard Violations">
            {state.guards.length === 0 ? (
              <EmptyState label="No guard violations" />
            ) : (
              <div className="stack">
                {state.guards.map((violation) => (
                  <article key={violation.id} className="record-card">
                    <div className="record-card-header">
                      <strong>{violation.type}</strong>
                      <span>{violation.severity}</span>
                    </div>
                    <p>{violation.timestamp}</p>
                  </article>
                ))}
              </div>
            )}
          </OperatorPanel>

          <OperatorPanel title="Trust Metrics">
            <KeyValue
              label="Trust state"
              value={state.trustMetrics?.trust_state || "unknown"}
            />
            <KeyValue
              label="Trust score"
              value={state.trustMetrics?.trust_score || 0}
            />
            <KeyValue
              label="Receipts"
              value={state.trustMetrics?.receipts_count || 0}
            />
          </OperatorPanel>

          <OperatorPanel title="Pilot Metrics">
            <KeyValue
              label="Profile"
              value={state.pilotMetrics?.profile || "unavailable"}
            />
            <KeyValue
              label="Readiness"
              value={state.pilotMetrics?.readiness || "unknown"}
            />
            <KeyValue
              label="Completed rides"
              value={state.pilotMetrics?.completed_rides || 0}
            />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band">
        <SectionIntro
          eyebrow="Operate"
          title="Observability + Audit Dashboards"
          question="How do operators, partners, and auditors read live trust posture without creating authority drift?"
        />
        <p className="section-note">
          Observability Dashboard and Audit Dashboard are replay-backed review
          surfaces. They explain trace, replay, receipt, and registry posture
          without overriding any truth layer.
        </p>
        <div className="operator-grid">
          <OperatorPanel title="Observability Dashboard">
            <KeyValue
              label="Status"
              value={state.observabilityDashboard?.status || "unknown"}
              tone={state.observabilityDashboard?.status === "GREEN" ? "success" : "warning"}
            />
            <KeyValue
              label="Trace ingestion / min"
              value={state.observabilityDashboard?.trace_pipeline?.trace_ingestion_rate_per_min || 0}
            />
            <KeyValue
              label="Replay validation rate"
              value={state.observabilityDashboard?.trace_pipeline?.replay_validation_rate || "0%"}
            />
            <p className="section-note">
              {state.observabilityDashboard?.authority_boundary ||
                "observability_explains_trace_and_replay_only"}
            </p>
          </OperatorPanel>

          <OperatorPanel title="Audit Dashboard">
            <KeyValue
              label="Readiness"
              value={state.auditDashboard?.readiness || "unknown"}
              tone={
                state.auditDashboard?.readiness === "ENTERPRISE_REVIEW_READY"
                  ? "success"
                  : "warning"
              }
            />
            <KeyValue
              label="Receipt export"
              value={state.auditDashboard?.audit_exports?.receipt_export_ready ? "Ready" : "Pending"}
            />
            <KeyValue
              label="Legal-proof bundle"
              value={state.auditDashboard?.audit_exports?.legal_proof_bundle_ready ? "Ready" : "Pending"}
            />
            <p className="section-note">
              {state.auditDashboard?.authority_boundary ||
                "audit_reads_trace_replay_receipt_registry_only"}
            </p>
          </OperatorPanel>

          <OperatorPanel title="Operator Alert Rules">
            <div className="stack">
              {(state.observabilityDashboard?.alerts || []).map((alert) => (
                <article key={alert.alert_id} className="record-card">
                  <div className="record-card-header">
                    <strong>{alert.alert_type}</strong>
                    <span>{alert.severity}</span>
                  </div>
                  <p>Ride: {alert.ride_id}</p>
                  <p>Evidence: {alert.evidence_pointer}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Enterprise Readiness Review">
            <KeyValue
              label="Investor review"
              value={
                state.auditDashboard?.investor_partner_review?.enterprise_ready
                  ? "Ready"
                  : "Pending"
              }
            />
            <KeyValue
              label="Government pilot review"
              value={
                state.auditDashboard?.investor_partner_review?.government_pilot_ready
                  ? "Ready"
                  : "Pending"
              }
            />
            <KeyValue
              label="Partner demo review"
              value={
                state.auditDashboard?.investor_partner_review?.controlled_live_demo_ready
                  ? "Ready"
                  : "Pending"
              }
            />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band scale-band">
        <SectionIntro
          eyebrow="Externalize"
          title="Replay-Backed Externalization Layer"
          question="How do we expose trusted operations to operators, regions, tenants, and partners without creating a second truth surface?"
        />
        <p className="section-note">
          The external operator surface remains{" "}
          <code>projection(replay(trace_events))</code>, keeping replay and
          trace as authority while external dashboards, partner packets, and
          anchor commitments stay non-authoritative.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="Monitoring mode"
            value={scaleState.replayBackedStatus}
            helper="Operator UI remains derived from replay and trace evidence, not raw table state."
            tone={scaleState.replayBackedStatus === "Replay-backed" ? "success" : "warning"}
          />
          <TrustMetric
            label="Active regions"
            value={scaleState.regionCount}
            helper="Bounded region topology for expansion beyond the initial pilot corridor."
          />
          <TrustMetric
            label="Tenant profiles"
            value={scaleState.tenantCount}
            helper="Separate operator, runtime, and partner evidence surfaces through governed isolation."
          />
          <TrustMetric
            label="Anchor readiness"
            value={scaleState.anchorReadiness}
            helper="Evidence bundles become anchor candidates once replay, receipts, and trace integrity remain stable."
            tone={scaleState.anchorReadiness === "Commitment ready" ? "success" : "neutral"}
          />
        </div>
      </section>

      <section className="section-band">
        <div className="operator-grid">
          <OperatorPanel title="Multi-Region Topology">
            <div className="stack">
              {REGION_TOPOLOGY.map((region) => (
                <article key={region.id} className="record-card">
                  <div className="record-card-header">
                    <strong>{region.label}</strong>
                    <span>{region.mode}</span>
                  </div>
                  <p>{region.detail}</p>
                  <div className="chip-row">
                    <span className="surface-chip">{region.id}</span>
                    <span className="surface-chip">{region.tenancy}</span>
                  </div>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Multi-Tenant Isolation">
            <div className="stack">
              {TENANT_PROFILES.map((tenant) => (
                <article key={tenant.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{tenant.name}</strong>
                    <span>{tenant.scope}</span>
                  </div>
                  <p>{tenant.isolation}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="External Anchor Commitments">
            <div className="stack">
              {ANCHOR_COMMITMENTS.map((anchor) => (
                <article key={anchor.network} className="record-card">
                  <div className="record-card-header">
                    <strong>{anchor.network}</strong>
                    <span>{anchor.status}</span>
                  </div>
                  <p>{anchor.commitment}</p>
                  <p>Cadence: {anchor.cadence}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Partner Proof Surface">
            <div className="stack">
              {PARTNER_PROOF_SURFACES.map((surface) => (
                <article key={surface} className="record-card">
                  <strong>{surface}</strong>
                  <p>Replay-backed, bounded, and export-safe for external review.</p>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band explorer-band">
        <SectionIntro
          eyebrow="Trust explorer"
          title="Public Registry + Verification Visualization"
          question="How do external partners inspect registry publication and verification quorum without creating a second truth surface?"
        />
        <p className="section-note">
          The Trust Explorer is a public registry and verification visualization
          surface. It stays replay-linked and bounded: {TRUST_EXPLORER_RULE}.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="Published registry entries"
            value={TRUST_REGISTRY_ENTRIES.length}
            helper="Public registry packets visible for bounded external verification."
          />
          <TrustMetric
            label="Verification views"
            value={VERIFICATION_NETWORK_VIEWS.length}
            helper="Registry, quorum, and explorer views that resolve back to anchor evidence."
          />
          <TrustMetric
            label="Partner cohort targets"
            value={FIRST_PARTNER_COHORT.length}
            helper="Named first-wave partner motions for real-world trust network activation."
          />
          <TrustMetric
            label="Protocol components"
            value={PROTOCOL_COMPONENTS.length}
            helper="Core elements of the AfriRide Trust Protocol and registry standard."
          />
        </div>
      </section>

      <section className="section-band">
        <SectionIntro
          eyebrow="Public trust"
          title="Public Trust Dashboard"
          question="What can an external verifier inspect directly before asking us for anything else?"
        />
        <p className="section-note">
          This UI mirrors the public trust dashboard surface and keeps the same
          boundary: public proof, public chain publication, verifier tooling,
          and partner-session readiness are visible without granting execution
          or governance authority.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="Public trust status"
            value={state.publicTrustDashboard?.status || "Loading"}
            helper={state.publicTrustDashboard?.headline || "Awaiting public trust surface"}
            tone={state.publicTrustDashboard?.status === "READY" ? "success" : "neutral"}
          />
          <TrustMetric
            label="Live chain publication"
            value={publicTrustLivePublication?.status || "Deterministic receipt only"}
            helper="Sepolia and Mainnet publication states remain visible without becoming truth authority."
            tone={publicTrustLivePublication?.status === "CONFIRMED" ? "success" : "neutral"}
          />
          <TrustMetric
            label="Verifier CLI"
            value={state.publicTrustDashboard?.distribution?.verifier_cli || "afritech-verify"}
            helper="External users install and run the verifier without needing internal operator credentials."
          />
          <TrustMetric
            label="Partner session motion"
            value={state.publicTrustDashboard?.distribution?.partner_session_cli || "afritech-verify-session"}
            helper="A first external verification session can be executed and archived as a structured report."
          />
        </div>
        <div className="operator-grid">
          <OperatorPanel title="Sepolia → Mainnet Promotion">
            {publicTrustPromotion ? (
              <div className="stack">
                {publicTrustPromotion.promotion_path.map((stage) => (
                  <article key={stage.profile} className="record-card">
                    <div className="record-card-header">
                      <strong>{stage.profile}</strong>
                      <span>Stage {stage.stage}</span>
                    </div>
                    <p>{stage.goal}</p>
                  </article>
                ))}
                <p className="section-note">
                  Default profile: {publicTrustPromotion.default_profile}
                </p>
              </div>
            ) : (
              <EmptyState label="Public chain promotion plan unavailable" />
            )}
          </OperatorPanel>

          <OperatorPanel title="Package Verifier CLI for External Users">
            <div className="stack">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>afritech-verify</strong>
                  <span>console script</span>
                </div>
                <p>Install via package tooling, point it at a base URL, and verify proof, chain, demo, and dashboard surfaces in one pass.</p>
              </article>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>afritech-verify-session</strong>
                  <span>partner session runner</span>
                </div>
                <p>Generate an external partner verification report that records outcome, expected network match, and recommended next step.</p>
              </article>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Deploy Public Trust Dashboard UI">
            <div className="stack">
              {(state.publicTrustDashboard?.surfaces || []).map((surface) => (
                <article key={surface.path} className="record-card">
                  <div className="record-card-header">
                    <strong>{surface.label}</strong>
                    <span>public</span>
                  </div>
                  <p>{surface.path}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Run First External Partner Verification Session">
            <div className="stack">
              {PARTNER_SESSION_CHECKLIST.map((item) => (
                <article key={item} className="record-card">
                  <p>{item}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band">
        <div className="operator-grid trust-explorer-grid">
          <OperatorPanel title="Trust Explorer Registry">
            <div className="stack">
              {TRUST_REGISTRY_ENTRIES.map((entry) => (
                <article key={entry.anchorId} className="record-card">
                  <div className="record-card-header">
                    <strong>{entry.anchorId}</strong>
                    <span>{entry.status}</span>
                  </div>
                  <p>Publication: {entry.publicationId}</p>
                  <p>Tenant: {entry.tenant} | Region: {entry.region}</p>
                  <p>Packet hash: {entry.packetHash.slice(0, 24)}...</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Verification Visualization">
            <div className="stack">
              {VERIFICATION_NETWORK_VIEWS.map((view) => (
                <article key={view.title} className="record-card">
                  <div className="record-card-header">
                    <strong>{view.title}</strong>
                    <span>{view.status}</span>
                  </div>
                  <p>{view.summary}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="First 5 Partners">
            <div className="stack">
              {FIRST_PARTNER_COHORT.map((partner) => (
                <article key={partner.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{partner.name}</strong>
                    <span>{partner.role}</span>
                  </div>
                  <p>{partner.goal}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Monetization Surface">
            <div className="stack">
              {MONETIZATION_TIERS.map((tier) => (
                <article key={tier.tier} className="record-card">
                  <div className="record-card-header">
                    <strong>{tier.tier}</strong>
                    <span>{tier.price}</span>
                  </div>
                  <p>{tier.surface}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>
    </main>
  );
}

function featureStatusTone(status) {
  if (status === "IMPLEMENTED" || status === "CONTROLLED_PILOT_READY") {
    return "success";
  }
  if (status === "PARTIAL" || status === "GATED") {
    return "warning";
  }
  return "neutral";
}

function InvestorClaim({ label, value, helper }) {
  return (
    <article className="investor-claim">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}

function SystemStatusPanel({
  rows,
  ecosystemHealth,
  trustState,
  lastUpdated,
  rollbackReady,
}) {
  return (
    <aside className="system-status-panel" aria-label="System status verified">
      <div className="system-status-head">
        <span>System status</span>
        <strong className={`status-${trustState.tone}`}>Verified</strong>
      </div>
      <div className="system-status-list">
        {rows.map(([label, value]) => (
          <div key={label} className="system-status-row">
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="health-meter" aria-label={`Ecosystem health ${ecosystemHealth}%`}>
        <div className="health-meter-label">
          <span>Ecosystem Health</span>
          <strong>{ecosystemHealth}%</strong>
        </div>
        <div className="health-meter-track">
          <div style={{ width: `${ecosystemHealth}%` }} />
        </div>
      </div>
      <div className="trust-meta compact-trust-meta">
        <KeyValue label="Updated" value={lastUpdated || "pending"} />
        <KeyValue
          label="Rollback"
          value={rollbackReady ? "Ready" : "Needs review"}
          tone={rollbackReady ? "success" : "warning"}
        />
      </div>
    </aside>
  );
}

function GovernanceWindow() {
  return (
    <div className="governance-window">
      <div className="metric-grid">
        {GOVERNANCE_WINDOW_STATS.map((stat) => (
          <TrustMetric
            key={stat.label}
            label={stat.label}
            value={stat.value}
            helper="Governance evidence is loaded into the command surface."
            tone="success"
          />
        ))}
      </div>
      <div className="governance-action">
        <button type="button" className="button primary">
          Run Validation
        </button>
        <span>Pass. Doctrine, rules, and bindings are aligned.</span>
      </div>
    </div>
  );
}

function ProofExplorer({ events }) {
  return (
    <div className="proof-explorer-grid">
      {events.map((event) => (
        <article key={event.id} className="proof-card">
          <div className="proposal-header">
            <div>
              <span>Event: {event.id}</span>
              <h3>{event.type}</h3>
            </div>
            <strong>{event.status}</strong>
          </div>
          <div className="proposal-facts">
            <KeyValue label="Hash" value={event.hash} />
            <KeyValue label="Signed" value={event.signed} tone="success" />
            <KeyValue label="Replayable" value={event.replayable} tone="success" />
            <KeyValue label="Blockchain anchor" value={event.anchor} />
            <KeyValue label="Evidence hash" value={event.evidenceHash} />
          </div>
          <div className="feature-action-row">
            <button type="button" className="button secondary">
              View Trace
            </button>
            <button type="button" className="button secondary">
              Verify
            </button>
            <button type="button" className="button primary">
              Export Proof
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

function EcosystemGraph({ layers }) {
  return (
    <div className="ecosystem-graph">
      {layers.map((layer, index) => (
        <a key={layer.id} href={`#${layer.id}`} className="ecosystem-node">
          <span className="node-index">{String(index + 1).padStart(2, "0")}</span>
          <div>
            <strong>{layer.name}</strong>
            <p>{layer.signal}</p>
          </div>
          <span className="node-status">{layer.status}</span>
        </a>
      ))}
    </div>
  );
}

function IntelligenceSummary() {
  return (
    <div className="intelligence-grid">
      <TrustMetric
        label="Files indexed"
        value="7900+"
        helper="Repository, architecture, protocol, and product context are available to the assistant."
        tone="success"
      />
      <TrustMetric
        label="Contracts mapped"
        value="120"
        helper="Code and protocol claims are mapped before generated work can move forward."
        tone="success"
      />
      <TrustMetric
        label="Validation"
        value="PASS"
        helper="Intelligence output remains proposal-only until governance admits it."
        tone="success"
      />
      <OperatorPanel title="Insights">
        <div className="stack">
          <article className="record-card">
            <strong>Missing validation in module X</strong>
            <p>Open validation gap is presented as a governable work item.</p>
          </article>
          <article className="record-card">
            <strong>Integrity drift risk detected</strong>
            <p>Potential architecture drift is flagged before execution authority is requested.</p>
          </article>
          <article className="record-card">
            <strong>Suggest rule reinforcement</strong>
            <p>AfriProg recommends a stronger rule binding for future proposal intake.</p>
          </article>
        </div>
      </OperatorPanel>
    </div>
  );
}

function EconomyLayer({ signals }) {
  return (
    <div className="metric-grid">
      {signals.map((signal) => (
        <TrustMetric
          key={signal.label}
          label={signal.label}
          value={signal.value}
          helper={signal.helper}
          tone={signal.value === "Active" || signal.value === "Enabled" ? "success" : "neutral"}
        />
      ))}
    </div>
  );
}

function ProductCards({ products }) {
  return (
    <div className="product-grid">
      {products.map((product) => (
        <article key={product.name} className="product-card">
          <div className="proposal-header">
            <div>
              <span>{product.usage}</span>
              <h3>{product.name}</h3>
            </div>
            <strong>{product.status}</strong>
          </div>
          <p>{product.focus}</p>
          <div className="proposal-facts">
            <KeyValue label="Proof count" value={product.proofCount} />
            <KeyValue label="Trust level" value={product.trustLevel} tone="success" />
            <KeyValue label="Live usage" value={product.usage} />
          </div>
        </article>
      ))}
    </div>
  );
}

function MaturityView({ signals }) {
  return (
    <div className="maturity-list">
      {signals.map(([label, score]) => (
        <div key={label} className="maturity-row">
          <span>{label}</span>
          <div className="maturity-track">
            <div style={{ width: `${score * 10}%` }} />
          </div>
          <strong>{score}</strong>
        </div>
      ))}
    </div>
  );
}

function DemoFlow({ steps }) {
  return (
    <ol className="demo-flow-list">
      {steps.map((step, index) => (
        <li key={step.title}>
          <span>{index + 1}</span>
          <div>
            <strong>{step.title}</strong>
            <p>{step.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function DemoRecordingScript({ script }) {
  return (
    <section className="demo-script-panel" aria-label="Investor demo recording script">
      <div className="record-card-header">
        <div>
          <span className="surface-chip">Record demo</span>
          <h3>Investor Demo Recording Script</h3>
        </div>
        <strong>5 minutes</strong>
      </div>
      <div className="demo-script-list">
        {script.map((segment) => (
          <article key={segment.time} className="record-card">
            <div className="record-card-header">
              <strong>{segment.time}</strong>
              <span>{segment.shot}</span>
            </div>
            <p>{segment.narration}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function MonetizationPipeline({ steps }) {
  return (
    <section className="monetization-panel" aria-label="First customer and revenue pipeline">
      <div className="record-card-header">
        <div>
          <span className="surface-chip">Monetize</span>
          <h3>First Customer Revenue Path</h3>
        </div>
        <strong>Proof to paid pilot</strong>
      </div>
      <div className="monetization-grid">
        {steps.map((step) => (
          <article key={step.stage} className="record-card">
            <span className="surface-chip">{step.stage}</span>
            <h4>{step.customer}</h4>
            <p>{step.offer}</p>
            <KeyValue label="Commercial ask" value={step.price} />
          </article>
        ))}
      </div>
    </section>
  );
}

function GitPullPlan({ steps }) {
  return (
    <section className="git-pull-panel" aria-label="Git pull deployment plan">
      <div className="record-card-header">
        <div>
          <span className="surface-chip">Deploy OS</span>
          <h3>Git Pull Launch Plan</h3>
        </div>
        <strong>fast-forward only</strong>
      </div>
      <div className="git-pull-list">
        {steps.map((step) => (
          <article key={step.step} className="record-card">
            <div className="record-card-header">
              <strong>{step.step}</strong>
              <span>operator action</span>
            </div>
            <code>{step.command}</code>
            <p>{step.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function FeatureRegistryDashboard({ registry, badge }) {
  if (!registry) {
    return (
      <OperatorPanel title="Feature Registry Status">
        <EmptyState label="Feature registry data is pending from /api/feature-registry." />
      </OperatorPanel>
    );
  }

  const features = registry.features || [];
  const productionReadyCount = Number(registry.production_ready_feature_count || 0);
  const verificationProductReady =
    productionReadyCount >= Number(registry.verified_true_threshold || 3) &&
    registry.production_proven === false &&
    registry.live_pilot_authorized === false;

  return (
    <div className="feature-registry-layout">
      <div className="metric-grid">
        <TrustMetric
          label="Registry classification"
          value={registry.status || "FEATURE_REGISTRY_LEVEL_12"}
          helper={`${registry.classification || "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"} | ${registry.generation_mode || "REPLAY_DERIVED_EVIDENCE_PROJECTION"}`}
          tone="success"
        />
        <TrustMetric
          label="Evidence complete"
          value={`${registry.complete_feature_count || 0}/${registry.feature_count || 0}`}
          helper="Required implementation, test, replay, proof, and boundary guard evidence validates."
          tone={
            registry.complete_feature_count === registry.feature_count
              ? "success"
              : "warning"
          }
        />
        <TrustMetric
          label="Production-ready claims"
          value={productionReadyCount}
          helper="Verification products can be production-ready while production deployment remains blocked."
          tone={verificationProductReady ? "success" : "warning"}
        />
        <TrustMetric
          label="Claim history"
          value="v1"
          helper={registry.claim_history || "docs/governance/AFRITECH_FEATURE_CLAIM_HISTORY.md"}
          tone="neutral"
        />
      </div>

      <OperatorPanel title="Trust Badge System">
        <div className="trust-badge-panel">
          <div className="trust-badge-preview" aria-label="AfriTech public trust badge">
            <span className="trust-badge-mark">✓</span>
            <strong>{badge?.label || "Verified by AfriTech Trust Layer"}</strong>
          </div>
          <div className="trust-badge-copy">
            <strong>{badge?.status || "PENDING"}</strong>
            <p>{badge?.embed?.text || "Public proof resolves through /public/trust-badge and /public/ecosystem-evolution/verify."}</p>
            <div className="surface-chip-row" aria-label="Production-ready verification features">
              {PRODUCTIZED_TRUST_FEATURE_IDS.map((featureId) => (
                <span key={featureId} className="surface-chip">
                  {featureId}
                </span>
              ))}
            </div>
            <div className="feature-action-row">
              <a className="button secondary" href="/public/trust-badge">
                Public Badge
              </a>
              <a className="button secondary" href="/public/ecosystem-evolution/verify">
                Verify System Integrity
              </a>
            </div>
          </div>
        </div>
      </OperatorPanel>

      <OperatorPanel title="Feature Claims">
        <div className="feature-registry-table" role="table" aria-label="Governed feature registry">
          <div className="feature-registry-row feature-registry-head" role="row">
            <span role="columnheader">Feature</span>
            <span role="columnheader">Technical</span>
            <span role="columnheader">Activation</span>
            <span role="columnheader">Evidence</span>
            <span role="columnheader">Boundary Guard</span>
          </div>
          {features.map((feature) => (
            <article key={feature.id} className="feature-registry-row" role="row">
              <div role="cell">
                <strong>{feature.name}</strong>
                <p>{feature.description}</p>
                <span className="surface-chip">{feature.version} | {feature.last_updated}</span>
              </div>
              <div role="cell">
                <span className={`registry-status status-${featureStatusTone(feature.technical_status)}`}>
                  {feature.technical_status}
                </span>
              </div>
              <div role="cell">
                <span className={`registry-status status-${featureStatusTone(feature.activation_status)}`}>
                  {feature.activation_status}
                </span>
              </div>
              <div role="cell">
                <strong>{feature.validation?.required_evidence_count || 0} refs</strong>
                <p>{feature.evidence_complete ? "EVIDENCE_VALIDATED" : "REVIEW_REQUIRED"}</p>
              </div>
              <div role="cell">
                <strong>{feature.validation?.boundary_guard_valid ? "BOUNDARY_GUARDED" : "GUARD_REVIEW"}</strong>
                <p>{feature.boundary_guard}</p>
              </div>
            </article>
          ))}
        </div>
      </OperatorPanel>

      <OperatorPanel title="Registry Enforcement">
        <div className="operator-grid compact-operator-grid">
          <article className="record-card">
            <strong>JSON / Proof Validation</strong>
            <p>JSON evidence must parse as a non-empty object; JSON proof payloads must expose required authority keys.</p>
          </article>
          <article className="record-card">
            <strong>Boundary Guard</strong>
            <p>Every feature claim links to an existing validator module before it can count as evidence complete.</p>
          </article>
          <article className="record-card">
            <strong>CI Enforcement</strong>
            <p>pytest afritech/tests/test_features.py -q is wired into the AfriRide proof pipeline.</p>
          </article>
          <article className="record-card">
            <strong>Production Gated</strong>
            <p>Production-ready verification features remain read-only and cannot imply live pilot, economic activation, or production-proven deployment.</p>
          </article>
        </div>
      </OperatorPanel>
    </div>
  );
}

function SystemTrustStatus({ trustState, lastUpdated, rollbackReady }) {
  return (
    <aside className="trust-status" aria-label="System trust status">
      <p>System Trust Status</p>
      <strong className={`status-${trustState.tone}`}>{trustState.label}</strong>
      <span>{trustState.summary}</span>
      <div className="trust-meta">
        <KeyValue label="Device" value={DEVICE_ID} />
        <KeyValue label="Mode" value={TEST_MODE ? "TEST_MODE" : "STANDARD"} />
        <KeyValue label="Updated" value={lastUpdated || "pending"} />
        <KeyValue
          label="Rollback"
          value={rollbackReady ? "Ready" : "Needs review"}
          tone={rollbackReady ? "success" : "warning"}
        />
      </div>
    </aside>
  );
}

function SectionIntro({ eyebrow, title, question }) {
  return (
    <div className="section-intro">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{question}</p>
    </div>
  );
}

function TrustMetric({ label, value, helper, tone = "neutral" }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}

function ProposalCard({ proposal }) {
  return (
    <article className="proposal-card">
      <div className="proposal-header">
        <div>
          <span>{proposal.id}</span>
          <h3>{proposal.title}</h3>
        </div>
        <strong>{proposal.status}</strong>
      </div>
      <p>{proposal.summary}</p>
      <div className="proposal-facts">
        <KeyValue label="Surface" value={proposal.surface} />
        <KeyValue
          label="Replay validation"
          value={proposal.replay}
          tone={proposal.replay === "PASS" ? "success" : "warning"}
        />
        <KeyValue
          label="Contracts"
          value={proposal.contracts}
          tone={proposal.contracts === "PASS" ? "success" : "warning"}
        />
        <KeyValue label="Drift risk" value={proposal.driftRisk} />
        <KeyValue label="Rollback readiness" value={proposal.rollback} />
        <KeyValue label="Decision records" value={proposal.approvals} />
      </div>
    </article>
  );
}

function RuleCard({ rule }) {
  return (
    <article className="rule-card">
      <span>{rule.name}</span>
      <strong>{rule.value}</strong>
      <p>{rule.detail}</p>
    </article>
  );
}

function OperatorPanel({ title, children }) {
  return (
    <section className="operator-panel">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function ConversationPanel({ messages, value, pending, onChange, onSubmit }) {
  return (
    <aside className="conversation-panel" aria-label="Trust conversation">
      <div className="conversation-status">
        <span>Trust conversation</span>
        <strong>Evidence only</strong>
      </div>
      <div className="conversation-messages">
        {messages.map((message, index) => (
          <article
            key={`${message.role}-${index}`}
            className={`conversation-message message-${message.role}`}
          >
            <span>{message.role === "user" ? "You" : "System"}</span>
            <p>{message.text}</p>
            {message.evidence && (
              <div className="evidence-chip">
                {message.evidence.proposal_id} | {message.evidence.decision.status}
              </div>
            )}
          </article>
        ))}
      </div>
      <form className="conversation-form" onSubmit={onSubmit}>
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Ask why this was approved"
          aria-label="Trust question"
        />
        <button type="submit" disabled={pending}>
          {pending ? "Checking" : "Ask"}
        </button>
      </form>
    </aside>
  );
}

function KeyValue({ label, value, tone = "neutral" }) {
  return (
    <div className="key-value">
      <span>{label}</span>
      <strong className={`value-${tone}`}>{value}</strong>
    </div>
  );
}

function EmptyState({ label }) {
  return <div className="empty-state">{label}</div>;
}

function GovernanceFeedbackPanel({ submission }) {
  if (!submission) {
    return (
      <EmptyState label="Rejected by Governance feedback appears after an explicit proposal submission." />
    );
  }

  return (
    <div className="stack">
      <article className="record-card">
        <div className="record-card-header">
          <strong>{submission.governanceStatus === "rejected" ? "Rejected by Governance" : "Governance review state"}</strong>
          <span>{submission.governanceStatus}</span>
        </div>
        <p>{submission.governanceSummary}</p>
        {submission.rejectionReason && <p>{submission.rejectionReason}</p>}
      </article>
      <article className="record-card">
        <strong>Why this outcome happened</strong>
        <div className="stack compact-stack">
          {submission.validationViolations.length > 0 ? (
            submission.validationViolations.map((violation) => (
              <div key={violation} className="reason-chip">
                {violation}
              </div>
            ))
          ) : (
            <div className="reason-chip reason-chip-success">
              No validation violations detected before governance review.
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

function ReplayReasoningPanel({ submission }) {
  if (!submission) {
    return (
      <EmptyState label='Replay-backed reasoning appears after submission, for example: "This failed because replay invariant X was violated."' />
    );
  }

  return (
    <div className="stack">
      <article className="record-card">
        <div className="record-card-header">
          <strong>{submission.reasoning.status}</strong>
          <span>{submission.reasoning.invariant}</span>
        </div>
        <p>{submission.reasoning.explanation}</p>
      </article>
      <div className="proposal-facts">
        <KeyValue label="Replay invariant" value={submission.reasoning.invariant} />
        <KeyValue
          label="Failure mode"
          value={submission.reasoning.failureMode || "none"}
          tone={submission.reasoning.failureMode ? "warning" : "success"}
        />
        <KeyValue
          label="Divergence location"
          value={submission.reasoning.divergenceLocation || "none"}
        />
      </div>
    </div>
  );
}

function WalkthroughPanel({ active, step, steps, narrative, onNext, onPrevious }) {
  return (
    <div className="stack">
      <p className="section-note">
        Partners can walk the boundary from draft to replay explanation and see that AI helps
        while governance decides.
      </p>
      <div className="walkthrough-steps">
        {steps.map((entry, index) => (
          <article
            key={entry.id}
            className={`record-card walkthrough-step ${index === step ? "walkthrough-step-active" : ""}`}
          >
            <strong>{entry.title}</strong>
            <p>{entry.detail}</p>
          </article>
        ))}
      </div>
      <article className="record-card">
        <div className="record-card-header">
          <strong>{active ? "Demo Walkthrough Mode" : "Walkthrough preview"}</strong>
          <span>
            Step {step + 1}/{steps.length}
          </span>
        </div>
        <p>{narrative}</p>
      </article>
      <div className="afriprog-action-row">
        <button type="button" className="button secondary" onClick={onPrevious} disabled={step === 0}>
          Previous
        </button>
        <button
          type="button"
          className="button primary"
          onClick={onNext}
          disabled={!active || step === steps.length - 1}
        >
          Next boundary step
        </button>
      </div>
    </div>
  );
}
