import React, { useEffect, useMemo, useState } from "react";
import { AuditorDashboard } from "./AuditorDashboard";
import { connectDashboardRealtime } from "./realtime";
import { LiveVerifierPanel } from "./LiveVerifierPanel";
import { TrustExplorerFrontend } from "./TrustExplorer";

const API_BASE_URL =
  import.meta?.env?.VITE_AFRIRIDE_API_URL ||
  (globalThis.location?.hostname === "localhost" ||
  globalThis.location?.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : globalThis.location?.origin || "");
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
  novatechOrgPlatform: null,
  novatechSaas: null,
  novatechOutcomeStatus: null,
  novatechTrustNetwork: null,
  novatechMarketplace: null,
  novatechDocumentationCompliance: null,
  novatechControlledExecutionActivation: null,
  novatechMarketplaceOnboarding: null,
  novapayLiveTestReadiness: null,
  novarideEcosystem: null,
  novaridePlatformArchitectureContract: null,
  novarideOperatorDashboardContract: null,
  operatorAutonomy: null,
  novarideFleetManagerContract: null,
  novarideBusinessPortalContract: null,
  novarideAdminContract: null,
  novarideInspectorAppContract: null,
  novarideSupportContract: null,
  novaridePhase11Status: null,
  novaridePhase12Status: null,
  novaridePhase13Status: null,
  novaridePartnerPortalContract: null,
  operatorDigitalTwin: null,
  operatorMetaLearningRedesign: null,
  operatorDemandForecast: null,
  operatorStrategyEngine: null,
  operatorBusinessPricing: null,
  operatorCityProfitOptimization: null,
  liveAnalytics: null,
  analyticsArchive: null,
  decisionArchive: null,
  actionArchive: null,
  operatorCityAutomation: null,
  operatorMultiCityOrchestration: null,
};

const MAX_ANALYTICS_POINTS = 16;

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
  { id: "intelligence", name: "Intelligence", status: "Indexed", signal: "AfriPro / NovaCodePro workspace" },
  { id: "economy", name: "Economy", status: "Modeled", signal: "Gasless proof market" },
  { id: "products", name: "Products", status: "Packaged", signal: "AfriRide, AfriPay, AfriPro" },
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
  { name: "AfriPro / NovaCodePro", status: "Active", proofCount: "144", trustLevel: "91%", usage: "Governed coding", focus: "AI software factory roadmap with proposal-only handoff" },
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
  { title: "Show Intelligence", detail: "Switch to AfriPro / NovaCodePro and demonstrate proposal-only AI assistance." },
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

const NOVATECH_PLATFORM_NAV = [
  { label: "Main", href: "#home", detail: "NovaTech home" },
  { label: "Organization OS", href: "#organization", detail: "Intranet + extranet" },
  { label: "SaaS / Tenants", href: "#saas", detail: "Organizations + billing" },
  { label: "Outcome Intelligence", href: "#outcomes", detail: "Outcome + trust network" },
  { label: "NovaProgramming", href: "/v1/novaprogramming/dashboard", detail: "Engineering layer" },
  { label: "NovaScript", href: "/v1/novascript/dashboard", detail: "AI + trust layer" },
  { label: "NovaTrust", href: "/public/trust/dashboard", detail: "Verification layer" },
  { label: "NovaPower", href: "#power", detail: "Infrastructure layer" },
  { label: "NovaID / AfriID", href: "#identity", detail: "Identity layer" },
  { label: "NovaPay / AfriPay", href: "#payments", detail: "Payments layer" },
  { label: "Products", href: "#products", detail: "Business apps" },
];

const NOVATECH_CORE_LAYERS = [
  {
    name: "NovaProgramming",
    status: "Wired",
    route: "/console/programming",
    summary: "Engineering control, metrics, RBAC, staff dashboards, and governed release surfaces.",
  },
  {
    name: "NovaScript",
    status: "Wired",
    route: "/console/intelligence",
    summary: "AI system state, risk analysis, trust graph, and repository intelligence.",
  },
  {
    name: "NovaTrust",
    status: "Wired",
    route: "/console/trust",
    summary: "Proof packets, replay validation, event timeline, and external verification surfaces.",
  },
  {
    name: "NovaPower",
    status: "Wired",
    route: "/console/authority",
    summary: "Policy decisions for roles, scopes, tenants, ownership, and risk controls.",
  },
  {
    name: "NovaID / AfriID",
    status: "Wired",
    route: "/console/identity",
    summary: "Identity binding, organizations, devices, sessions, roles, and KYC posture.",
  },
  {
    name: "NovaPay / AfriPay",
    status: "Wired",
    route: "/console/payments",
    summary: "Intent validation, transaction execution, receipts, settlements, and finance audit trails.",
  },
];

const NOVATECH_CORE_CONSOLE_MODULES = [
  { key: "identity", label: "NovaID / AfriID", path: "/console/identity", metric: "Identity" },
  { key: "authority", label: "NovaPower", path: "/console/authority", metric: "Authority" },
  { key: "payments", label: "NovaPay / AfriPay", path: "/console/payments", metric: "Payment" },
  { key: "trust", label: "NovaTrust", path: "/console/trust", metric: "Proof" },
  { key: "intelligence", label: "NovaScript", path: "/console/intelligence", metric: "Intelligence" },
  { key: "programming", label: "NovaProgramming", path: "/console/programming", metric: "Evolution" },
];

const NOVATECH_CORE_FLOW = [
  "Identity",
  "Authority",
  "Execution",
  "Payment",
  "Proof",
  "Intelligence",
  "Evolution",
];

const NOVATECH_CONSOLE_WIREFRAMES = [
  {
    screen: "/console/identity",
    title: "NovaID Command Surface",
    zones: ["Session status", "Organization switcher", "Device registry", "Role editor"],
  },
  {
    screen: "/console/authority",
    title: "NovaPower Policy Surface",
    zones: ["Policy table", "Decision trace", "Review queue", "Control log"],
  },
  {
    screen: "/console/payments",
    title: "NovaPay Transaction Surface",
    zones: ["Intent queue", "Transactions", "Receipts", "Settlements"],
  },
  {
    screen: "/console/trust",
    title: "NovaTrust Explorer",
    zones: ["Timeline", "Actor", "Action", "Replay result"],
  },
  {
    screen: "/console/intelligence",
    title: "NovaScript Intelligence Surface",
    zones: ["Ask system", "Risk assistant", "Audit summary", "Recommendations"],
  },
  {
    screen: "/console/programming",
    title: "NovaProgramming Studio",
    zones: ["Project list", "Proposal editor", "Diff viewer", "Validator results"],
  },
];

const NOVATRUST_PUBLIC_EXPLORER = {
  route: "/trust/explorer/:receipt_id",
  apiRoute: "/v1/core-platform/trust/explorer/:receipt_id",
  pilotFlow: "/v1/core-platform/pilot/flow",
  zones: [
    "Timeline",
    "Actor",
    "Authority decision",
    "Payment receipt",
    "Replay result",
    "AI explanation",
  ],
};

const NOVATECH_PRODUCT_LAYERS = [
  {
    name: "AfriRide / NovaRide",
    status: "Active",
    route: "/v1/operator/dashboard",
    summary: "Mobility execution, receipts, replay, and operator monitoring.",
  },
  {
    name: "AfriEat / NovaEat",
    status: "Planned",
    route: "#products",
    summary: "Food delivery and logistics with payment-backed fulfillment.",
  },
  {
    name: "AfriPro / NovaCodePro",
    status: "Phase 0 roadmap",
    route: "/v1/novaprogramming/dashboard",
    summary: "AI software engineering platform: SaaS foundation, thinker/builder engines, governed code generation, DevOps, testing, learning, integrations, and enterprise controls.",
  },
  {
    name: "NovaVirtualMall",
    status: "Planned",
    route: "#products",
    summary: "E-commerce product marketplace with verified purchase flow.",
  },
  {
    name: "NovaLogistics",
    status: "Planned",
    route: "#products",
    summary: "Delivery network and fleet management surfaces.",
  },
  {
    name: "NovaHealth",
    status: "Planned",
    route: "#products",
    summary: "Medical services and telehealth control planes.",
  },
  {
    name: "NovaLearn",
    status: "Planned",
    route: "#products",
    summary: "Education platform, courses, and learning operations.",
  },
  {
    name: "NovaTalent",
    status: "Planned",
    route: "#products",
    summary: "Hiring and workforce marketplace surfaces.",
  },
];

const NOVAPAY_SHARED_SERVICES = [
  "Identity Service",
  "Transfer Service",
  "Policy Engine",
  "Compliance Engine",
  "Routing Engine",
  "FX Engine",
  "Ledger",
  "Settlement",
  "Receipt",
  "Audit",
  "Replay",
];

const NOVAPAY_UNIFIED_DOMAIN_MODEL = [
  "Customer",
  "Wallet",
  "Transfer",
  "Funding Source",
  "Jurisdiction",
  "License",
  "Policy",
  "Compliance",
  "Routing",
  "Settlement",
  "Ledger",
  "Receipt",
  "Audit",
  "Replay",
];

const NOVAPAY_ROLE_APPS = [
  {
    name: "NovaPay Consumer App",
    audience: "Individuals, families, students, migrant workers, international remittance customers",
    navigation: ["Home", "Transfer", "Wallet", "Scan QR", "Activity", "Profile"],
    capabilities: [
      "Multi-currency wallet",
      "Saved beneficiaries",
      "Local transfer",
      "International remittance",
      "Phone number transfer",
      "Wallet-to-wallet",
      "QR transfer",
      "Mobile money funding",
      "Bank funding",
      "Card funding",
      "Cash via agent",
      "Merchant QR",
      "Bill payments",
      "Airtime",
      "Utilities",
      "Biometrics",
      "Device binding",
      "Trusted devices",
      "Transaction approvals",
      "Cryptographic receipts",
      "Verification codes",
      "Replay timeline",
    ],
    primaryFlow: "Quote -> Transfer -> Receipt -> Replay proof",
    surface: "consumer_mobile",
  },
  {
    name: "NovaPay Agent App",
    audience: "Cash-in agents, cash-out agents, rural agents",
    navigation: ["Dashboard", "Cash In", "Cash Out", "Customers", "Reports", "Profile"],
    capabilities: [
      "Customer lookup by phone",
      "Customer lookup by QR",
      "Customer lookup by wallet ID",
      "Cash In",
      "Cash Out",
      "Agent settlement",
      "Float management",
      "Opening balance",
      "Closing balance",
      "Cash reconciliation",
      "Float requests",
      "KYC capture",
      "Document scan",
      "Photo verification",
    ],
    primaryFlow: "Lookup -> KYC check -> Cash operation -> Reconciliation receipt",
    surface: "agent_mobile",
  },
  {
    name: "NovaPay Merchant App",
    audience: "Retail, restaurants, shops, SMEs",
    navigation: ["Dashboard", "Receive", "Transactions", "Settlement", "Reports", "Settings"],
    capabilities: [
      "Receive payments",
      "QR payments",
      "Wallet payments",
      "Mobile money payments",
      "Refunds",
      "Merchant settlement",
      "Daily sales",
      "Settlement reports",
      "Business analytics",
      "Customer receipts",
      "Invoice generation",
    ],
    primaryFlow: "QR request -> Customer payment -> Merchant receipt -> Settlement report",
    surface: "merchant_mobile",
  },
  {
    name: "NovaPay Business App",
    audience: "Companies, payroll teams, NGOs, government",
    navigation: ["Overview", "Bulk Pay", "Approvals", "Treasury", "Reports", "Integrations"],
    capabilities: [
      "Bulk payments",
      "Payroll",
      "Supplier payments",
      "Expense management",
      "Role-based approvals",
      "Treasury",
      "Reports",
      "API integration",
    ],
    primaryFlow: "Upload batch -> Approval policy -> Bulk disbursement -> Audit export",
    surface: "business_web",
  },
  {
    name: "NovaPay Operations App",
    audience: "NovaPay operations team",
    navigation: ["Overview", "Transfers", "Compliance", "Treasury", "Providers", "Replay", "Settings"],
    capabilities: [
      "Live transfers",
      "Settlement queue",
      "Pending transactions",
      "Compliance cases",
      "Fraud monitoring",
      "Liquidity Dashboard",
      "Treasury Dashboard",
      "Provider Health",
      "Incident Management",
      "Replay",
    ],
    primaryFlow: "Monitor queue -> Inspect transfer -> Verify replay -> Escalate incident",
    surface: "operations_console",
  },
  {
    name: "NovaPay Compliance App",
    audience: "Compliance officers",
    navigation: ["Cases", "AML", "Sanctions", "KYC", "Reports", "Audit"],
    capabilities: [
      "AML",
      "Sanctions",
      "KYC",
      "Transaction monitoring",
      "Case management",
      "Reporting",
      "Audit export",
      "Suspicious activity review",
    ],
    primaryFlow: "Case queue -> Evidence review -> Decision trace -> Audit package",
    surface: "compliance_console",
  },
  {
    name: "NovaPay Support App",
    audience: "Customer support",
    navigation: ["Search", "Transfers", "Replay", "Disputes", "Refunds", "Messages"],
    capabilities: [
      "Customer search",
      "Transfer replay",
      "Receipt verification",
      "Dispute management",
      "Refund workflow",
      "Communication history",
    ],
    primaryFlow: "Customer search -> Replay timeline -> Receipt verification -> Support outcome",
    surface: "support_console",
  },
  {
    name: "NovaPay Administration App",
    audience: "Platform administrators",
    navigation: ["Organizations", "Users", "Roles", "Policies", "Providers", "Licenses"],
    capabilities: [
      "Organizations",
      "Users",
      "Roles",
      "Permissions",
      "Policies",
      "Feature flags",
      "Configuration",
      "Provider management",
      "License management",
    ],
    primaryFlow: "Configure tenant -> Assign roles -> Publish policy -> Verify access",
    surface: "admin_console",
  },
  {
    name: "NovaPay Developer Portal",
    audience: "Partners, developers, banks, fintechs",
    navigation: ["Docs", "API Keys", "Sandbox", "Webhooks", "Events", "SDKs"],
    capabilities: [
      "API keys",
      "SDKs",
      "Documentation",
      "Sandbox",
      "Webhook management",
      "Event Explorer",
    ],
    primaryFlow: "Read docs -> Create sandbox key -> Register webhook -> Verify event",
    surface: "developer_portal",
  },
];

const NOVAPAY_IMPLEMENTATION_ROADMAP = [
  "NovaPay Consumer App",
  "NovaPay Operations App",
  "NovaPay Agent App",
  "NovaPay Merchant App",
  "NovaPay Compliance App",
  "NovaPay Business App",
  "NovaPay Administration App",
  "NovaPay Developer Portal",
];

const NOVAPAY_PRIORITY_APP_BUILDS = [
  {
    name: "Consumer App",
    surface: "consumer_mobile",
    productLabel: "NovaPay Consumer App",
    persona: "Individuals, families, students, migrant workers, and remittance customers",
    promise: "Send, receive, store, pay, and prove money movement from one mobile wallet.",
    screens: [
      "Home balance",
      "Send Money",
      "Beneficiaries",
      "Wallet",
      "Scan QR",
      "Activity",
      "Receipt",
      "Replay",
      "Profile",
    ],
    workflow: [
      "Authenticate device",
      "Select beneficiary",
      "Request quote",
      "Confirm funding source",
      "Create transfer",
      "Show receipt",
      "Open replay timeline",
    ],
    backendBindings: [
      "POST /v1/transfers/quote",
      "POST /v1/transfers",
      "GET /v1/transfers/{id}/receipt",
      "GET /v1/transfers/{id}/replay",
      "GET /v1/transfers/{id}/audit-package",
    ],
    proofWidgets: ["Quote hash", "Receipt code", "Event timeline", "Device binding", "Replay valid badge"],
  },
  {
    name: "Agent App",
    surface: "agent_mobile",
    productLabel: "NovaPay Agent App",
    persona: "Cash-in, cash-out, and rural liquidity agents",
    promise: "Operate cash services with float visibility, identity checks, and end-of-day reconciliation.",
    screens: [
      "Agent Dashboard",
      "Cash In",
      "Cash Out",
      "Customer Lookup",
      "KYC Capture",
      "Float",
      "Settlement",
      "Reports",
      "Profile",
    ],
    workflow: [
      "Open shift",
      "Lookup customer",
      "Verify KYC",
      "Record cash movement",
      "Confirm receipt",
      "Reconcile float",
      "Close shift",
    ],
    backendBindings: [
      "POST /v1/funding-sources/validate",
      "POST /v1/transfers",
      "GET /v1/treasury/snapshot",
      "GET /v1/transfers/{id}/receipt",
      "GET /v1/transfers/{id}/verification",
    ],
    proofWidgets: ["KYC status", "Float delta", "Cash receipt", "Settlement exposure", "Closing balance proof"],
  },
  {
    name: "Merchant App",
    surface: "merchant_mobile",
    productLabel: "NovaPay Merchant App",
    persona: "Retailers, restaurants, shops, SMEs, and market sellers",
    promise: "Accept QR, wallet, and mobile money payments with refunds, settlement, and daily sales proof.",
    screens: [
      "Merchant Dashboard",
      "Receive Payment",
      "QR Display",
      "Transactions",
      "Refunds",
      "Settlement",
      "Invoices",
      "Reports",
      "Settings",
    ],
    workflow: [
      "Create payment request",
      "Display QR",
      "Receive customer payment",
      "Issue receipt",
      "Settle merchant balance",
      "Export daily report",
    ],
    backendBindings: [
      "POST /v1/transfers/quote",
      "POST /v1/transfers",
      "GET /v1/transfers/{id}/verification",
      "GET /v1/treasury/snapshot",
      "GET /v1/core-platform/payments/providers/status",
    ],
    proofWidgets: ["Payment status", "QR payload hash", "Refund trace", "Settlement batch", "Sales proof"],
  },
  {
    name: "Business App/Portal/Web",
    surface: "business_web_portal",
    productLabel: "NovaPay Business App / Portal / Web",
    persona: "Companies, payroll teams, NGOs, enterprises, and government programs",
    promise: "Run payroll, supplier payments, approvals, treasury controls, and audit exports from a web portal.",
    screens: [
      "Business Overview",
      "Bulk Payments",
      "Payroll",
      "Approvals",
      "Treasury",
      "Suppliers",
      "API Integration",
      "Reports",
      "Audit Export",
    ],
    workflow: [
      "Upload payment file",
      "Validate recipients",
      "Apply approval policy",
      "Reserve liquidity",
      "Execute disbursement",
      "Generate audit bundle",
      "Export report",
    ],
    backendBindings: [
      "GET /v1/policies",
      "POST /v1/transfers/quote",
      "POST /v1/transfers",
      "GET /v1/treasury/snapshot",
      "GET /v1/transfers/{id}/audit-package",
    ],
    proofWidgets: ["Approval chain", "Policy version", "Batch status", "Liquidity gate", "Audit package"],
  },
  {
    name: "Operations App/Website",
    surface: "operations_web",
    productLabel: "NovaPay Operations App / Website",
    persona: "NovaPay operations, treasury, support escalation, and provider monitoring teams",
    promise: "Monitor transfers, liquidity, settlement queues, provider health, incidents, replay, and audit evidence.",
    screens: [
      "Operations Overview",
      "Live Transfers",
      "Settlement Queue",
      "Compliance Cases",
      "Fraud Monitor",
      "Liquidity Dashboard",
      "Treasury Dashboard",
      "Provider Health",
      "Replay Console",
      "Incidents",
    ],
    workflow: [
      "Watch live transfers",
      "Filter exceptions",
      "Inspect decision trace",
      "Validate event chain",
      "Check liquidity",
      "Escalate incident",
      "Export audit package",
    ],
    backendBindings: [
      "GET /v1/treasury/snapshot",
      "GET /v1/corridors",
      "GET /v1/policies",
      "GET /v1/transfers/{id}/timeline",
      "GET /v1/transfers/{id}/audit-package",
    ],
    proofWidgets: ["Provider health", "Outbox status", "Snapshot root", "Event chain", "External verifier result"],
  },
];

const NOVAPAY_PORTAL_APP_BUILDS = [
  {
    name: "Merchant App/Web/Portal",
    surface: "merchant_web_portal",
    productLabel: "NovaPay Merchant App / Web / Portal",
    audience: "Retail groups, restaurants, shops, SMEs, finance managers, and branch operators",
    outcome: "Give merchants one governed workspace for accepting payments, issuing refunds, settling balances, and proving daily sales.",
    pages: [
      "Merchant Overview",
      "Payment Requests",
      "QR Checkout",
      "Transactions",
      "Refund Console",
      "Settlement Batches",
      "Invoices",
      "Disputes",
      "Analytics",
      "Merchant Settings",
    ],
    commandCenter: [
      "Create QR payment request",
      "Generate invoice",
      "Approve refund",
      "Review settlement batch",
      "Export daily sales proof",
      "Verify receipt",
    ],
    webWorkflow: [
      "Create payment intent",
      "Present QR or payment link",
      "Confirm customer payment",
      "Issue cryptographic receipt",
      "Batch settlement",
      "Export merchant audit report",
    ],
    backendBindings: [
      "POST /v1/transfers/quote",
      "POST /v1/transfers",
      "GET /v1/transfers/{id}/receipt",
      "GET /v1/transfers/{id}/verification",
      "GET /v1/core-platform/payments/providers/status",
      "GET /v1/treasury/snapshot",
    ],
    proofControls: [
      "QR payload hash",
      "Receipt verifier",
      "Refund replay trace",
      "Settlement batch hash",
      "Daily sales root",
    ],
  },
  {
    name: "Agent App/Web/Portal",
    surface: "agent_web_portal",
    productLabel: "NovaPay Agent App / Web / Portal",
    audience: "Agent network managers, cash-in agents, cash-out agents, rural liquidity supervisors, and field auditors",
    outcome: "Give agents and supervisors a governed workspace for cash operations, float control, KYC capture, reconciliation, and proof exports.",
    pages: [
      "Agent Overview",
      "Cash In Console",
      "Cash Out Console",
      "Customer Lookup",
      "KYC Review",
      "Float Ledger",
      "Float Requests",
      "Shift Reconciliation",
      "Agent Settlements",
      "Field Audit",
    ],
    commandCenter: [
      "Open agent shift",
      "Lookup customer",
      "Capture KYC evidence",
      "Process cash in",
      "Process cash out",
      "Request float top-up",
      "Close and reconcile shift",
    ],
    webWorkflow: [
      "Open shift",
      "Verify customer identity",
      "Validate funding source",
      "Record cash movement",
      "Generate receipt",
      "Reconcile float ledger",
      "Submit shift proof",
    ],
    backendBindings: [
      "POST /v1/funding-sources/validate",
      "POST /v1/transfers/quote",
      "POST /v1/transfers",
      "GET /v1/transfers/{id}/receipt",
      "GET /v1/transfers/{id}/replay",
      "GET /v1/treasury/snapshot",
    ],
    proofControls: [
      "KYC evidence hash",
      "Cash receipt code",
      "Float delta proof",
      "Closing balance proof",
      "Shift reconciliation root",
    ],
  },
];

const NOVAPAY_CONTROL_PLANE_GUARANTEES = [
  "All apps are thin clients over the governed backend",
  "One Transfer aggregate",
  "One Ledger truth",
  "One Event platform",
  "One Audit and Proof model",
  "No duplicated business logic in role apps",
];

const NOVARIDE_APP_FALLBACKS = [
  "NovaRide Rider App",
  "NovaRide Driver App",
  "NovaRide Operator App / Portal",
  "NovaRide Inspector App / Portal",
  "NovaRide Fleet Portal",
  "NovaRide Merchant Portal",
  "NovaRide Corporate Portal",
  "NovaRide Trust & Safety Portal",
  "NovaRide Customer Support Portal",
  "NovaRide Admin",
  "NovaRide Developer Portal",
  "NovaRide Passenger",
  "NovaRide Partner",
];

const NOVARIDE_NEXT_GEN_PLATFORM_STACK = [
  {
    name: "NovaRide Rider App",
    users: "Daily commuters, families, tourists, and business travelers",
    modules: ["Home", "Book Ride", "Live Tracking", "Trip Timeline", "Wallet", "Ride History", "Trust Center", "Replay", "Support", "Profile"],
    features: ["Instant booking", "Scheduled rides", "Airport pickup", "Ride sharing", "Live GPS tracking", "Driver verification", "Cryptographic receipts", "Emergency assistance", "NovaPay integration"],
  },
  {
    name: "NovaRide Driver App",
    users: "Independent drivers and fleet drivers",
    modules: ["Dashboard", "Ride Queue", "Navigation", "Trip Lifecycle", "Earnings", "Wallet", "Vehicle", "Trust Score", "Replay", "Diagnostics"],
    features: ["Ride acceptance", "Smart dispatch", "Route optimization", "Earnings analytics", "Safety alerts", "Vehicle inspections", "Driver reputation", "Settlement through NovaPay"],
  },
  {
    name: "NovaRide Operator App / Portal",
    users: "NovaRide operations, safety, reliability, and city-control teams",
    modules: ["Live Operations Dashboard", "Live Map: rides + drivers", "Manual Dispatch Intervention", "Driver Availability", "Demand Heatmap", "Incident Monitoring", "SOS Escalation", "Ride Replay", "Payment / Receipt Status", "Provider Health", "Operational Alerts"],
    features: ["Monitor city", "Detect issue", "Inspect ride/driver", "Adjust governed dispatch if needed", "Escalate incident", "Verify replay/evidence", "Close operation log"],
  },
  {
    name: "NovaRide Inspector App / Portal",
    users: "Vehicle inspectors, driver verifiers, and regulatory compliance teams",
    modules: ["Vehicle Inspection", "Driver Verification", "License / Permit Check", "Insurance Check", "Roadworthiness Checklist", "Photo Evidence Capture", "Compliance Score", "Inspection History", "Regulatory Export", "Violation / Suspension Workflow"],
    features: ["Select driver/vehicle", "Verify documents", "Inspect vehicle", "Capture evidence", "Approve / reject / suspend", "Generate compliance proof"],
  },
  {
    name: "NovaRide Fleet Portal",
    users: "Taxi companies, corporate fleets, and logistics operators",
    modules: ["Fleet Dashboard", "Vehicle Management", "Driver Management", "Live Tracking", "Dispatch", "Maintenance", "Fuel", "Performance", "Reporting"],
    features: ["Fleet visibility", "Vehicle compliance", "Driver performance", "Maintenance tracking", "NovaPay payouts"],
  },
  {
    name: "NovaRide Merchant Portal",
    users: "Hotels, airports, shopping centres, hospitals, and universities",
    modules: ["Guest Ride Booking", "Corporate Billing", "Voucher Management", "Ride Analytics", "Invoice Management", "Settlement"],
    features: ["Book guest rides", "Issue vouchers", "Track guest journeys", "Review invoices", "Settle through NovaPay"],
  },
  {
    name: "NovaRide Corporate Portal",
    users: "Businesses, government, and NGOs",
    modules: ["Employee Travel", "Approvals", "Cost Centres", "Budgets", "Invoices", "Travel Analytics"],
    features: ["Approve trips", "Control budgets", "Allocate cost centres", "Review travel analytics", "Export invoices"],
  },
  {
    name: "NovaRide Trust & Safety Portal",
    users: "Safety and compliance response teams",
    modules: ["SOS Cases", "Incident Timeline", "Replay", "Evidence Viewer", "Driver Verification", "Passenger Verification", "Risk Scoring"],
    features: ["Review incident evidence", "Inspect replay", "Score risk", "Escalate safety action", "Export evidence"],
  },
  {
    name: "NovaRide Customer Support Portal",
    users: "Support agents and escalation teams",
    modules: ["Customer Search", "Ride Search", "Replay", "Refunds", "Disputes", "Communications", "Receipt Verification"],
    features: ["Search riders/drivers", "Inspect ride replay", "Verify receipts", "Handle disputes", "Request governed refunds"],
  },
  {
    name: "NovaRide Administrator Portal",
    users: "Platform administrators",
    modules: ["Organizations", "RBAC", "Configuration", "Pricing Rules", "Geofencing", "Feature Flags", "Licensing", "Provider Configuration"],
    features: ["Configure tenants", "Manage RBAC", "Publish pricing rules", "Control geofences", "Manage providers"],
  },
  {
    name: "NovaRide Developer Portal",
    users: "Partners, integrators, and developers",
    modules: ["API Keys", "SDKs", "Sandbox", "Webhook Manager", "Documentation", "Usage Analytics"],
    features: ["Create API keys", "Use sandbox", "Register webhooks", "Inspect usage", "Read API docs"],
  },
];

const NOVARIDE_GOVERNED_BACKEND_CHAIN = [
  "NovaID",
  "Policy Engine",
  "Dispatch Engine",
  "Matching",
  "Pricing",
  "Trust & Safety",
  "Inspection Registry",
  "Incident Registry",
  "Ride Lifecycle",
  "NovaPay",
  "Receipt",
  "Replay",
  "Audit",
];

const NOVARIDE_AI_INTELLIGENCE_LAYER = [
  "Demand Forecasting",
  "Driver Position Prediction",
  "ETA Prediction",
  "Fraud Detection",
  "Safety Scoring",
  "Dynamic Pricing",
  "Traffic Intelligence",
  "Dispatch Optimization",
  "Operational Insights",
];

const NOVARIDE_EVIDENCE_BACKED_RIDE_FLOW = [
  "Ride Request",
  "Dispatch Decision",
  "Driver Assignment",
  "Pickup",
  "Trip",
  "Payment",
  "Receipt",
  "Replay Timeline",
  "Verification Package",
];

const NOVARIDE_ENTERPRISE_OPERATIONS_LAYER = [
  {
    name: "Unified Command Center",
    purpose: "One operational control surface for rides, drivers, incidents, payments, providers, and replay evidence.",
    capabilities: ["City status", "Live operations", "Dispatch intervention", "Incident escalation", "Proof review"],
  },
  {
    name: "City Operations / Zone Model",
    purpose: "Model cities, service zones, airport zones, geofences, surge boundaries, and jurisdiction-aware operating rules.",
    capabilities: ["City registry", "Service zones", "Airport zones", "Geofencing", "Zone policy"],
  },
  {
    name: "Operational Digital Twin",
    purpose: "Replay and simulate the live mobility network using rides, drivers, demand, incidents, and provider state.",
    capabilities: ["Network snapshot", "Scenario simulation", "Capacity projection", "Replay comparison", "What-if analysis"],
  },
  {
    name: "AI Decision Explanation Layer",
    purpose: "Explain dispatch, pricing, safety, fraud, ETA, and demand recommendations without granting AI authority.",
    capabilities: ["Dispatch explanation", "Pricing explanation", "Risk explanation", "Confidence signals", "Operator review"],
  },
  {
    name: "Workflow / Incident Engine",
    purpose: "Coordinate SOS, disputes, support, trust, compliance, provider incidents, approvals, and closure evidence.",
    capabilities: ["Case routing", "SLA tracking", "Escalation policy", "Evidence binding", "Closure log"],
  },
  {
    name: "Fleet Intelligence",
    purpose: "Track driver supply, vehicle health, inspection status, utilization, maintenance, earnings, and fleet quality.",
    capabilities: ["Supply health", "Vehicle health", "Driver quality", "Maintenance forecast", "Fleet scorecards"],
  },
  {
    name: "Public Trust Portal",
    purpose: "Publish controlled transparency views for receipts, safety standards, verification, and public trust evidence.",
    capabilities: ["Receipt verification", "Safety standards", "Trust reports", "Public status", "Audit exports"],
  },
  {
    name: "Partner / Developer Ecosystem",
    purpose: "Expose governed APIs, webhooks, sandbox, SDKs, partner onboarding, and usage analytics.",
    capabilities: ["API keys", "Webhooks", "Sandbox", "SDK catalog", "Partner analytics"],
  },
  {
    name: "SRE Observability",
    purpose: "Measure reliability, latency, errors, queues, provider health, replay lag, and operational risk.",
    capabilities: ["SLO dashboard", "Error budget", "Provider health", "Queue lag", "Replay lag"],
  },
  {
    name: "Multi-Tenant Governance",
    purpose: "Govern organizations, roles, feature flags, policies, licensing, data boundaries, and tenant isolation.",
    capabilities: ["Tenant registry", "RBAC", "Feature flags", "Policy versions", "Data residency"],
  },
];

const NOVARIDE_OPERATOR_MODULE_FALLBACKS = [
  { key: "operations", name: "Operations", status: "partially_implemented" },
  { key: "ride_management", name: "Ride Management", status: "partially_implemented" },
  { key: "driver_monitoring", name: "Driver Monitoring", status: "partially_implemented" },
  { key: "safety_emergency", name: "Safety & Emergency", status: "contract_declared" },
  { key: "analytics", name: "Analytics Dashboard", status: "implemented" },
  { key: "ecosystem", name: "NovaRide Ecosystem Panel", status: "implemented" },
  { key: "support_escalation", name: "Support & Escalation", status: "contract_declared" },
];

const NOVARIDE_OPERATOR_ALLOWED_ACTION_FALLBACKS = [
  "manual_dispatch",
  "ride_reassignment",
  "monitoring",
  "emergency_handling",
];

const NOVARIDE_OPERATOR_FORBIDDEN_ACTION_FALLBACKS = [
  "direct_payment_execution",
  "direct_provider_integrations",
  "backend_rule_bypass",
];

const NOVARIDE_FLEET_MODULE_FALLBACKS = [
  { key: "fleet_management", name: "Fleet Management", status: "partially_implemented" },
  { key: "driver_management", name: "Driver Management", status: "partially_implemented" },
  { key: "vehicle_management", name: "Vehicle Management", status: "contract_declared" },
  { key: "maintenance_compliance", name: "Maintenance & Compliance", status: "contract_declared" },
  { key: "financial_management", name: "Financial Management", status: "contract_declared" },
  { key: "fleet_analytics", name: "Fleet Analytics", status: "partially_implemented" },
];

const NOVARIDE_FLEET_ALLOWED_ACTION_FALLBACKS = [
  "manage_vehicles",
  "assign_drivers",
  "view_earnings_reports",
  "receive_payouts_via_novapay",
];

const NOVARIDE_FLEET_FORBIDDEN_ACTION_FALLBACKS = [
  "dispatch_logic_bypass",
  "direct_payment_provider_access",
  "bypass_trust_compliance_checks",
];

const NOVARIDE_BUSINESS_MODULE_FALLBACKS = [
  { key: "corporate_travel", name: "Corporate Travel Management", status: "contract_declared" },
  { key: "employee_management", name: "Employee Management", status: "contract_declared" },
  { key: "approval_workflow", name: "Approval Workflow", status: "contract_declared" },
  { key: "business_wallet_billing", name: "Business Wallet & Billing", status: "partially_implemented" },
  { key: "department_budgets", name: "Department Budgets", status: "contract_declared" },
  { key: "reporting_analytics", name: "Reporting & Analytics", status: "contract_declared" },
];

const NOVARIDE_BUSINESS_ALLOWED_ACTION_FALLBACKS = [
  "book_rides",
  "approve_reject_requests",
  "manage_employees",
  "view_billing_reports",
];

const NOVARIDE_BUSINESS_FORBIDDEN_ACTION_FALLBACKS = [
  "direct_payment_execution",
  "dispatch_logic_bypass",
  "pricing_rule_bypass",
];

const NOVARIDE_ADMIN_MODULE_FALLBACKS = [
  { key: "user_role_management", name: "User & Role Management", status: "partially_implemented" },
  { key: "driver_vehicle_approval", name: "Driver & Vehicle Approval", status: "contract_declared" },
  { key: "pricing_service_configuration", name: "Pricing & Service Configuration", status: "contract_declared" },
  { key: "geography_service_zones", name: "Geography & Service Zones", status: "contract_declared" },
  { key: "promotions_campaigns", name: "Promotions & Campaigns", status: "contract_declared" },
  { key: "compliance_audit", name: "Compliance & Audit", status: "partially_implemented" },
  { key: "system_health_monitoring", name: "System Health & Monitoring", status: "partially_implemented" },
];

const NOVARIDE_ADMIN_ALLOWED_ACTION_FALLBACKS = [
  "configure_platform_rules",
  "approve_participants",
  "control_pricing_zones",
  "monitor_compliance",
];

const NOVARIDE_ADMIN_FORBIDDEN_ACTION_FALLBACKS = [
  "direct_ride_execution",
  "manual_payment_processing",
  "audit_replay_bypass",
];

const NOVARIDE_INSPECTOR_MODULE_FALLBACKS = [
  { key: "inspection_workflow", name: "Inspection Workflow", status: "contract_declared" },
  { key: "driver_verification", name: "Driver Verification", status: "contract_declared" },
  { key: "vehicle_inspection", name: "Vehicle Inspection", status: "contract_declared" },
  { key: "document_validation", name: "Document Validation", status: "contract_declared" },
  { key: "photo_evidence_capture", name: "Photo & Evidence Capture", status: "contract_declared" },
  { key: "inspection_reports", name: "Inspection Reports", status: "contract_declared" },
  { key: "compliance_status", name: "Compliance Status", status: "contract_declared" },
];

const NOVARIDE_INSPECTOR_ALLOWED_ACTION_FALLBACKS = [
  "perform_inspections",
  "submit_reports",
  "capture_evidence",
  "validate_documents",
];

const NOVARIDE_INSPECTOR_FORBIDDEN_ACTION_FALLBACKS = [
  "approve_payments",
  "admin_decision_bypass",
  "trust_engine_bypass",
];

const NOVARIDE_SUPPORT_MODULE_FALLBACKS = [
  { key: "customer_ticket_management", name: "Customer Ticket Management", status: "contract_declared" },
  { key: "ride_lookup_investigation", name: "Ride Lookup & Investigation", status: "partially_implemented" },
  { key: "refund_dispute_handling", name: "Refund & Dispute Handling", status: "contract_declared" },
  { key: "driver_passenger_assistance", name: "Driver & Passenger Assistance", status: "contract_declared" },
  { key: "escalation_management", name: "Escalation Management", status: "contract_declared" },
  { key: "audit_replay_integration", name: "Audit & Replay Integration", status: "partially_implemented" },
];

const NOVARIDE_SUPPORT_ALLOWED_ACTION_FALLBACKS = [
  "view_ride_data",
  "manage_tickets",
  "request_refunds",
  "contact_users",
  "escalate_cases",
];

const NOVARIDE_SUPPORT_FORBIDDEN_ACTION_FALLBACKS = [
  "novapay_bypass",
  "pricing_rule_mutation",
  "audit_log_bypass",
  "direct_payment_execution",
];

const NOVARIDE_PARTNER_MODULE_FALLBACKS = [
  { key: "ride_booking_widget", name: "Ride Booking & Widget Integration", status: "contract_declared" },
  { key: "guest_transport_management", name: "Guest Transport Management", status: "contract_declared" },
  { key: "bulk_ride_requests", name: "Bulk Ride Requests", status: "contract_declared" },
  { key: "partner_reporting", name: "Partner Reporting", status: "contract_declared" },
  { key: "billing_payments", name: "Billing & Payments", status: "contract_declared" },
  { key: "partner_configuration", name: "Partner Configuration", status: "contract_declared" },
];

const NOVARIDE_PARTNER_ALLOWED_ACTION_FALLBACKS = [
  "book_guest_rides",
  "manage_bulk_transport",
  "view_reports_billing",
  "configure_booking_settings",
];

const NOVARIDE_PARTNER_FORBIDDEN_ACTION_FALLBACKS = [
  "dispatch_logic_bypass",
  "direct_payment_processing",
  "pricing_rule_bypass",
  "direct_driver_access",
];

const NOVARIDE_ARCHITECTURE_SERVICE_FALLBACKS = [
  "NovaID",
  "NovaPay",
  "Dispatch Engine",
  "Pricing Engine",
  "Maps & Routing",
  "Trust Engine",
  "NovaNotify",
  "Analytics Engine",
  "Audit & Replay",
];

const NOVARIDE_ARCHITECTURE_FLOW_FALLBACKS = [
  "passenger_app_requests_ride",
  "api_validates_request_with_novaid",
  "pricing_engine_estimates_fare",
  "dispatch_engine_matches_driver",
  "driver_app_receives_request",
  "driver_accepts",
  "maps_tracks_trip",
  "trip_completes",
  "novapay_processes_payment",
  "audit_engine_stores_logs",
  "analytics_updated",
];

const NOVARIDE_ARCHITECTURE_BACKEND_AUTHORITY_FALLBACKS = [
  "dispatch_decisions",
  "novapay_payments",
  "pricing_calculations",
  "fraud_detection",
  "external_integrations",
];

const NOVARIDE_ARCHITECTURE_APP_BLOCKED_FALLBACKS = [
  "payment_processing",
  "pricing_mutation",
  "dispatch_bypass",
  "direct_provider_access",
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
      "Operators and developers describe intent in plain language before a governed NovaCodePro proposal is shaped for AfriProgramming review.",
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
      "AfriPro / NovaCodePro can prepare integration artifacts for APIs and SDKs without bypassing the governed execution path.",
  },
];

const NOVACODEPRO_PHASES = [
  { phase: "Phase 0", focus: "SaaS foundation", modules: "core, organizations, accounts, subscriptions, catalog, audit, feature flags, notifications, integrations" },
  { phase: "Phase 1", focus: "AI core", modules: "prompt, context, thinker, builder, orchestrator, memory" },
  { phase: "Phase 2", focus: "Architecture engine", modules: "patterns, diagrams, ADRs, modeling" },
  { phase: "Phase 3", focus: "Code generation", modules: "APIs, services, schemas, tests, refactors" },
  { phase: "Phase 4", focus: "Automation & DevOps", modules: "deployment, CI/CD, workflows, infrastructure, scheduler" },
  { phase: "Phase 5", focus: "Testing & debugging", modules: "testing, debug, validation, simulation" },
  { phase: "Phase 6", focus: "Monitoring & optimization", modules: "monitoring, logging, analytics, optimization, alerting" },
  { phase: "Phase 7", focus: "Knowledge & learning", modules: "knowledge, docs, tutorials, explanations" },
  { phase: "Phase 8", focus: "Apps layer", modules: "Studio, Dev, Architect, Automate, Learn, Operator, Admin" },
  { phase: "Phase 9", focus: "Integration ecosystem", modules: "GitHub, GitLab, VS Code, cloud, Docker, Kubernetes, databases, APIs" },
  { phase: "Phase 10", focus: "Governance & enterprise", modules: "RBAC, policy, compliance, security, audit, guards" },
  { phase: "Phase 11", focus: "Autonomous builder", modules: "self-debug, upgrades, adaptive architecture" },
  { phase: "Phase 12", focus: "NovaCodePro OS", modules: "multi-project orchestration and AI software factory operations" },
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

function normalizeAnalyticsSnapshot(snapshot) {
  return {
    snapshotId: snapshot.snapshot_id || snapshot.snapshotId || "",
    organizationId: snapshot.organization_id || snapshot.organizationId || "",
    source: snapshot.source || "unknown",
    snapshotType: snapshot.snapshot_type || snapshot.snapshotType || "operator_dashboard",
    trustScore: toNumber(snapshot.trust_score ?? snapshot.trustScore, 0),
    trustHealth: toNumber(snapshot.trust_health ?? snapshot.trustHealth, 0),
    replayHealthScore: toNumber(snapshot.replay_health_score ?? snapshot.replayHealthScore, 0),
    evidenceCoverage: toNumber(snapshot.evidence_coverage ?? snapshot.evidenceCoverage, 0),
    exceptionPressure: toNumber(snapshot.exception_pressure ?? snapshot.exceptionPressure, 0),
    alertCount: toNumber(snapshot.alert_count ?? snapshot.alertCount, 0),
    activeDrivers: toNumber(snapshot.active_drivers ?? snapshot.activeDrivers, 0),
    completedRides: toNumber(snapshot.completed_rides ?? snapshot.completedRides, 0),
    totalRides: toNumber(snapshot.total_rides ?? snapshot.totalRides, 0),
    guardCount: toNumber(snapshot.guard_count ?? snapshot.guardCount, 0),
    replayFailures: toNumber(snapshot.replay_failures ?? snapshot.replayFailures, 0),
    hashChainFailures: toNumber(snapshot.hash_chain_failures ?? snapshot.hashChainFailures, 0),
    missingTraces: toNumber(snapshot.missing_traces ?? snapshot.missingTraces, 0),
    receiptsCount: toNumber(snapshot.receipts_count ?? snapshot.receiptsCount, 0),
    traceCount: toNumber(snapshot.trace_count ?? snapshot.traceCount, 0),
    snapshotHash: snapshot.snapshot_hash || snapshot.snapshotHash || "",
    windowBucket: snapshot.window_bucket || snapshot.windowBucket || "",
    createdAt: snapshot.created_at || snapshot.createdAt || "",
    payload: snapshot.payload || {},
  };
}

function normalizeAnalyticsArchive(payload) {
  if (!payload) {
    return null;
  }

  const historyItems = Array.isArray(payload.history?.items)
    ? payload.history.items
    : Array.isArray(payload.history)
      ? payload.history
      : [];
  const latest = payload.latest ? normalizeAnalyticsSnapshot(payload.latest) : null;
  const prediction = payload.prediction
    ? {
        ...payload.prediction,
        riskLevel: payload.prediction.risk_level || payload.prediction.riskLevel || "unknown",
        watchItems: payload.prediction.watch_items || payload.prediction.watchItems || [],
        headline: payload.prediction.headline || payload.prediction.summary || "",
        confidence: toNumber(payload.prediction.confidence, 0),
        predictedTrustScore: toNumber(
          payload.prediction.predicted_trust_score ?? payload.prediction.predictedTrustScore,
          0,
        ),
        predictedEvidenceCoverage: toNumber(
          payload.prediction.predicted_evidence_coverage ??
            payload.prediction.predictedEvidenceCoverage,
          0,
        ),
        predictedExceptionPressure: toNumber(
          payload.prediction.predicted_exception_pressure ??
            payload.prediction.predictedExceptionPressure,
          0,
        ),
      }
    : null;

  return {
    ...payload,
    history: {
      ...(payload.history || {}),
      items: historyItems.map(normalizeAnalyticsSnapshot),
    },
    latest,
    prediction,
  };
}

function normalizeDecisionSnapshot(snapshot) {
  if (!snapshot) {
    return null;
  }

  return {
    decisionId: snapshot.decision_id || snapshot.decisionId || "",
    organizationId: snapshot.organization_id || snapshot.organizationId || "",
    source: snapshot.source || "unknown",
    decisionType: snapshot.decision_type || snapshot.decisionType || "operator_decision",
    decisionLane: snapshot.decision_lane || snapshot.decisionLane || "observe",
    decisionAction: snapshot.decision_action || snapshot.decisionAction || "continue_monitoring",
    decisionPriority: snapshot.decision_priority || snapshot.decisionPriority || "low",
    decisionSummary: snapshot.decision_summary || snapshot.decisionSummary || "",
    trustScore: toNumber(snapshot.trust_score ?? snapshot.trustScore, 0),
    trustHealth: toNumber(snapshot.trust_health ?? snapshot.trustHealth, 0),
    replayHealthScore: toNumber(snapshot.replay_health_score ?? snapshot.replayHealthScore, 0),
    evidenceCoverage: toNumber(snapshot.evidence_coverage ?? snapshot.evidenceCoverage, 0),
    exceptionPressure: toNumber(snapshot.exception_pressure ?? snapshot.exceptionPressure, 0),
    alertCount: toNumber(snapshot.alert_count ?? snapshot.alertCount, 0),
    guardCount: toNumber(snapshot.guard_count ?? snapshot.guardCount, 0),
    replayFailures: toNumber(snapshot.replay_failures ?? snapshot.replayFailures, 0),
    hashChainFailures: toNumber(snapshot.hash_chain_failures ?? snapshot.hashChainFailures, 0),
    missingTraces: toNumber(snapshot.missing_traces ?? snapshot.missingTraces, 0),
    riskScore: toNumber(snapshot.risk_score ?? snapshot.riskScore, 0),
    riskLevel: snapshot.risk_level || snapshot.riskLevel || "unknown",
    confidence: toNumber(snapshot.confidence, 0),
    stabilityIndex: toNumber(snapshot.stability_index ?? snapshot.stabilityIndex, 0),
    recommendedActions:
      snapshot.recommended_actions || snapshot.recommendedActions || snapshot.playbook || [],
    watchItems: snapshot.watch_items || snapshot.watchItems || [],
    snapshotHash: snapshot.snapshot_hash || snapshot.snapshotHash || "",
    windowBucket: snapshot.window_bucket || snapshot.windowBucket || "",
    createdAt: snapshot.created_at || snapshot.createdAt || "",
    payload: snapshot.payload || {},
  };
}

function normalizeDecisionArchive(payload) {
  if (!payload) {
    return null;
  }

  const historyItems = Array.isArray(payload.history?.items)
    ? payload.history.items
    : Array.isArray(payload.history)
      ? payload.history
      : [];
  const current = payload.current
    ? {
        ...payload.current,
        decisionType:
          payload.current.decision_type || payload.current.decisionType || "operator_decision",
        decisionLane:
          payload.current.decision_lane || payload.current.decisionLane || "observe",
        decisionAction:
          payload.current.decision_action || payload.current.decisionAction || "continue_monitoring",
        decisionPriority:
          payload.current.decision_priority || payload.current.decisionPriority || "low",
        decisionSummary:
          payload.current.decision_summary || payload.current.decisionSummary || "",
        trustScore: toNumber(payload.current.trust_score ?? payload.current.trustScore, 0),
        trustHealth: toNumber(payload.current.trust_health ?? payload.current.trustHealth, 0),
        replayHealthScore: toNumber(
          payload.current.replay_health_score ?? payload.current.replayHealthScore,
          0,
        ),
        evidenceCoverage: toNumber(
          payload.current.evidence_coverage ?? payload.current.evidenceCoverage,
          0,
        ),
        exceptionPressure: toNumber(
          payload.current.exception_pressure ?? payload.current.exceptionPressure,
          0,
        ),
        alertCount: toNumber(payload.current.alert_count ?? payload.current.alertCount, 0),
        guardCount: toNumber(payload.current.guard_count ?? payload.current.guardCount, 0),
        replayFailures: toNumber(payload.current.replay_failures ?? payload.current.replayFailures, 0),
        hashChainFailures: toNumber(
          payload.current.hash_chain_failures ?? payload.current.hashChainFailures,
          0,
        ),
        missingTraces: toNumber(payload.current.missing_traces ?? payload.current.missingTraces, 0),
        riskScore: toNumber(payload.current.risk_score ?? payload.current.riskScore, 0),
        riskLevel: payload.current.risk_level || payload.current.riskLevel || "unknown",
        confidence: toNumber(payload.current.confidence, 0),
        stabilityIndex: toNumber(
          payload.current.stability_index ?? payload.current.stabilityIndex,
          0,
        ),
        recommendedActions:
          payload.current.recommended_actions ||
          payload.current.recommendedActions ||
          payload.current.playbook ||
          [],
        watchItems: payload.current.watch_items || payload.current.watchItems || [],
        advisoryOnly: payload.current.advisory_only ?? payload.current.advisoryOnly ?? true,
        executionAuthority:
          payload.current.execution_authority ?? payload.current.executionAuthority ?? false,
        signals: payload.current.signals || {},
        reasoning: payload.current.reasoning || {},
        analyticsLatest: payload.current.analytics_latest
          ? normalizeAnalyticsSnapshot(payload.current.analytics_latest)
          : null,
        latestRecordId: payload.current.latest_record_id || payload.current.latestRecordId || null,
        readOnly: true,
        projectionOnly: true,
      }
    : null;

  const latest = payload.latest ? normalizeDecisionSnapshot(payload.latest) : null;

  return {
    ...payload,
    current,
    latest,
    history: {
      ...(payload.history || {}),
      items: historyItems.map(normalizeDecisionSnapshot),
      source_breakdown: payload.history?.source_breakdown || {},
    },
    signals: payload.signals || current?.signals || {},
    readOnly: payload.read_only ?? payload.readOnly ?? true,
    projectionOnly: payload.projection_only ?? payload.projectionOnly ?? true,
  };
}

function normalizeActionSnapshot(snapshot) {
  if (!snapshot) {
    return null;
  }

  const decisionQuality = snapshot.decision_quality || {};

  return {
    actionId: snapshot.action_id || snapshot.actionId || "",
    organizationId: snapshot.organization_id || snapshot.organizationId || "",
    source: snapshot.source || "unknown",
    actionType: snapshot.action_type || snapshot.actionType || "controlled_autonomous_action",
    decisionId: snapshot.decision_id || snapshot.decisionId || "",
    decisionLane: snapshot.decision_lane || snapshot.decisionLane || "observe",
    decisionPriority: snapshot.decision_priority || snapshot.decisionPriority || "low",
    actionLane: snapshot.action_lane || snapshot.actionLane || "monitor",
    actionMode: snapshot.action_mode || snapshot.actionMode || "guided_control",
    actionPriority: snapshot.action_priority || snapshot.actionPriority || "low",
    actionSummary: snapshot.action_summary || snapshot.actionSummary || "",
    controlSignal: snapshot.control_signal || snapshot.controlSignal || "maintain_monitoring",
    safetyGate: snapshot.safety_gate || snapshot.safetyGate || "pass",
    automationTier: toNumber(snapshot.automation_tier ?? snapshot.automationTier, 0),
    executionTier:
      snapshot.execution_tier ||
      snapshot.executionTier ||
      snapshot.payload?.action?.execution_tier ||
      snapshot.payload?.action?.executionTier ||
      "advisory",
    executionTierReady:
      snapshot.execution_tier_ready ??
      snapshot.executionTierReady ??
      snapshot.payload?.action?.execution_tier_ready ??
      snapshot.payload?.action?.executionTierReady ??
      false,
    executionTierSummary:
      snapshot.execution_tier_summary ||
      snapshot.executionTierSummary ||
      snapshot.payload?.action?.execution_tier_summary ||
      snapshot.payload?.action?.executionTierSummary ||
      "",
    executionTierControls:
      snapshot.execution_tier_controls ||
      snapshot.executionTierControls ||
      snapshot.payload?.action?.execution_tier_controls ||
      snapshot.payload?.action?.executionTierControls ||
      [],
    decisionQualityScore: toNumber(
      snapshot.decision_quality_score ?? snapshot.decisionQualityScore ?? decisionQuality.score,
      0,
    ),
    evidenceAlignmentScore: toNumber(
      snapshot.evidence_alignment_score ??
        snapshot.evidenceAlignmentScore ??
        decisionQuality.evidence_alignment_score ??
        decisionQuality.evidenceAlignmentScore,
      0,
    ),
    calibratedConfidence: toNumber(
      snapshot.calibrated_confidence ??
        snapshot.calibratedConfidence ??
        decisionQuality.calibrated_confidence ??
        decisionQuality.calibratedConfidence,
      0,
    ),
    historyAlignmentScore: toNumber(
      snapshot.history_alignment_score ??
        snapshot.historyAlignmentScore ??
        decisionQuality.history_alignment_score ??
        decisionQuality.historyAlignmentScore,
      0,
    ),
    qualityBand:
      snapshot.quality_band ||
      snapshot.qualityBand ||
      decisionQuality.band ||
      "unknown",
    trustScore: toNumber(snapshot.trust_score ?? snapshot.trustScore, 0),
    trustHealth: toNumber(snapshot.trust_health ?? snapshot.trustHealth, 0),
    replayHealthScore: toNumber(snapshot.replay_health_score ?? snapshot.replayHealthScore, 0),
    evidenceCoverage: toNumber(snapshot.evidence_coverage ?? snapshot.evidenceCoverage, 0),
    exceptionPressure: toNumber(snapshot.exception_pressure ?? snapshot.exceptionPressure, 0),
    alertCount: toNumber(snapshot.alert_count ?? snapshot.alertCount, 0),
    guardCount: toNumber(snapshot.guard_count ?? snapshot.guardCount, 0),
    replayFailures: toNumber(snapshot.replay_failures ?? snapshot.replayFailures, 0),
    hashChainFailures: toNumber(snapshot.hash_chain_failures ?? snapshot.hashChainFailures, 0),
    missingTraces: toNumber(snapshot.missing_traces ?? snapshot.missingTraces, 0),
    stabilityIndex: toNumber(snapshot.stability_index ?? snapshot.stabilityIndex, 0),
    recommendedActions:
      snapshot.recommended_actions || snapshot.recommendedActions || snapshot.control_actions || [],
    watchItems: snapshot.watch_items || snapshot.watchItems || [],
    controlActions: snapshot.control_actions || snapshot.controlActions || [],
    operatorGuidance: snapshot.operator_guidance || snapshot.operatorGuidance || [],
    signals: snapshot.signals || {},
    reasoning: snapshot.reasoning || {},
    decision: snapshot.decision ? normalizeDecisionSnapshot(snapshot.decision) : null,
    decisionQuality:
      snapshot.decision_quality || snapshot.decisionQuality
        ? {
            score: toNumber(decisionQuality.score ?? snapshot.decision_quality_score, 0),
            band:
              decisionQuality.band ||
              snapshot.quality_band ||
              snapshot.qualityBand ||
              "unknown",
            calibratedConfidence: toNumber(
              decisionQuality.calibrated_confidence ??
                decisionQuality.calibratedConfidence ??
                snapshot.calibrated_confidence ??
                snapshot.calibratedConfidence,
              0,
            ),
            evidenceAlignmentScore: toNumber(
              decisionQuality.evidence_alignment_score ??
                decisionQuality.evidenceAlignmentScore ??
                snapshot.evidence_alignment_score ??
                snapshot.evidenceAlignmentScore,
              0,
            ),
            historyAlignmentScore: toNumber(
              decisionQuality.history_alignment_score ??
                decisionQuality.historyAlignmentScore ??
                snapshot.history_alignment_score ??
                snapshot.historyAlignmentScore,
              0,
            ),
            trustAlignmentScore: toNumber(
              decisionQuality.trust_alignment_score ??
                decisionQuality.trustAlignmentScore ??
                snapshot.trust_health,
              0,
            ),
            replayAlignmentScore: toNumber(
              decisionQuality.replay_alignment_score ??
                decisionQuality.replayAlignmentScore ??
                snapshot.replay_health_score,
              0,
            ),
            evidenceCalibrated:
              decisionQuality.evidence_calibrated ?? decisionQuality.evidenceCalibrated ?? true,
            summary: decisionQuality.summary || snapshot.action_summary || "",
          }
        : {
            score: toNumber(snapshot.decision_quality_score ?? snapshot.decisionQualityScore, 0),
            band: snapshot.quality_band || snapshot.qualityBand || "unknown",
            calibratedConfidence: toNumber(
              snapshot.calibrated_confidence ?? snapshot.calibratedConfidence,
              0,
            ),
            evidenceAlignmentScore: toNumber(
              snapshot.evidence_alignment_score ?? snapshot.evidenceAlignmentScore,
              0,
            ),
            historyAlignmentScore: toNumber(
              snapshot.history_alignment_score ?? snapshot.historyAlignmentScore,
              0,
            ),
            trustAlignmentScore: toNumber(snapshot.trust_health ?? snapshot.trustHealth, 0),
            replayAlignmentScore: toNumber(
              snapshot.replay_health_score ?? snapshot.replayHealthScore,
              0,
            ),
            evidenceCalibrated: true,
            summary: snapshot.action_summary || "",
          },
    snapshotHash: snapshot.snapshot_hash || snapshot.snapshotHash || "",
    windowBucket: snapshot.window_bucket || snapshot.windowBucket || "",
    createdAt: snapshot.created_at || snapshot.createdAt || "",
    payload: snapshot.payload || {},
    readOnly: true,
    projectionOnly: true,
    advisoryOnly: true,
  };
}

function normalizeActionArchive(payload) {
  if (!payload) {
    return null;
  }

  const historyItems = Array.isArray(payload.history?.items)
    ? payload.history.items
    : Array.isArray(payload.history)
      ? payload.history
      : [];
  const current = payload.current
    ? normalizeActionSnapshot(payload.current)
    : null;
  const latest = payload.latest ? normalizeActionSnapshot(payload.latest) : null;

  return {
    ...payload,
    current,
    latest,
    history: {
      ...(payload.history || {}),
      items: historyItems.map(normalizeActionSnapshot),
      source_breakdown: payload.history?.source_breakdown || {},
    },
    signals: payload.signals || current?.signals || current?.decisionQuality || {},
    reasoning: payload.reasoning || current?.reasoning || {},
    readOnly: payload.read_only ?? payload.readOnly ?? true,
    projectionOnly: payload.projection_only ?? payload.projectionOnly ?? true,
  };
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

function deriveOperationAIDecisionState({
  decision,
  action,
  liveAnalyticsSnapshot,
  novarideOperatorDashboardContract,
  novarideEcosystem,
  liveNotifications,
  activeRidesCount,
}) {
  const lane = decision?.decisionLane || action?.decisionLane || "observe";
  const laneTone = decisionLaneTone(lane);
  const priority = decision?.decisionPriority || action?.decisionPriority || "low";
  const confidence = Number(action?.calibratedConfidence ?? decision?.confidence ?? 0);
  const trustHealth = toNumber(
    action?.trustHealth ?? decision?.trustHealth ?? liveAnalyticsSnapshot?.trustHealth,
    0,
  );
  const replayHealth = toNumber(
    action?.replayHealthScore ?? decision?.replayHealthScore ?? liveAnalyticsSnapshot?.replayHealthScore,
    0,
  );
  const evidenceCoverage = toNumber(
    action?.evidenceCoverage ?? decision?.evidenceCoverage ?? liveAnalyticsSnapshot?.evidenceCoverage,
    0,
  );
  const exceptionPressure = toNumber(
    action?.exceptionPressure ?? decision?.exceptionPressure ?? liveAnalyticsSnapshot?.exceptionPressure,
    0,
  );
  const alertCount = toNumber(
    action?.alertCount ?? decision?.alertCount ?? liveAnalyticsSnapshot?.alertCount,
    0,
  );
  const guardCount = toNumber(
    action?.guardCount ?? decision?.guardCount ?? liveAnalyticsSnapshot?.guardCount,
    0,
  );
  const activeDrivers = toNumber(liveAnalyticsSnapshot?.onlineDrivers, 0);
  const driverCount = toNumber(liveAnalyticsSnapshot?.driverCount, 0);
  const completedRides = toNumber(liveAnalyticsSnapshot?.completedRides, 0);
  const demandPressure = clampNumber(
    Math.round(
      activeRidesCount * 12 +
        alertCount * 8 +
        guardCount * 10 +
        exceptionPressure * 4 +
        (100 - evidenceCoverage) * 0.25 +
        (100 - trustHealth) * 0.2 -
        activeDrivers * 5,
    ),
    0,
    100,
  );

  const demandLabel = demandPressure >= 75 ? "High" : demandPressure >= 45 ? "Moderate" : "Stable";
  const driverSupplyLabel = `${activeDrivers} online / ${driverCount || activeDrivers || 0} known`;

  let dispatchPosture = "Maintain current dispatch band";
  if (lane === "escalate") {
    dispatchPosture = "Freeze non-essential dispatch";
  } else if (lane === "review") {
    dispatchPosture = "Open operator review before widening dispatch";
  } else if (lane === "watch") {
    dispatchPosture = "Increase observation around dispatch pressure";
  } else if (demandPressure >= 70 && activeDrivers > 0) {
    dispatchPosture = "Prioritize driver supply to the busiest zone";
  } else if (demandPressure >= 70) {
    dispatchPosture = "Hold new dispatch until supply returns";
  }

  const operatorMove =
    action?.controlActions?.[0] ||
    decision?.recommendedActions?.[0] ||
    (lane === "escalate"
      ? "Escalate the incident, isolate the affected window, and hold non-essential changes."
      : lane === "review"
        ? "Review replay pressure, evidence gaps, and driver supply before widening activity."
        : demandPressure >= 70
          ? "Shift drivers toward the busiest corridor and keep operator watch active."
          : "Maintain the replay-backed operating band and continue live sampling.");

  const summary =
    decision?.decisionSummary ||
    action?.actionSummary ||
    "The operation AI engine is waiting for the next persisted operator window.";

  const watchItems = [
    ...(decision?.watchItems || []),
    ...(action?.watchItems || []),
    ...(liveNotifications || []).map((notification) => notification.title),
  ].filter(Boolean);

  const moduleCount = Array.isArray(novarideOperatorDashboardContract?.modules)
    ? novarideOperatorDashboardContract.modules.length
    : 0;

  return {
    lane,
    laneTone,
    priority,
    confidence,
    trustHealth,
    replayHealth,
    evidenceCoverage,
    exceptionPressure,
    alertCount,
    guardCount,
    activeRidesCount,
    activeDrivers,
    driverCount,
    completedRides,
    demandPressure,
    demandLabel,
    driverSupplyLabel,
    dispatchPosture,
    operatorMove,
    summary,
    controlSignal: action?.controlSignal || decision?.decisionAction || "maintain_monitoring",
    safetyGate: action?.safetyGate || "pass",
    executionTier: action?.executionTier || "advisory",
    executionTierReady: Boolean(action?.executionTierReady),
    ecosystemApps: toNumber(novarideEcosystem?.app_count, 0),
    moduleCount,
    recommendedActions: (action?.controlActions || decision?.recommendedActions || []).slice(0, 4),
    watchItems: Array.from(new Set(watchItems)).slice(0, 6),
  };
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parsePercent(value, fallback = 0) {
  if (typeof value === "string") {
    const match = value.match(/(\d+(?:\.\d+)?)/);
    if (match) {
      return toNumber(match[1], fallback);
    }
  }
  return toNumber(value, fallback);
}

function clampNumber(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function buildLiveAnalyticsSnapshot({
  trustMetrics,
  replayHealth,
  evidence,
  pilotMetrics,
  observabilityDashboard,
  guards,
  drivers,
  activeRides,
  liveEvents,
}) {
  const timestamp = new Date().toLocaleTimeString();
  const trustScore = toNumber(trustMetrics?.trust_score, 0);
  const replayFailures = toNumber(replayHealth?.failures, 0);
  const hashChainFailures = toNumber(replayHealth?.hash_chain_failures, 0);
  const replaySuccessRate = parsePercent(replayHealth?.replay_success_rate, 100);
  const missingTraces = toNumber(evidence?.missing_traces, 0);
  const receiptsCount = toNumber(evidence?.receipts_count, 0);
  const traceCount = toNumber(evidence?.trace_count, 0);
  const completedRides = toNumber(pilotMetrics?.completed_rides, 0);
  const totalRides = toNumber(
    pilotMetrics?.total_rides,
    activeRides.length > 0 ? activeRides.length : completedRides,
  );
  const onlineDrivers = drivers.filter((driver) => driver.status === "ONLINE").length;
  const driverCount = drivers.length;
  const guardCount = guards.length;
  const alertCount = toNumber(observabilityDashboard?.alerts?.length, 0);
  const exceptionCount = replayFailures + hashChainFailures + missingTraces + guardCount;
  const evidenceCoverage =
    traceCount > 0
      ? clampNumber(Math.round((receiptsCount / traceCount) * 100), 0, 100)
      : receiptsCount > 0
        ? 100
        : 0;
  const trustHealth = clampNumber(
    trustScore - replayFailures * 14 - missingTraces * 5 - guardCount * 8,
    0,
    100,
  );
  const replayHealthScore = clampNumber(
    replaySuccessRate - replayFailures * 18 - hashChainFailures * 14 - missingTraces * 6 - guardCount * 8,
    0,
    100,
  );
  const alertTone =
    exceptionCount > 0
      ? "critical"
      : trustScore >= 90
        ? "good"
        : "warn";

  const notifications = buildOperatorNotifications({
    timestamp,
    trustScore,
    replayFailures,
    hashChainFailures,
    replaySuccessRate,
    missingTraces,
    guardCount,
    alertCount,
    liveEvents,
  });

  return {
    timestamp,
    trustScore,
    trustHealth,
    replayFailures,
    hashChainFailures,
    replaySuccessRate,
    missingTraces,
    receiptsCount,
    traceCount,
    completedRides,
    totalRides,
    onlineDrivers,
    driverCount,
    guardCount,
    alertCount,
    exceptionCount,
    evidenceCoverage,
    replayHealthScore,
    alertTone,
    notifications,
  };
}

function buildOperatorNotifications({
  timestamp,
  trustScore,
  replayFailures,
  hashChainFailures,
  missingTraces,
  guardCount,
  alertCount,
  decisionLane,
  decisionSummary,
  decisionQualityScore,
  decisionQualityBand,
  controlSignal,
  safetyGate,
  calibratedConfidence,
  executionTier,
  executionTierReady,
  liveEvents,
}) {
  const notifications = [];

  if (replayFailures > 0 || hashChainFailures > 0) {
    notifications.push({
      id: "replay-exception",
      severity: replayFailures + hashChainFailures > 1 ? "critical" : "warning",
      title: "Replay exception detected",
      detail: `${replayFailures} replay failure(s) and ${hashChainFailures} hash-chain issue(s) are present in the current trust window.`,
      source: "Replay health",
      timestamp,
    });
  }

  if (missingTraces > 0) {
    notifications.push({
      id: "pilot-evidence-gap",
      severity: "warning",
      title: "Pilot evidence gap",
      detail: `${missingTraces} trace(s) are missing from the current evidence pipeline snapshot.`,
      source: "Evidence pipeline",
      timestamp,
    });
  }

  if (trustScore > 0 && trustScore < 90) {
    notifications.push({
      id: "trust-drift",
      severity: trustScore < 80 ? "critical" : "warning",
      title: "Trust score softened",
      detail: `Current trust score is ${trustScore}. The live analytics trail is below the preferred operating band.`,
      source: "Trust metrics",
      timestamp,
    });
  }

  if (guardCount > 0) {
    notifications.push({
      id: "guard-violations",
      severity: guardCount > 2 ? "critical" : "warning",
      title: "Operator guard violations",
      detail: `${guardCount} guard violation(s) are currently visible on the control surface.`,
      source: "Governance guardrail",
      timestamp,
    });
  }

  if (alertCount > 0) {
    notifications.push({
      id: "observability-alerts",
      severity: alertCount > 2 ? "critical" : "warning",
      title: "Observability alerts present",
      detail: `${alertCount} operator alert(s) were published by the observability dashboard.`,
      source: "Observability dashboard",
      timestamp,
    });
  }

  if (decisionLane === "review" || decisionLane === "escalate") {
    notifications.push({
      id: "decision-engine",
      severity: decisionLane === "escalate" ? "critical" : "warning",
      title:
        decisionLane === "escalate"
          ? "Decision engine escalated review"
          : "Decision engine opened operator review",
      detail:
        decisionSummary ||
        "The AI decision engine recommends operator review for the current trust window.",
      source: "AI decision engine",
      timestamp,
    });
  }

  if (
    safetyGate === "hold" ||
    decisionQualityBand === "weak" ||
    (Number.isFinite(decisionQualityScore) && decisionQualityScore > 0 && decisionQualityScore < 70)
  ) {
    notifications.push({
      id: "action-quality-calibration",
      severity: safetyGate === "hold" || decisionQualityScore < 55 ? "critical" : "warning",
      title:
        safetyGate === "hold"
          ? "Autonomous action engine held"
          : "Decision quality calibration weakened",
      detail:
        safetyGate === "hold"
          ? "The controlled autonomous action engine is in hold mode until evidence alignment improves."
          : `Decision quality is ${decisionQualityScore || 0}/100 with ${decisionQualityBand || "unknown"} calibration${calibratedConfidence ? ` and ${Math.round(calibratedConfidence * 100)}% calibrated confidence` : ""}.`,
      source: controlSignal || "Action calibration",
      timestamp,
    });
  }

  if (controlSignal === "require_operator_review") {
    notifications.push({
      id: "action-review-required",
      severity: "warning",
      title: "Operator review required",
      detail:
        "The action engine is advisory-only and is requesting operator review before any higher-risk handling.",
      source: "Action control signal",
      timestamp,
    });
  }

  if (executionTierReady || executionTier === "controlled") {
    notifications.push({
      id: "controlled-execution-tier",
      severity: executionTierReady ? "info" : "warning",
      title:
        executionTierReady
          ? "Controlled execution tier enabled"
          : "Controlled execution tier pending",
      detail:
        executionTierReady
          ? "Decision quality and evidence alignment are strong enough for operator-supervised limited automation proposals."
          : "The system is approaching a controlled execution tier, but the safety gate or calibrated confidence is not yet strong enough.",
      source: "Controlled autonomy",
      timestamp,
    });
  }

  liveEvents
    .filter((event) => event.type || event.data?.source || event.data?.summary || event.data?.status)
    .slice(0, 4)
    .forEach((event, index) => {
      notifications.push({
        id: `live-event-${index}`,
        severity: event.type && String(event.type).includes("ALERT") ? "warning" : "info",
        title: event.type || "Dashboard event",
        detail:
          typeof event.data?.source === "string"
            ? event.data.source
            : event.channel || "Live dashboard stream event",
        source: "WebSocket stream",
        timestamp,
      });
    });

  return notifications.slice(0, 8);
}

function appendAnalyticsTrail(trail, snapshot) {
  return [...trail, snapshot].slice(-MAX_ANALYTICS_POINTS);
}

function chartPoints(series, key) {
  return series.map((point) => toNumber(point[key], 0));
}

function buildPolylinePath(values, width, height, padding = 8) {
  if (values.length === 0) {
    return "";
  }

  const max = Math.max(...values);
  const min = Math.min(...values);
  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;
  const step = values.length > 1 ? innerWidth / (values.length - 1) : innerWidth;
  const range = max === min ? 0 : max - min;

  return values
    .map((value, index) => {
      const x = padding + step * index;
      const normalized = range === 0 ? 0.5 : (value - min) / range;
      const y = height - padding - normalized * innerHeight;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function buildAreaPath(values, width, height, padding = 8) {
  if (values.length === 0) {
    return "";
  }

  const max = Math.max(...values);
  const min = Math.min(...values);
  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;
  const step = values.length > 1 ? innerWidth / (values.length - 1) : innerWidth;
  const range = max === min ? 0 : max - min;

  const topPath = values
    .map((value, index) => {
      const x = padding + step * index;
      const normalized = range === 0 ? 0.5 : (value - min) / range;
      const y = height - padding - normalized * innerHeight;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
  const closingPoints = [
    `L${(padding + innerWidth).toFixed(2)},${(height - padding).toFixed(2)}`,
    `L${padding.toFixed(2)},${(height - padding).toFixed(2)}`,
    "Z",
  ];
  return `${topPath} ${closingPoints.join(" ")}`;
}

export default function OperatorDashboard() {
  const [state, setState] = useState(EMPTY_OPERATOR_STATE);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [liveConnection, setLiveConnection] = useState("connecting");
  const [liveEvents, setLiveEvents] = useState([]);
  const [analyticsTrail, setAnalyticsTrail] = useState([]);
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
  const [controlledExecutionBusy, setControlledExecutionBusy] = useState(false);
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

  useEffect(() => {
    let socket = null;
    let cancelled = false;

    operatorToken()
      .then((token) => {
        if (cancelled) {
          return;
        }

        socket = connectDashboardRealtime(token, {
          onOpen: () => setLiveConnection("connected"),
          onClose: () => setLiveConnection("disconnected"),
          onError: () => setLiveConnection("error"),
          onMessage: (message) => {
            setLiveConnection("connected");
            setLiveEvents((current) => [message, ...current].slice(0, 8));
            setLastUpdated(new Date().toISOString());
            if (message?.data?.summary && typeof message.data.summary === "object") {
              setError(null);
            }
          },
        });
      })
      .catch(() => {
        if (!cancelled) {
          setLiveConnection("error");
        }
      });

    return () => {
      cancelled = true;
      if (socket) {
        socket.close();
      }
    };
  }, []);

  async function fetchOperatorState() {
    try {
      const organizationId = state.novatechSaas?.organization_id || "org-nova";
      const [
        systemHealthResult,
        activeRidesResult,
        driversResult,
        replayHealthResult,
        evidenceResult,
        guardsResult,
        trustMetricsResult,
        pilotMetricsResult,
        observabilityDashboardResult,
        auditDashboardResult,
        publicTrustDashboardResult,
        operatorAnalyticsResult,
        operatorDecisionsResult,
        operatorActionsResult,
        novatechPlatformResult,
        novatechSaasResult,
        novatechOutcomeStatusResult,
        novatechTrustNetworkResult,
        novatechMarketplaceResult,
        novatechDocumentationComplianceResult,
        novatechControlledExecutionActivationResult,
        novatechMarketplaceOnboardingResult,
        novapayLiveTestReadinessResult,
        novarideEcosystemResult,
        novaridePlatformArchitectureContractResult,
        novarideOperatorDashboardContractResult,
        operatorAutonomyResult,
        novarideFleetManagerContractResult,
        novarideBusinessPortalContractResult,
        novarideAdminContractResult,
        novarideInspectorAppContractResult,
        novarideSupportContractResult,
        novaridePhase11StatusResult,
        novaridePhase12StatusResult,
        novaridePhase13StatusResult,
        novaridePartnerPortalContractResult,
        operatorCityAutomationResult,
        operatorMultiCityOrchestrationResult,
        operatorDigitalTwinResult,
        operatorMetaLearningRedesignResult,
        operatorDemandForecastResult,
        operatorStrategyEngineResult,
        operatorBusinessPricingResult,
        operatorCityProfitOptimizationResult,
      ] = await Promise.allSettled([
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
        readJson("/v1/operator/analytics"),
        readJson("/v1/operator/decisions"),
        readJson("/v1/operator/actions"),
        readJson("/v1/novatech/intranet/platform"),
        readJson("/v1/novatech/saas/status"),
        readJson("/v1/novatech/outcomes/status"),
        readJson("/v1/novatech/trust-network/status"),
        readJson("/v1/novatech/marketplace/status"),
        readJson("/v1/novatech/documentation/status"),
        readJson(`/v1/novatech/organizations/${organizationId}/execution/activation`),
        readJson("/v1/novatech/marketplace/onboarding"),
        readJson("/v1/core-platform/transfers/live-test/readiness"),
        readJson("/v1/novaride/ecosystem"),
        readJson("/v1/novaride/platform/architecture-contract"),
        readJson("/v1/novaride/operator/dashboard-contract"),
        readJson("/v1/operator/autonomy"),
        readJson("/v1/novaride/fleet/manager-contract"),
        readJson("/v1/novaride/business/portal-contract"),
        readJson("/v1/novaride/admin/contract"),
        readJson("/v1/novaride/inspector/app-contract"),
        readJson("/v1/novaride/support/contract"),
        readJson("/v1/novaride/phase11/status"),
        readJson("/v1/novaride/phase12/status"),
        readJson("/v1/novaride/phase13/status"),
        readJson("/v1/novaride/partner/portal-contract"),
        readJson("/v1/operator/city-automation"),
        readJson("/v1/operator/multi-city-orchestration"),
        readJson("/v1/operator/digital-twin"),
        readJson("/v1/operator/meta-learning-redesign"),
        readJson("/v1/operator/demand-forecast"),
        readJson("/v1/operator/strategy-engine"),
        readJson("/v1/operator/business-pricing"),
        readJson("/v1/operator/city-profit-optimization"),
      ]);

      const activeRides =
        activeRidesResult.status === "fulfilled"
          ? normalizeActiveRides(activeRidesResult.value)
          : state.activeRides;
      const drivers =
        driversResult.status === "fulfilled" ? normalizeDrivers(driversResult.value) : state.drivers;
      const replayHealth =
        replayHealthResult.status === "fulfilled" ? replayHealthResult.value : state.replayHealth;
      const evidence =
        evidenceResult.status === "fulfilled" ? evidenceResult.value : state.evidence;
      const guards =
        guardsResult.status === "fulfilled" ? normalizeGuards(guardsResult.value) : state.guards;
      const trustMetrics =
        trustMetricsResult.status === "fulfilled" ? trustMetricsResult.value : state.trustMetrics;
      const pilotMetrics =
        pilotMetricsResult.status === "fulfilled" ? pilotMetricsResult.value : state.pilotMetrics;
      const observabilityDashboard =
        observabilityDashboardResult.status === "fulfilled"
          ? observabilityDashboardResult.value
          : state.observabilityDashboard;
      const auditDashboard =
        auditDashboardResult.status === "fulfilled"
          ? auditDashboardResult.value
          : state.auditDashboard;
      const publicTrustDashboard =
        publicTrustDashboardResult.status === "fulfilled"
          ? publicTrustDashboardResult.value
          : state.publicTrustDashboard;
      const analyticsArchive =
        operatorAnalyticsResult.status === "fulfilled"
          ? normalizeAnalyticsArchive(operatorAnalyticsResult.value)
          : state.analyticsArchive;
      const decisionArchive =
        operatorDecisionsResult.status === "fulfilled"
          ? normalizeDecisionArchive(operatorDecisionsResult.value)
          : state.decisionArchive;
      const actionArchive =
        operatorActionsResult.status === "fulfilled"
          ? normalizeActionArchive(operatorActionsResult.value)
          : state.actionArchive;
      const novatechOrgPlatform =
        novatechPlatformResult.status === "fulfilled"
          ? novatechPlatformResult.value
          : state.novatechOrgPlatform;
      const novatechSaas =
        novatechSaasResult.status === "fulfilled" ? novatechSaasResult.value : state.novatechSaas;
      const novatechOutcomeStatus =
        novatechOutcomeStatusResult.status === "fulfilled"
          ? novatechOutcomeStatusResult.value
          : state.novatechOutcomeStatus;
      const novatechTrustNetwork =
        novatechTrustNetworkResult.status === "fulfilled"
          ? novatechTrustNetworkResult.value
          : state.novatechTrustNetwork;
      const novatechMarketplace =
        novatechMarketplaceResult.status === "fulfilled"
          ? novatechMarketplaceResult.value
          : state.novatechMarketplace;
      const novatechDocumentationCompliance =
        novatechDocumentationComplianceResult.status === "fulfilled"
          ? novatechDocumentationComplianceResult.value
          : state.novatechDocumentationCompliance;
      const novatechControlledExecutionActivation =
        novatechControlledExecutionActivationResult.status === "fulfilled"
          ? novatechControlledExecutionActivationResult.value
          : state.novatechControlledExecutionActivation;
      const novatechMarketplaceOnboarding =
        novatechMarketplaceOnboardingResult.status === "fulfilled"
          ? novatechMarketplaceOnboardingResult.value
          : state.novatechMarketplaceOnboarding;
      const novapayLiveTestReadiness =
        novapayLiveTestReadinessResult.status === "fulfilled"
          ? novapayLiveTestReadinessResult.value
          : state.novapayLiveTestReadiness;
      const novarideEcosystem =
        novarideEcosystemResult.status === "fulfilled"
          ? novarideEcosystemResult.value
          : state.novarideEcosystem;
      const novaridePlatformArchitectureContract =
        novaridePlatformArchitectureContractResult.status === "fulfilled"
          ? novaridePlatformArchitectureContractResult.value
          : state.novaridePlatformArchitectureContract;
      const novarideOperatorDashboardContract =
        novarideOperatorDashboardContractResult.status === "fulfilled"
          ? novarideOperatorDashboardContractResult.value
          : state.novarideOperatorDashboardContract;
      const operatorAutonomy =
        operatorAutonomyResult.status === "fulfilled"
          ? operatorAutonomyResult.value
          : state.operatorAutonomy;
      const operatorCityAutomation =
        operatorCityAutomationResult.status === "fulfilled"
          ? operatorCityAutomationResult.value
          : state.operatorCityAutomation;
      const operatorMultiCityOrchestration =
        operatorMultiCityOrchestrationResult.status === "fulfilled"
          ? operatorMultiCityOrchestrationResult.value
          : state.operatorMultiCityOrchestration;
      const operatorDigitalTwin =
        operatorDigitalTwinResult.status === "fulfilled" ? operatorDigitalTwinResult.value : state.operatorDigitalTwin;
      const operatorMetaLearningRedesign =
        operatorMetaLearningRedesignResult.status === "fulfilled"
          ? operatorMetaLearningRedesignResult.value
          : state.operatorMetaLearningRedesign;
      const operatorDemandForecast =
        operatorDemandForecastResult.status === "fulfilled"
          ? operatorDemandForecastResult.value
          : state.operatorDemandForecast;
      const operatorStrategyEngine =
        operatorStrategyEngineResult.status === "fulfilled"
          ? operatorStrategyEngineResult.value
          : state.operatorStrategyEngine;
      const operatorBusinessPricing =
        operatorBusinessPricingResult.status === "fulfilled"
          ? operatorBusinessPricingResult.value
          : state.operatorBusinessPricing;
      const operatorCityProfitOptimization =
        operatorCityProfitOptimizationResult.status === "fulfilled"
          ? operatorCityProfitOptimizationResult.value
          : state.operatorCityProfitOptimization;
      const novarideFleetManagerContract =
        novarideFleetManagerContractResult.status === "fulfilled"
          ? novarideFleetManagerContractResult.value
          : state.novarideFleetManagerContract;
      const novarideBusinessPortalContract =
        novarideBusinessPortalContractResult.status === "fulfilled"
          ? novarideBusinessPortalContractResult.value
          : state.novarideBusinessPortalContract;
      const novarideAdminContract =
        novarideAdminContractResult.status === "fulfilled"
          ? novarideAdminContractResult.value
          : state.novarideAdminContract;
      const novarideInspectorAppContract =
        novarideInspectorAppContractResult.status === "fulfilled"
          ? novarideInspectorAppContractResult.value
          : state.novarideInspectorAppContract;
      const novarideSupportContract =
        novarideSupportContractResult.status === "fulfilled"
          ? novarideSupportContractResult.value
          : state.novarideSupportContract;
      const novaridePhase11Status =
        novaridePhase11StatusResult.status === "fulfilled"
          ? novaridePhase11StatusResult.value
          : state.novaridePhase11Status;
      const novaridePhase12Status =
        novaridePhase12StatusResult.status === "fulfilled"
          ? novaridePhase12StatusResult.value
          : state.novaridePhase12Status;
      const novaridePhase13Status =
        novaridePhase13StatusResult.status === "fulfilled"
          ? novaridePhase13StatusResult.value
          : state.novaridePhase13Status;
      const novaridePartnerPortalContract =
        novaridePartnerPortalContractResult.status === "fulfilled"
          ? novaridePartnerPortalContractResult.value
          : state.novaridePartnerPortalContract;
      const liveAnalytics = buildLiveAnalyticsSnapshot({
        trustMetrics,
        replayHealth,
        evidence,
        pilotMetrics,
        observabilityDashboard,
        guards,
        drivers,
        activeRides,
        liveEvents,
      });

      let systemHealth =
        systemHealthResult.status === "fulfilled" ? systemHealthResult.value : null;
      if (!systemHealth) {
        try {
          const fallbackHealth = await readJson("/health");
          systemHealth = {
            ...state.systemHealth,
            ...fallbackHealth,
            service: fallbackHealth.service || state.systemHealth?.service || "afriride-api",
            status: fallbackHealth.status || state.systemHealth?.status || "ok",
            active_rides: activeRides.length,
            completed_rides: state.systemHealth?.completed_rides || 0,
            drivers_online: drivers.filter((driver) => driver.status === "ONLINE").length,
            total_drivers: drivers.length,
            replay_failures: replayHealth.failures || 0,
            missing_traces: evidence.missing_traces || 0,
            hash_chain_failures: replayHealth.hash_chain_failures || 0,
            invariant_contract: state.systemHealth?.invariant_contract || "five-invariant-contract",
            enforcement_mode: state.systemHealth?.enforcement_mode || "metadata-only",
          };
        } catch {
          systemHealth = state.systemHealth;
        }
      }

      setState((current) => ({
        ...current,
        systemHealth,
        activeRides,
        drivers,
        replayHealth,
        evidence,
        guards,
        trustMetrics,
        pilotMetrics,
        observabilityDashboard,
        auditDashboard,
        publicTrustDashboard,
        novatechOrgPlatform,
        novatechSaas,
        novatechOutcomeStatus,
        novatechTrustNetwork,
        novatechMarketplace,
        novatechDocumentationCompliance,
        novatechControlledExecutionActivation,
        novatechMarketplaceOnboarding,
        novapayLiveTestReadiness,
        novarideEcosystem,
        novaridePlatformArchitectureContract,
        novarideOperatorDashboardContract,
        operatorAutonomy,
        novarideFleetManagerContract,
        novarideBusinessPortalContract,
        novarideAdminContract,
        novarideInspectorAppContract,
        novarideSupportContract,
        novaridePhase11Status,
        novaridePhase12Status,
        novaridePhase13Status,
        novaridePartnerPortalContract,
        operatorCityAutomation,
        operatorMultiCityOrchestration,
        operatorDigitalTwin,
        operatorMetaLearningRedesign,
        operatorDemandForecast,
        operatorStrategyEngine,
        operatorBusinessPricing,
        operatorCityProfitOptimization,
        liveAnalytics,
        analyticsArchive,
        decisionArchive,
        actionArchive,
      }));
      if (liveAnalytics) {
        setAnalyticsTrail((current) => appendAnalyticsTrail(current, liveAnalytics));
      }
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

  async function activateControlledExecution() {
    const organizationId = state.novatechSaas?.organization_id || "org-nova";
    setControlledExecutionBusy(true);
    try {
      await writeJson(`/v1/novatech/organizations/${organizationId}/execution/activate`, {
        acknowledged: true,
        requested_tier: "controlled",
        operator_note: "Operator acknowledged controlled execution readiness.",
      });
      await fetchOperatorState();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "controlled_execution_activation_failed");
    } finally {
      setControlledExecutionBusy(false);
    }
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
  const liveAnalyticsSnapshot = useMemo(
    () =>
      state.liveAnalytics ||
      buildLiveAnalyticsSnapshot({
        trustMetrics: state.trustMetrics,
        replayHealth: state.replayHealth,
        evidence: state.evidence,
        pilotMetrics: state.pilotMetrics,
        observabilityDashboard: state.observabilityDashboard,
        guards: state.guards,
        drivers: state.drivers,
        activeRides: state.activeRides,
        liveEvents,
      }),
    [
      state.liveAnalytics,
      state.trustMetrics,
      state.replayHealth,
      state.evidence,
      state.pilotMetrics,
      state.observabilityDashboard,
      state.guards,
      state.drivers,
      state.activeRides,
      liveEvents,
      ],
  );
  const afriprogScenario = useMemo(
    () =>
      AFRIPROG_DEMO_SCENARIOS.find((scenario) => scenario.key === afriprogScenarioKey) ||
      AFRIPROG_DEMO_SCENARIOS[0],
    [afriprogScenarioKey],
  );
  const persistedAnalyticsHistory = state.analyticsArchive?.history?.items || [];
  const persistedAnalyticsLatest =
    state.analyticsArchive?.latest ||
    (persistedAnalyticsHistory.length > 0
      ? persistedAnalyticsHistory[persistedAnalyticsHistory.length - 1]
      : null);
  const persistedAnalyticsInsights = state.analyticsArchive?.insights || [];
  const persistedAnalyticsPrediction = state.analyticsArchive?.prediction || null;
  const persistedAnalyticsTrend = state.analyticsArchive?.trend || null;
  const persistedAnalyticsSourceBreakdown =
    state.analyticsArchive?.history?.source_breakdown || {};
  const persistedDecisionHistory = state.decisionArchive?.history?.items || [];
  const persistedDecisionLatest =
    state.decisionArchive?.latest ||
    (persistedDecisionHistory.length > 0
      ? persistedDecisionHistory[persistedDecisionHistory.length - 1]
      : null);
  const persistedDecisionCurrent = state.decisionArchive?.current || persistedDecisionLatest;
  const persistedDecisionSourceBreakdown =
    state.decisionArchive?.history?.source_breakdown || {};
  const persistedActionHistory = state.actionArchive?.history?.items || [];
  const persistedActionLatest =
    state.actionArchive?.latest ||
    (persistedActionHistory.length > 0
      ? persistedActionHistory[persistedActionHistory.length - 1]
      : null);
  const persistedActionCurrent = state.actionArchive?.current || persistedActionLatest;
  const persistedActionSourceBreakdown = state.actionArchive?.history?.source_breakdown || {};
  const novatechOrgPlatform = state.novatechOrgPlatform;
  const novatechOrgPlatformSurfaces = novatechOrgPlatform?.surfaces || {};
  const novatechSaas = state.novatechSaas;
  const novatechSaasTenants = novatechSaas?.organizations || [];
  const novatechSaasBilling = novatechSaas?.billing || null;
  const novatechSaasBillingSurface = novatechSaas?.billing_surface || null;
  const novatechSaasExecution = novatechSaas?.safe_execution || null;
  const novatechCurrentTenant =
    novatechSaasTenants.find((tenant) => tenant.organization_id === novatechSaas?.organization_id) ||
    novatechSaasTenants[0] ||
    null;
  const novatechOutcomeStatus = state.novatechOutcomeStatus;
  const novatechOutcomeCurrent = novatechOutcomeStatus?.current || null;
  const novatechOutcomeRegistry = novatechOutcomeStatus?.registry || null;
  const novatechOutcomeLearning = novatechOutcomeStatus?.learning || null;
  const novatechOutcomeScoring = novatechOutcomeStatus?.scoring || null;
  const novatechOutcomeReplay = novatechOutcomeStatus?.replay || null;
  const novatechTrustNetwork = state.novatechTrustNetwork;
  const novatechMarketplace = state.novatechMarketplace;
  const novatechDocumentationCompliance = state.novatechDocumentationCompliance;
  const novatechControlledExecutionActivation = state.novatechControlledExecutionActivation;
  const novatechMarketplaceOnboarding = state.novatechMarketplaceOnboarding;
  const novapayLiveTestReadiness = state.novapayLiveTestReadiness;
  const novarideEcosystem = state.novarideEcosystem;
  const novaridePlatformArchitectureContract = state.novaridePlatformArchitectureContract;
  const novarideOperatorDashboardContract = state.novarideOperatorDashboardContract;
  const operatorAutonomy = state.operatorAutonomy;
  const novarideFleetManagerContract = state.novarideFleetManagerContract;
  const novarideBusinessPortalContract = state.novarideBusinessPortalContract;
  const novarideAdminContract = state.novarideAdminContract;
  const novarideInspectorAppContract = state.novarideInspectorAppContract;
  const novarideSupportContract = state.novarideSupportContract;
  const novaridePhase11Status = state.novaridePhase11Status;
  const novaridePhase12Status = state.novaridePhase12Status;
  const novaridePhase13Status = state.novaridePhase13Status;
  const novaridePartnerPortalContract = state.novaridePartnerPortalContract;
  const operatorCityAutomation = state.operatorCityAutomation;
  const operatorMultiCityOrchestration = state.operatorMultiCityOrchestration;
  const operatorDigitalTwin = state.operatorDigitalTwin;
  const operatorMetaLearningRedesign = state.operatorMetaLearningRedesign;
  const operatorDemandForecast = state.operatorDemandForecast;
  const operatorStrategyEngine = state.operatorStrategyEngine;
  const operatorBusinessPricing = state.operatorBusinessPricing;
  const operatorCityProfitOptimization = state.operatorCityProfitOptimization;
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
  const liveNotifications = useMemo(
    () =>
      buildOperatorNotifications({
        timestamp: new Date().toLocaleTimeString(),
        trustScore: toNumber(state.trustMetrics?.trust_score, 0),
        replayFailures: toNumber(state.replayHealth.failures, 0),
        hashChainFailures: toNumber(state.replayHealth.hash_chain_failures, 0),
        missingTraces: toNumber(state.evidence.missing_traces, 0),
        guardCount: state.guards.length,
        alertCount: toNumber(state.observabilityDashboard?.alerts?.length, 0),
        decisionLane: persistedDecisionCurrent?.decisionLane,
        decisionSummary: persistedDecisionCurrent?.decisionSummary,
        decisionQualityScore: persistedActionCurrent?.decisionQualityScore,
        decisionQualityBand: persistedActionCurrent?.qualityBand,
        controlSignal: persistedActionCurrent?.controlSignal,
        safetyGate: persistedActionCurrent?.safetyGate,
        calibratedConfidence: persistedActionCurrent?.calibratedConfidence,
        executionTier: persistedActionCurrent?.executionTier,
        executionTierReady: persistedActionCurrent?.executionTierReady,
        liveEvents,
      }),
    [
      state.trustMetrics,
      state.replayHealth,
      state.evidence,
      state.guards,
      state.observabilityDashboard,
      liveEvents,
      persistedDecisionCurrent,
      persistedActionCurrent,
    ],
  );
  const operationAIDecisionState = useMemo(
    () =>
      deriveOperationAIDecisionState({
        decision: persistedDecisionCurrent,
        action: persistedActionCurrent,
        liveAnalyticsSnapshot,
        novarideOperatorDashboardContract,
        novarideEcosystem,
        liveNotifications,
        activeRidesCount: state.activeRides.length,
      }),
    [
      persistedDecisionCurrent,
      persistedActionCurrent,
      liveAnalyticsSnapshot,
      novarideOperatorDashboardContract,
      novarideEcosystem,
      liveNotifications,
      state.activeRides.length,
    ],
  );

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
          <strong>NOVATECH OS</strong>
          <span>NovaTechSol / Nova Technology Solution</span>
        </div>
        <label className="os-search">
          <span>Search product, layer, route</span>
          <input defaultValue="NovaScript" aria-label="Search product, layer, route" />
        </label>
        <div className="verified-lock">Intranet ready</div>
      </header>

      <section className="section-band novatech-home-band" id="home">
        <div className="novatech-home-grid">
          <div className="hero-copy">
            <p className="eyebrow">NovaTech Platform</p>
            <h1>NovaTechSol / Nova Technology Solution</h1>
            <p className="hero-summary">
              One browser entrypoint for NovaProgramming, NovaScript, trust,
              infrastructure, identity, payments, and product lines. The browser
              shows the platform architecture first, then links into the live
              dashboards below.
            </p>
            <div className="hero-actions" aria-label="NovaTech navigation">
              <a className="button primary" href="/novatech/intranet/">
                Open Intranet
              </a>
              <a className="button secondary" href="/v1/novascript/dashboard">
                NovaScript
              </a>
              <a className="button secondary" href="/v1/novaprogramming/dashboard">
                NovaProgramming
              </a>
              <a className="button secondary" href="/v1/operator/dashboard">
                AfriRide Ops
              </a>
            </div>
          </div>

          <div className="trust-status">
            <p>Platform Snapshot</p>
            <strong>Core layers linked</strong>
            <span>
              NovaProgramming, NovaScript, NovaTrust, NovaPower, NovaID, and
              NovaPay are organized as a browser-first platform shell.
            </span>
            <div className="trust-meta">
              <span>Home: NovaTechSol</span>
              <span>Access: authenticated staff</span>
              <span>Authority: read-only portal</span>
            </div>
          </div>
        </div>
      </section>

      <nav className="layer-shell platform-nav" aria-label="NovaTech platform navigation">
        {NOVATECH_PLATFORM_NAV.map((item) => (
          <a key={item.label} href={item.href}>
            <strong>{item.label}</strong>
            <span>{item.detail}</span>
          </a>
        ))}
      </nav>

      <section className="section-band platform-band">
        <SectionIntro
          eyebrow="Platform Architecture"
          title="Core layers and product surfaces"
          question="Browser navigation is structured around the control layers first, then the vertical products underneath."
        />
        <OperatorPanel title="Unified Trust Operating Console">
          <div className="stack">
            <div className="record-card">
              <div className="record-card-header">
                <strong>NovaTechSol Core Flow</strong>
                <span>2026 platform wiring</span>
              </div>
              <p>
                Identity to authority to execution to payment to proof to intelligence to evolution,
                exposed as one browser entrypoint for the core platform only.
              </p>
              <div className="chip-row">
                {NOVATECH_CORE_FLOW.map((step) => (
                  <span key={step} className="surface-chip">{step}</span>
                ))}
              </div>
            </div>
            <div className="operator-grid dense-grid">
              {NOVATECH_CORE_CONSOLE_MODULES.map((module) => (
                <article key={module.key} className="record-card">
                  <div className="record-card-header">
                    <strong>{module.label}</strong>
                    <span>{module.metric}</span>
                  </div>
                  <p>{module.path}</p>
                </article>
              ))}
            </div>
          </div>
        </OperatorPanel>
        <OperatorPanel title="Console Wireframes">
          <div className="operator-grid dense-grid">
            {NOVATECH_CONSOLE_WIREFRAMES.map((wireframe) => (
              <article key={wireframe.screen} className="record-card">
                <div className="record-card-header">
                  <strong>{wireframe.title}</strong>
                  <span>{wireframe.screen}</span>
                </div>
                <div className="chip-row">
                  {wireframe.zones.map((zone) => (
                    <span key={zone} className="surface-chip">{zone}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </OperatorPanel>
        <div className="operator-grid">
          <OperatorPanel title="Core Platform Layers">
            <div className="stack">
              {NOVATECH_CORE_LAYERS.map((layer) => (
                <article key={layer.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{layer.name}</strong>
                    <span>{layer.status}</span>
                  </div>
                  <p>{layer.summary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">{layer.route}</span>
                  </div>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Vertical Products">
            <div className="stack">
              {NOVATECH_PRODUCT_LAYERS.map((product) => (
                <article key={product.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{product.name}</strong>
                    <span>{product.status}</span>
                  </div>
                  <p>{product.summary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">{product.route}</span>
                  </div>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band organization-band" id="organization">
        <SectionIntro
          eyebrow="Organization OS"
          title="NovaTech intranet, extranet, knowledge, workflows, and comms"
          question="The organization platform unifies internal control, external access, files, workflows, and messages behind one read-only browser surface."
        />
        {novatechOrgPlatform ? (
          <>
            <div className="metric-grid">
              <TrustMetric
                label="Intranet"
                value={novatechOrgPlatformSurfaces.intranet?.status || "ready"}
                helper={novatechOrgPlatformSurfaces.intranet?.summary || "Internal dashboards and control surfaces"}
                tone="success"
              />
              <TrustMetric
                label="Extranet"
                value={novatechOrgPlatformSurfaces.extranet?.status || "ready"}
                helper={novatechOrgPlatformSurfaces.extranet?.summary || "External proof and verification portals"}
                tone="success"
              />
              <TrustMetric
                label="Knowledge"
                value={novatechOrgPlatformSurfaces.knowledge?.project_count || 0}
                helper="Workspace projects, files, and document roots"
              />
              <TrustMetric
                label="Workflows"
                value={novatechOrgPlatformSurfaces.workflows?.workflow_count || 0}
                helper="Workflow templates and live instances"
              />
              <TrustMetric
                label="Comms"
                value={novatechOrgPlatformSurfaces.comms?.message_count || 0}
                helper="Read-only operational messages"
              />
            </div>
            <div className="operator-grid">
              <OperatorPanel title="Intranet">
                <div className="stack">
                  <article className="record-card">
                    <div className="record-card-header">
                      <strong>{novatechOrgPlatformSurfaces.intranet?.title || "NovaTech Intranet"}</strong>
                      <span>{novatechOrgPlatformSurfaces.intranet?.status || "ready"}</span>
                    </div>
                    <p>{novatechOrgPlatformSurfaces.intranet?.summary}</p>
                    <div className="chip-row">
                      <span className="surface-chip">
                        {novatechOrgPlatformSurfaces.intranet?.route || "/novatech/intranet/"}
                      </span>
                      {Object.values(novatechOrgPlatformSurfaces.intranet?.dashboards || {}).map((route) => (
                        <span key={route} className="surface-chip">
                          {route}
                        </span>
                      ))}
                    </div>
                  </article>
                </div>
              </OperatorPanel>

              <OperatorPanel title="Extranet">
                <div className="stack">
                  <article className="record-card">
                    <div className="record-card-header">
                      <strong>{novatechOrgPlatformSurfaces.extranet?.title || "NovaTech Extranet"}</strong>
                      <span>{novatechOrgPlatformSurfaces.extranet?.status || "ready"}</span>
                    </div>
                    <p>{novatechOrgPlatformSurfaces.extranet?.summary}</p>
                    <div className="chip-row">
                      {(novatechOrgPlatformSurfaces.extranet?.audiences || []).map((audience) => (
                        <span key={audience} className="surface-chip">
                          {audience}
                        </span>
                      ))}
                    </div>
                    <div className="chip-row">
                      {(novatechOrgPlatformSurfaces.extranet?.routes || []).map((route) => (
                        <span key={route} className="surface-chip">
                          {route}
                        </span>
                      ))}
                    </div>
                  </article>
                </div>
              </OperatorPanel>

              <OperatorPanel title="Knowledge">
                <div className="stack">
                  <article className="record-card">
                    <div className="record-card-header">
                      <strong>{novatechOrgPlatformSurfaces.knowledge?.title || "NovaKnowledge"}</strong>
                      <span>{novatechOrgPlatformSurfaces.knowledge?.status || "ready"}</span>
                    </div>
                    <p>{novatechOrgPlatformSurfaces.knowledge?.summary}</p>
                    <div className="chip-row">
                      <span className="surface-chip">
                        Projects {novatechOrgPlatformSurfaces.knowledge?.project_count || 0}
                      </span>
                      <span className="surface-chip">
                        Files {novatechOrgPlatformSurfaces.knowledge?.file_count || 0}
                      </span>
                      <span className="surface-chip">
                        {novatechOrgPlatformSurfaces.knowledge?.route || "/v1/novatech/intranet/knowledge"}
                      </span>
                    </div>
                    <div className="chip-row">
                      {(novatechOrgPlatformSurfaces.knowledge?.document_roots || []).map((root) => (
                        <span key={root} className="surface-chip">
                          {root}
                        </span>
                      ))}
                    </div>
                  </article>
                </div>
              </OperatorPanel>

              <OperatorPanel title="Workflows">
                <div className="stack">
                  <article className="record-card">
                    <div className="record-card-header">
                      <strong>{novatechOrgPlatformSurfaces.workflows?.title || "NovaWorkflow"}</strong>
                      <span>{novatechOrgPlatformSurfaces.workflows?.status || "ready"}</span>
                    </div>
                    <p>{novatechOrgPlatformSurfaces.workflows?.summary}</p>
                    <div className="chip-row">
                      <span className="surface-chip">
                        Workflows {novatechOrgPlatformSurfaces.workflows?.workflow_count || 0}
                      </span>
                      <span className="surface-chip">
                        {novatechOrgPlatformSurfaces.workflows?.route || "/v1/novatech/intranet/workflows"}
                      </span>
                    </div>
                    <div className="stack compact-stack">
                      {(novatechOrgPlatformSurfaces.workflows?.templates || []).map((template) => (
                        <div key={template.workflow_name} className="reason-chip reason-chip-success">
                          {template.workflow_name}: {template.purpose}
                        </div>
                      ))}
                    </div>
                  </article>
                </div>
              </OperatorPanel>

              <OperatorPanel title="Comms">
                <div className="stack">
                  <article className="record-card">
                    <div className="record-card-header">
                      <strong>{novatechOrgPlatformSurfaces.comms?.title || "NovaComms"}</strong>
                      <span>{novatechOrgPlatformSurfaces.comms?.status || "ready"}</span>
                    </div>
                    <p>{novatechOrgPlatformSurfaces.comms?.summary}</p>
                    <div className="chip-row">
                      <span className="surface-chip">
                        Messages {novatechOrgPlatformSurfaces.comms?.message_count || 0}
                      </span>
                      <span className="surface-chip">
                        {novatechOrgPlatformSurfaces.comms?.route || "/v1/novatech/intranet/comms"}
                      </span>
                    </div>
                    <div className="chip-row">
                      {(novatechOrgPlatformSurfaces.comms?.channels || []).map((channel) => (
                        <span key={channel.name} className="surface-chip">
                          {channel.name}
                        </span>
                      ))}
                    </div>
                    <div className="stack compact-stack">
                      {(novatechOrgPlatformSurfaces.comms?.messages || []).slice(0, 4).map((message) => (
                        <div key={`${message.channel}-${message.created_at}-${message.title}`} className="reason-chip">
                          {message.channel}: {message.title}
                        </div>
                      ))}
                    </div>
                  </article>
                </div>
              </OperatorPanel>
            </div>
          </>
        ) : (
          <EmptyState label="NovaTech organizational surfaces will appear after the first platform snapshot." />
        )}
      </section>

      <section className="section-band realtime-band">
        <SectionIntro
          eyebrow="Live System"
          title="Realtime dashboard stream"
          question="The browser listens to websocket events so ride, operations, and intranet changes surface without manual refresh."
        />
        <div className="operator-grid realtime-grid">
          <OperatorPanel title="Connection State">
            <div className="record-card">
              <div className="record-card-header">
                <strong>Dashboard socket</strong>
                <span className={`status-${liveConnection === "connected" ? "success" : liveConnection === "connecting" ? "neutral" : "warning"}`}>
                  {liveConnection}
                </span>
              </div>
              <p>
                Live websocket channel: <span className="surface-chip">/ws/dashboard</span>
              </p>
              <div className="chip-row">
                <span className="surface-chip">Auto-updates enabled</span>
                <span className="surface-chip">Sequence aware</span>
                <span className="surface-chip">Projection only</span>
              </div>
              <div className="key-value">
                <span>Last update</span>
                <strong>{lastUpdated || "Awaiting first event"}</strong>
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Live Event Stream">
            <div className="stack">
              {liveEvents.length > 0 ? (
                liveEvents.map((event, index) => (
                  <article key={`${event.sequence || index}-${event.type || "event"}`} className="record-card">
                    <div className="record-card-header">
                      <strong>{event.type || "DASHBOARD_EVENT"}</strong>
                      <span>#{event.sequence || index + 1}</span>
                    </div>
                    <p>{event.data?.source || event.channel || "dashboard"}</p>
                    <pre className="realtime-event-json">
                      {JSON.stringify(event.data || event, null, 2)}
                    </pre>
                  </article>
                ))
              ) : (
                <div className="empty-state">Waiting for backend events...</div>
              )}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <header className="hero trust-os-hero">
        <div className="hero-copy">
          <p className="eyebrow">Trust OS Interface</p>
          <h1>A browser for truth and operations.</h1>
          <p className="hero-summary">
            AfriTech OS turns doctrine, governance, execution, proof, trust,
            intelligence, economy, and products into one investor-ready command
            surface. NovaTech uses the same browser shell to organize platform
            layers and product dashboards into one internal control system.
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
          eyebrow="AfriPro / NovaCodePro"
          title="AfriPro / NovaCodePro Workspace"
          question="How does the AI software factory accelerate delivery without becoming a truth authority?"
        />
        <p className="section-note">AfriPro is the product line now positioned as NovaCodePro: a phased AI software engineering platform from SaaS foundation through NovaCodePro OS. The current workspace remains proposal-only: AfriProgramming, replay, and governance still decide what becomes real execution.</p>
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
        <OperatorPanel title="NovaCodePro Phase Roadmap">
          <div className="phase-grid">
            {NOVACODEPRO_PHASES.map((phase) => (
              <article key={phase.phase} className="record-card">
                <div className="record-card-header">
                  <strong>{phase.phase}</strong>
                  <span>{phase.focus}</span>
                </div>
                <p>{phase.modules}</p>
              </article>
            ))}
          </div>
        </OperatorPanel>
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
	                <strong>Django Backend for AfriPro / NovaCodePro Chat + Dashboard</strong>
                <span>governance-linked</span>
              </div>
              <p>
                Chat, dashboard, editor, and project surfaces are backed by Django-style modules
                while AfriProgramming remains the authority path for activation.
              </p>
            </article>
            <AuditorDashboard receiptIds={["demo-receipt", "pilot-demo-receipt"]} />
          </div>
        </OperatorPanel>
        <div className="operator-grid afriprog-grid">
          <OperatorPanel title="NovaCodePro Prompt Studio">
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

          <OperatorPanel title="NovaCodePro Controls">
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
	                  AfriPro / NovaCodePro output only becomes eligible for authority review after an explicit
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

      <section className="section-band analytics-band">
        <SectionIntro
          eyebrow="Live Analytics"
          title="Trust, replay, evidence, and operator alerts"
          question="The charts below are driven by the current trust snapshot and the rolling websocket trail, so they stay live without changing the authority model."
        />
        <div className="operator-grid analytics-grid">
          <OperatorPanel title="Live Trust Analytics">
            <AnalyticsTrendPanel
              title="Trust score trend"
              description="A rolling snapshot of the live trust score and derived health band."
              history={analyticsTrail}
              valueKey="trustScore"
              currentValue={liveAnalyticsSnapshot.trustScore || 0}
              accent="#1f7a55"
              unit=""
              stats={[
                { label: "Trust health", value: liveAnalyticsSnapshot.trustHealth || 0 },
                { label: "Drivers online", value: liveAnalyticsSnapshot.onlineDrivers || 0 },
                { label: "Notifications", value: liveNotifications.length || 0 },
              ]}
            />
          </OperatorPanel>

          <OperatorPanel title="Live Replay Exception Alerts">
            <AnalyticsTrendPanel
              title="Exception pressure"
              description="Replay failures, hash-chain failures, missing traces, and guard violations aggregated into one live pressure line."
              history={analyticsTrail}
              valueKey="exceptionCount"
              currentValue={liveAnalyticsSnapshot.exceptionCount || 0}
              accent="#c2410c"
              stats={[
                { label: "Replay success", value: `${liveAnalyticsSnapshot.replaySuccessRate || 0}%` },
                { label: "Replay failures", value: liveAnalyticsSnapshot.replayFailures || 0 },
                { label: "Hash-chain", value: liveAnalyticsSnapshot.hashChainFailures || 0 },
                { label: "Guards", value: liveAnalyticsSnapshot.guardCount || 0 },
              ]}
            />
          </OperatorPanel>

          <OperatorPanel title="Live Pilot Evidence Trends">
            <AnalyticsTrendPanel
              title="Evidence coverage"
              description="Receipt and trace coverage evolve with each polling cycle and ride projection update."
              history={analyticsTrail}
              valueKey="evidenceCoverage"
              currentValue={`${liveAnalyticsSnapshot.evidenceCoverage || 0}%`}
              accent="#185b8c"
              unit="%"
              stats={[
                { label: "Receipts", value: liveAnalyticsSnapshot.receiptsCount || 0 },
                { label: "Traces", value: liveAnalyticsSnapshot.traceCount || 0 },
                { label: "Completed rides", value: liveAnalyticsSnapshot.completedRides || 0 },
              ]}
            />
          </OperatorPanel>

          <OperatorPanel title="Live Operator Notifications">
            <NotificationFeed notifications={liveNotifications} />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band analytics-band realtime-analytics-band">
        <SectionIntro
          eyebrow="Predictive Demand"
          title="Real-time analytics dashboard"
          question="This projection combines live ride pressure, driver supply, and trust posture into a bounded demand forecast for the next operating windows."
        />
        <div className="operator-grid analytics-grid">
          <OperatorPanel title="Predictive Demand ML">
            <DemandForecastPanel demandForecast={operatorDemandForecast} />
          </OperatorPanel>

          <OperatorPanel title="Real-time City Pressure">
            <RealtimeAnalyticsPanel
              demandForecast={operatorDemandForecast}
              liveAnalyticsSnapshot={liveAnalyticsSnapshot}
            />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band analytics-band strategy-band">
        <SectionIntro
          eyebrow="Phase 5"
          title="Autonomous Strategy Engine"
          question="The strategy engine converts demand, autonomy, pricing, and profit surfaces into a bounded city strategy plan without taking execution authority."
        />
        <div className="operator-grid analytics-grid">
          <OperatorPanel title="Autonomous Strategy Engine">
            <StrategyEnginePanel strategyEngine={operatorStrategyEngine} />
          </OperatorPanel>

          <OperatorPanel title="Strategy Guardrails">
            <StrategyGuardrailsPanel strategyEngine={operatorStrategyEngine} />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band analytics-band analytics-history-band">
        <SectionIntro
          eyebrow="Persistent Intelligence"
          title="History, AI insights, and predictive analytics"
          question="These panels read from the persisted analytics store, so operators can review long-running trust patterns and forecast the next operating window."
        />
        <div className="operator-grid analytics-grid">
          <OperatorPanel title="Persistent Trust History">
            <AnalyticsTrendPanel
              title="Trust history"
              description="Deduped operator snapshots retained across refresh cycles and sessions."
              history={persistedAnalyticsHistory}
              valueKey="trustScore"
              currentValue={persistedAnalyticsLatest?.trustScore || liveAnalyticsSnapshot.trustScore || 0}
              accent="#1f7a55"
              stats={[
                { label: "Trust health", value: persistedAnalyticsLatest?.trustHealth || 0 },
                { label: "Replay health", value: persistedAnalyticsLatest?.replayHealthScore || 0 },
                { label: "Trend delta", value: persistedAnalyticsTrend?.trust?.delta || 0 },
              ]}
            />
            <div className="chip-row">
              <span className="surface-chip">
                Source: {persistedAnalyticsLatest?.source || "afriride_operator_dashboard"}
              </span>
              <span className="surface-chip">
                Window: {persistedAnalyticsLatest?.windowBucket || "live"}
              </span>
              <span className="surface-chip">
                Snapshots: {persistedAnalyticsHistory.length || 0}
              </span>
            </div>
          </OperatorPanel>

          <OperatorPanel title="AI Insights">
            <AnalyticsInsightFeed insights={persistedAnalyticsInsights} />
          </OperatorPanel>

          <OperatorPanel title="Predictive Analytics">
            <PredictionPanel
              prediction={persistedAnalyticsPrediction}
              latest={persistedAnalyticsLatest}
              trend={persistedAnalyticsTrend}
            />
          </OperatorPanel>

          <OperatorPanel title="History Trail">
            <AnalyticsHistoryFeed
              history={persistedAnalyticsHistory}
              sourceBreakdown={persistedAnalyticsSourceBreakdown}
            />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band decision-band operation-ai-band">
        <SectionIntro
          eyebrow="Operations AI"
          title="Operation AI Decision Dashboard"
          question="The decision surface translates live dispatch pressure, trust, replay, and evidence into a read-only operator posture without taking execution authority."
        />
        <div className="operator-grid analytics-grid">
          <OperatorPanel title="Dispatch posture">
            <OperationAIDecisionPanel
              decision={persistedDecisionCurrent}
              action={persistedActionCurrent}
              liveAnalyticsSnapshot={liveAnalyticsSnapshot}
              liveNotifications={liveNotifications}
              novarideOperatorDashboardContract={novarideOperatorDashboardContract}
              novarideEcosystem={novarideEcosystem}
              operatorCityAutomation={operatorCityAutomation}
              operatorMultiCityOrchestration={operatorMultiCityOrchestration}
              operatorDigitalTwin={operatorDigitalTwin}
              operatorMetaLearningRedesign={operatorMetaLearningRedesign}
              operatorBusinessPricing={operatorBusinessPricing}
              activeRidesCount={state.activeRides.length}
              operationState={operationAIDecisionState}
            />
          </OperatorPanel>

          <OperatorPanel title="Current Decision">
            <DecisionSummaryPanel decision={persistedDecisionCurrent} latest={persistedDecisionLatest} />
          </OperatorPanel>

          <OperatorPanel title="Decision Stability Trend">
            <AnalyticsTrendPanel
              title="Stability index"
              description="Persisted decisions accumulate a stability score so operators can see whether the lane is strengthening or drifting."
              history={persistedDecisionHistory}
              valueKey="stabilityIndex"
              currentValue={persistedDecisionCurrent?.stabilityIndex || 0}
              accent="#2f6f73"
              stats={[
                { label: "Lane", value: persistedDecisionCurrent?.decisionLane || "observe" },
                { label: "Priority", value: persistedDecisionCurrent?.decisionPriority || "low" },
                { label: "Risk", value: persistedDecisionCurrent?.riskLevel || "unknown" },
              ]}
            />
          </OperatorPanel>

          <OperatorPanel title="Decision Guidance">
            <DecisionGuidancePanel decision={persistedDecisionCurrent} />
          </OperatorPanel>

          <OperatorPanel title="Decision History">
            <DecisionHistoryFeed
              history={persistedDecisionHistory}
              sourceBreakdown={persistedDecisionSourceBreakdown}
            />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band action-band">
        <SectionIntro
          eyebrow="Controlled autonomy"
          title="Predictive AI and autonomous execution thresholds"
          question="The action engine converts decision quality into operator guidance, safety gates, and a persistent review trail while only enabling bounded autonomy when safe thresholds clear."
        />
        <div className="operator-grid analytics-grid">
          <OperatorPanel title="Autonomy thresholds">
            <OperationAIDecisionPanel
              decision={persistedDecisionCurrent}
              action={persistedActionCurrent}
              liveAnalyticsSnapshot={liveAnalyticsSnapshot}
              liveNotifications={liveNotifications}
              novarideOperatorDashboardContract={novarideOperatorDashboardContract}
              novarideEcosystem={novarideEcosystem}
              operatorAutonomy={operatorAutonomy}
              operatorCityAutomation={operatorCityAutomation}
              operatorMultiCityOrchestration={operatorMultiCityOrchestration}
              operatorDigitalTwin={operatorDigitalTwin}
              operatorMetaLearningRedesign={operatorMetaLearningRedesign}
              operatorBusinessPricing={operatorBusinessPricing}
              activeRidesCount={state.activeRides.length}
              operationState={operationAIDecisionState}
            />
          </OperatorPanel>

          <OperatorPanel title="Current Action">
            <ActionSummaryPanel action={persistedActionCurrent} latest={persistedActionLatest} />
          </OperatorPanel>

          <OperatorPanel title="Decision Quality Trend">
            <AnalyticsTrendPanel
              title="Quality calibration"
              description="Persisted actions accumulate a calibrated quality score so operators can see whether guidance is converging or drifting."
              history={persistedActionHistory}
              valueKey="decisionQualityScore"
              currentValue={persistedActionCurrent?.decisionQualityScore || 0}
              accent="#0f766e"
              stats={[
                { label: "Action lane", value: persistedActionCurrent?.actionLane || "monitor" },
                { label: "Mode", value: persistedActionCurrent?.actionMode || "guided_control" },
                { label: "Gate", value: persistedActionCurrent?.safetyGate || "pass" },
                { label: "Tier", value: persistedActionCurrent?.automationTier || 0 },
              ]}
            />
          </OperatorPanel>

          <OperatorPanel title="Action Guidance">
            <ActionGuidancePanel action={persistedActionCurrent} />
          </OperatorPanel>

          <OperatorPanel title="Action History">
            <ActionHistoryFeed
              history={persistedActionHistory}
              sourceBreakdown={persistedActionSourceBreakdown}
            />
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band saas-band" id="saas">
        <SectionIntro
          eyebrow="SaaS Platform"
          title="Multi-tenant organizations, billing, and safe execution"
          question="The platform keeps tenant isolation, billing previews, and execution readiness in one governed directory without granting automatic authority."
        />
        <p className="section-note">
          Safe execution remains advisory-only. Billing is previewed from usage evidence, tenants are
          isolated per organization, and controlled execution only becomes ready when trust,
          billing, and safety gates align.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="Tenants"
            value={novatechSaas?.tenant_count || 0}
            helper="Organizations merged from the store and adoption registry."
          />
          <TrustMetric
            label="Billing estimate"
            value={
              novatechSaasBilling
                ? `AUD ${Number(novatechSaasBilling.estimated_amount || 0).toFixed(2)}`
                : "AUD 0.00"
            }
            helper="Usage-derived preview only, no automated billing authority."
          />
          <TrustMetric
            label="Execution gate"
            value={novatechSaasExecution?.execution_tier || "advisory"}
            helper={novatechSaasExecution?.safe_execution_enabled ? "Enabled for operator review" : "Held pending readiness"}
            tone={novatechSaasExecution?.safe_execution_enabled ? "success" : "warning"}
          />
          <TrustMetric
            label="Readiness"
            value={novatechSaasExecution?.safe_execution_enabled ? "Enabled" : "Held"}
            helper="Execution authority stays disabled while the engine stays projection-only."
            tone={novatechSaasExecution?.safe_execution_enabled ? "success" : "neutral"}
          />
        </div>
        <div className="operator-grid">
          <OperatorPanel title="Tenant Directory">
            <div className="stack">
              {novatechSaasTenants.length > 0 ? (
                novatechSaasTenants.map((tenant) => (
                  <article key={tenant.organization_id} className="record-card">
                    <div className="record-card-header">
                      <strong>{tenant.organization_name || tenant.organization_id}</strong>
                      <span>{tenant.status}</span>
                    </div>
                    <p>{tenant.legal_name || tenant.organization_name}</p>
                    <div className="chip-row">
                      <span className="surface-chip">{tenant.organization_id}</span>
                      <span className="surface-chip">{tenant.trust_domain}</span>
                      <span className="surface-chip">{tenant.sector}</span>
                      <span className="surface-chip">{tenant.certification_label || "Uncertified"}</span>
                    </div>
                    <div className="chip-row">
                      <span className="surface-chip">Billing {tenant.billing_plan}</span>
                      <span className="surface-chip">
                        Est. AUD {Number(tenant.billing_estimated_amount || 0).toFixed(2)}
                      </span>
                      <span className="surface-chip">Trust {tenant.trust_score}</span>
                    </div>
                  </article>
                ))
              ) : (
                <EmptyState label="Tenant directory will appear after organizations are onboarded." />
              )}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Billing & Subscriptions">
            {novatechSaasBillingSurface ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Billing preview</strong>
                    <span>{novatechSaasBillingSurface.summary?.plan || "enterprise"}</span>
                  </div>
                  <p>
                    Usage total {novatechSaasBillingSurface.summary?.usage_total || 0} with estimated
                    amount AUD {Number(novatechSaasBillingSurface.summary?.estimated_amount || 0).toFixed(2)}.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Trust {novatechSaasBillingSurface.summary?.trust_score ?? 0}
                    </span>
                    <span className="surface-chip">
                      Billing {novatechSaasBillingSurface.summary?.billing_enabled ? "enabled" : "preview"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Subscription preview</strong>
                    <span>{novatechSaasBillingSurface.subscription_preview?.status || "active"}</span>
                  </div>
                  <p>
                    {novatechSaasBillingSurface.subscription_preview?.plan_name || "enterprise"} at{" "}
                    {novatechSaasBillingSurface.subscription_preview?.recurring_amount?.currency || "AUD"}{" "}
                    {novatechSaasBillingSurface.subscription_preview?.recurring_amount?.amount || "0.00"}.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Next billing {novatechSaasBillingSurface.subscription_preview?.next_billing_at || "pending"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Invoice preview</strong>
                    <span>{novatechSaasBillingSurface.invoice_preview?.status || "open"}</span>
                  </div>
                  <p>
                    Invoice {novatechSaasBillingSurface.invoice_preview?.invoice_id || "pending"} due{" "}
                    {novatechSaasBillingSurface.invoice_preview?.due_at || "pending"}.
                  </p>
                </article>
                <div className="chip-row">
                  {(novatechSaasBillingSurface.billing_history || []).slice(0, 4).map((record) => (
                    <span key={record.billing_id} className="surface-chip">
                      {record.plan} | AUD {Number(record.estimated_amount || 0).toFixed(2)}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState label="Billing preview will appear after tenant usage is recorded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Safe Execution Engine">
            {novatechSaasExecution ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novatechSaasExecution.execution_tier || "advisory"}</strong>
                    <span>{novatechSaasExecution.safe_execution_enabled ? "enabled" : "held"}</span>
                  </div>
                  <p>{novatechSaasExecution.action_summary || "Safe execution is waiting on the next readiness window."}</p>
                  <div className="chip-row">
                    <span className="surface-chip">Gate {novatechSaasExecution.safety_gate || "hold"}</span>
                    <span className="surface-chip">
                      Control {novatechSaasExecution.control_signal || "maintain_monitoring"}
                    </span>
                    <span className="surface-chip">
                      Quality {novatechSaasExecution.decision_quality_score || 0}
                    </span>
                    <span className="surface-chip">
                      Confidence {Math.round((novatechSaasExecution.calibrated_confidence || 0) * 100)}%
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Controlled execution activation</strong>
                    <span>
                      {novatechControlledExecutionActivation?.activation?.activation_status || "held"}
                    </span>
                  </div>
                  <p>
                    {novatechControlledExecutionActivation?.activation?.activation_reason ||
                      "Activate the controlled tier once the readiness gate and operator acknowledgment align."}
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Requested {novatechControlledExecutionActivation?.activation?.requested_tier || "controlled"}
                    </span>
                    <span className="surface-chip">
                      Ack {novatechControlledExecutionActivation?.activation?.acknowledged ? "yes" : "no"}
                    </span>
                    <span className="surface-chip">
                      Ready {novatechControlledExecutionActivation?.activation?.activation_ready ? "yes" : "no"}
                    </span>
                    <span className="surface-chip">
                      Scope {novatechControlledExecutionActivation?.activation?.activation_scope?.length || 0}
                    </span>
                  </div>
                  <div className="feature-action-row">
                    <button
                      type="button"
                      className="button primary"
                      onClick={activateControlledExecution}
                      disabled={
                        controlledExecutionBusy || !novatechSaasExecution?.safe_execution_enabled
                      }
                    >
                      {controlledExecutionBusy ? "Activating..." : "Activate controlled execution"}
                    </button>
                    <span className="surface-chip">
                      {novatechControlledExecutionActivation?.activation?.safe_execution_enabled
                        ? "Enabled for review"
                        : "Held pending readiness"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Readiness checks</strong>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Tenant {novatechSaasExecution.readiness?.tenant_ready ? "ready" : "hold"}
                    </span>
                    <span className="surface-chip">
                      Billing {novatechSaasExecution.readiness?.billing_ready ? "ready" : "hold"}
                    </span>
                    <span className="surface-chip">
                      Execution {novatechSaasExecution.readiness?.execution_tier_ready ? "ready" : "hold"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Operator reasons</strong>
                  <div className="stack compact-stack">
                    {(novatechSaas?.reasons || []).map((reason) => (
                      <div key={reason} className="reason-chip">
                        {reason}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Safe execution will appear after a tenant snapshot is available." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Shared NovaRide Platform Architecture">
            {novaridePlatformArchitectureContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novaridePlatformArchitectureContract.principle || "Apps = Interface; Platform = Authority"}</strong>
                    <span>{novaridePlatformArchitectureContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Passenger, Driver, and Operator surfaces send requests and display data.
                    NovaRide API validates access, then shared services own dispatch,
                    pricing, payments, trust, notifications, analytics, and replay.
                  </p>
                  <div className="chip-row">
                    {(novaridePlatformArchitectureContract.layers?.api_gateway?.responsibilities || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Shared services</strong>
                  <div className="chip-row">
                    {(novaridePlatformArchitectureContract.layers?.execution_layer?.services ||
                      NOVARIDE_ARCHITECTURE_SERVICE_FALLBACKS).map((service) => (
                      <span key={service.key || service} className="surface-chip">
                        {service.name || service}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Authority boundary</strong>
                    <span>{novaridePlatformArchitectureContract.authority_boundary?.payments || "NovaPay_backend_only"}</span>
                  </div>
                  <div className="chip-row">
                    {(novaridePlatformArchitectureContract.authority_boundary?.backend_full_control ||
                      NOVARIDE_ARCHITECTURE_BACKEND_AUTHORITY_FALLBACKS).map((item) => (
                      <span key={item} className="surface-chip">
                        Backend: {item}
                      </span>
                    ))}
                    {(novaridePlatformArchitectureContract.authority_boundary?.apps_no_authority ||
                      NOVARIDE_ARCHITECTURE_APP_BLOCKED_FALLBACKS).map((item) => (
                      <span key={item} className="surface-chip">
                        App blocked: {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Ride request flow</strong>
                  <div className="chip-row">
                    {(novaridePlatformArchitectureContract.ride_request_flow ||
                      NOVARIDE_ARCHITECTURE_FLOW_FALLBACKS).map((step) => (
                      <span key={step} className="surface-chip">
                        {step}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide platform architecture contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Next-Generation Mobility Platform">
            <div className="stack">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Governed mobility platform</strong>
                  <span>apps_request_control_plane_decides_events_prove</span>
                </div>
                <p>
                  Rider and Driver apps request and display. Operator and Inspector portals
                  control quality and compliance. Control Plane decides. Execution Plane
                  performs. Event Platform proves every ride.
                </p>
                <div className="chip-row">
                  <span className="surface-chip">Control Plane decides</span>
                  <span className="surface-chip">Execution Plane performs</span>
                  <span className="surface-chip">Event Platform proves</span>
                  {NOVARIDE_GOVERNED_BACKEND_CHAIN.map((service) => (
                    <span key={service} className="surface-chip">{service}</span>
                  ))}
                </div>
              </article>

              <article className="record-card">
                <strong>AI and intelligence layer</strong>
                <div className="chip-row">
                  {NOVARIDE_AI_INTELLIGENCE_LAYER.map((signal) => (
                    <span key={signal} className="reason-chip">{signal}</span>
                  ))}
                </div>
              </article>

              <article className="record-card">
                <strong>Evidence-backed ride flow</strong>
                <div className="flow-line" aria-label="NovaRide evidence backed ride flow">
                  {NOVARIDE_EVIDENCE_BACKED_RIDE_FLOW.map((step) => (
                    <span key={step}>{step}</span>
                  ))}
                </div>
              </article>

              <div className="novapay-build-grid">
                {NOVARIDE_NEXT_GEN_PLATFORM_STACK.map((surface) => (
                  <article key={surface.name} className="record-card novapay-build-card">
                    <div className="record-card-header">
                      <strong>{surface.name}</strong>
                      <span>{surface.users}</span>
                    </div>
                    <div className="novapay-build-section">
                      <strong>Modules</strong>
                      <div className="chip-row">
                        {surface.modules.map((module) => (
                          <span key={module} className="surface-chip">{module}</span>
                        ))}
                      </div>
                    </div>
                    <div className="novapay-build-section">
                      <strong>Capabilities</strong>
                      <div className="chip-row">
                        {surface.features.map((feature) => (
                          <span key={feature} className="reason-chip reason-chip-success">{feature}</span>
                        ))}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="NovaRide Enterprise Operations Layer">
            <div className="stack">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>10/10 enterprise operations depth</strong>
                  <span>governed_evidence_backed_ai_assisted_mobility_control_platform</span>
                </div>
                <p>
                  App and portal surfaces now sit on an enterprise operations layer for command,
                  zones, digital twin simulation, incident workflow, fleet intelligence, public
                  trust, developer ecosystem, SRE observability, and multi-tenant governance.
                </p>
                <div className="chip-row">
                  <span className="surface-chip">Enterprise Operations: 10/10</span>
                  <span className="surface-chip">AI-assisted decisions</span>
                  <span className="surface-chip">Evidence-backed operations</span>
                  <span className="surface-chip">Multi-tenant governance</span>
                </div>
              </article>

              <div className="novapay-build-grid">
                {NOVARIDE_ENTERPRISE_OPERATIONS_LAYER.map((capability) => (
                  <article key={capability.name} className="record-card novapay-build-card">
                    <div className="record-card-header">
                      <strong>{capability.name}</strong>
                      <span>{capability.purpose}</span>
                    </div>
                    <div className="chip-row">
                      {capability.capabilities.map((item) => (
                        <span key={item} className="reason-chip reason-chip-success">{item}</span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="NovaRide Operator Command Center">
            {novarideOperatorDashboardContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Operations decision layer</strong>
                    <span>{novarideOperatorDashboardContract.status || "controlled_pilot_ready"}</span>
                  </div>
                  <p>
                    Real-time control, ride management, driver monitoring, safety,
                    analytics, ecosystem visibility, and support escalation remain
                    bound to backend authority.
                  </p>
                  <div className="chip-row">
                    {(novarideOperatorDashboardContract.layout?.left_navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Core modules</strong>
                  <div className="chip-row">
                    {(novarideOperatorDashboardContract.modules || NOVARIDE_OPERATOR_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Authority model</strong>
                    <span>Backend enforced</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novarideOperatorDashboardContract.authority_model?.allowed ||
                      NOVARIDE_OPERATOR_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novarideOperatorDashboardContract.authority_model?.forbidden ||
                      NOVARIDE_OPERATOR_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide operator contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Fleet Manager">
            {novarideFleetManagerContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideFleetManagerContract.role || "FLEET_OWNER"}</strong>
                    <span>{novarideFleetManagerContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Fleet owners manage vehicles, drivers, compliance, finances, and reports while
                    dispatch, payments, trust, inspection, and replay stay backend-authoritative.
                  </p>
                  <div className="chip-row">
                    {(novarideFleetManagerContract.navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Fleet modules</strong>
                  <div className="chip-row">
                    {(novarideFleetManagerContract.modules || NOVARIDE_FLEET_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Fleet RBAC</strong>
                    <span>{novarideFleetManagerContract.authority_model?.payments || "NovaPay_backend_only"}</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novarideFleetManagerContract.rbac?.allowed ||
                      NOVARIDE_FLEET_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novarideFleetManagerContract.rbac?.forbidden ||
                      NOVARIDE_FLEET_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide fleet manager contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Business Portal">
            {novarideBusinessPortalContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideBusinessPortalContract.role || "CLIENT"}</strong>
                    <span>{novarideBusinessPortalContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Companies manage employee travel, approvals, budgets, billing, and reports
                    while dispatch, pricing, payments, identity, and audit remain backend-authoritative.
                  </p>
                  <div className="chip-row">
                    {(novarideBusinessPortalContract.navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Business modules</strong>
                  <div className="chip-row">
                    {(novarideBusinessPortalContract.modules || NOVARIDE_BUSINESS_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Business RBAC</strong>
                    <span>{novarideBusinessPortalContract.authority_model?.payments || "NovaPay_backend_only"}</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novarideBusinessPortalContract.rbac?.allowed ||
                      NOVARIDE_BUSINESS_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novarideBusinessPortalContract.rbac?.forbidden ||
                      NOVARIDE_BUSINESS_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide business portal contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Admin">
            {novarideAdminContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideAdminContract.role || "ADMIN"}</strong>
                    <span>{novarideAdminContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Platform administrators configure roles, approvals, pricing policies,
                    service zones, campaigns, compliance, audit, and system health while rides
                    and payments remain backend-authoritative.
                  </p>
                  <div className="chip-row">
                    {(novarideAdminContract.navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Admin modules</strong>
                  <div className="chip-row">
                    {(novarideAdminContract.modules || NOVARIDE_ADMIN_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Admin governance</strong>
                    <span>{novarideAdminContract.authority_model?.payments || "NovaPay_policy_level_only"}</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novarideAdminContract.rbac?.allowed ||
                      NOVARIDE_ADMIN_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novarideAdminContract.rbac?.forbidden ||
                      NOVARIDE_ADMIN_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide admin contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Inspector App">
            {novarideInspectorAppContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideInspectorAppContract.role || "VERIFIER"}</strong>
                    <span>{novarideInspectorAppContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Field inspectors verify drivers, vehicles, documents, photos, and reports.
                    Trust Engine remains the final compliance authority and Audit Engine keeps
                    evidence replayable.
                  </p>
                  <div className="chip-row">
                    {(novarideInspectorAppContract.navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Inspector modules</strong>
                  <div className="chip-row">
                    {(novarideInspectorAppContract.modules || NOVARIDE_INSPECTOR_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Compliance authority</strong>
                    <span>{novarideInspectorAppContract.authority_model?.compliance || "Trust_Engine_final_authority"}</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novarideInspectorAppContract.rbac?.allowed ||
                      NOVARIDE_INSPECTOR_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novarideInspectorAppContract.rbac?.forbidden ||
                      NOVARIDE_INSPECTOR_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide inspector app contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Support">
            {novarideSupportContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideSupportContract.role || "OPERATOR"}</strong>
                    <span>{novarideSupportContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Support agents manage tickets, ride investigations, refund requests,
                    driver and passenger assistance, escalations, and replay-backed decisions
                    while NovaPay executes approved refunds through the backend.
                  </p>
                  <div className="chip-row">
                    {(novarideSupportContract.navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Support modules</strong>
                  <div className="chip-row">
                    {(novarideSupportContract.modules || NOVARIDE_SUPPORT_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Refund authority</strong>
                    <span>{novarideSupportContract.authority_model?.refund_execution || "NovaPay_backend_only"}</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novarideSupportContract.rbac?.allowed ||
                      NOVARIDE_SUPPORT_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novarideSupportContract.rbac?.forbidden ||
                      NOVARIDE_SUPPORT_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide support contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Phase 11 Compliance & Inspection">
            {novaridePhase11Status ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Support Dashboard UI</strong>
                    <span>{novaridePhase11Status.readiness?.regulatory_readiness_ready ? "government_review_ready" : "controlled_review"}</span>
                  </div>
                  <p>
                    Auto Ticket Classification, the Auto Refund System, the Analytics Backend, and the
                    Driver Scoring Algorithm stay projection-backed while Trust Engine and NovaPay keep
                    the final authority.
                  </p>
                  <div className="chip-row">
                    {(novaridePhase11Status.support_dashboard?.dashboard_cards || []).map((card) => (
                      <span key={card.label} className="surface-chip">
                        {card.label}: {card.value}
                      </span>
                    ))}
                  </div>
                </article>

                <div className="metric-grid">
                  <KeyValue
                    label="Inspection Workflow"
                    value={novaridePhase11Status.compliance_workspace?.summary?.inspection_workflow_ready ? "Ready" : "Pending"}
                    tone={novaridePhase11Status.compliance_workspace?.summary?.inspection_workflow_ready ? "success" : "warning"}
                  />
                  <KeyValue
                    label="Document Verification"
                    value={novaridePhase11Status.compliance_workspace?.summary?.document_verification_ready ? "Ready" : "Pending"}
                    tone={novaridePhase11Status.compliance_workspace?.summary?.document_verification_ready ? "success" : "warning"}
                  />
                  <KeyValue
                    label="Inspection Reports"
                    value={novaridePhase11Status.compliance_workspace?.summary?.inspection_reports_ready ? "Ready" : "Pending"}
                    tone={novaridePhase11Status.compliance_workspace?.summary?.inspection_reports_ready ? "success" : "warning"}
                  />
                  <KeyValue
                    label="Driver Scoring Algorithm"
                    value={novaridePhase11Status.compliance_workspace?.driver_scoring?.average_score || 0}
                  />
                  <KeyValue
                    label="Fraud Detection"
                    value={novaridePhase11Status.compliance_workspace?.fraud_detection?.risk_band || "low"}
                    tone={
                      novaridePhase11Status.compliance_workspace?.fraud_detection?.risk_band === "critical"
                        ? "warning"
                        : "success"
                    }
                  />
                  <KeyValue
                    label="Regulatory Readiness"
                    value={novaridePhase11Status.compliance_workspace?.regulatory_readiness?.readiness_band || "watch"}
                  />
                </div>

                <article className="record-card">
                  <strong>Auto ticket classification</strong>
                  <div className="chip-row">
                    {(novaridePhase11Status.compliance_workspace?.ticket_classification?.classifications || []).map((ticket) => (
                      <span key={ticket.ticket_id} className="surface-chip">
                        {ticket.ticket_id}: {ticket.category} ({ticket.confidence})
                      </span>
                    ))}
                  </div>
                </article>

                <article className="record-card">
                  <strong>Smart refunds</strong>
                  <div className="chip-row">
                    {(novaridePhase11Status.compliance_workspace?.smart_refunds?.recommendations || []).map((refund) => (
                      <span key={refund.refund_id} className="surface-chip">
                        {refund.refund_id}: AUD {refund.suggested_refund_amount}
                      </span>
                    ))}
                  </div>
                </article>

                <article className="record-card">
                  <strong>Inspection and compliance queues</strong>
                  <div className="stack compact-stack">
                    <div className="reason-chip">
                      Inspection queue: {novaridePhase11Status.compliance_workspace?.inspections?.inspection_total || 0}
                    </div>
                    <div className="reason-chip">
                      Verified documents: {novaridePhase11Status.compliance_workspace?.documents?.verified_count || 0}
                    </div>
                    <div className="reason-chip">
                      Inspection reports: {novaridePhase11Status.compliance_workspace?.inspection_reports?.report_total || 0}
                    </div>
                    <div className="reason-chip">
                      Regulatory review: {novaridePhase11Status.compliance_workspace?.regulatory_readiness?.readiness_band || "watch"}
                    </div>
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Phase 11 compliance and inspection status will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Phase 12 Multi-City & Global Scaling">
            {novaridePhase12Status ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Global scaling</strong>
                    <span>{novaridePhase12Status.readiness?.multi_city_ready ? "global_ready" : novaridePhase12Status.readiness?.phase11_ready ? "global_review_ready" : "global_held"}</span>
                  </div>
                  <p>
                    Auto Decision Engine, Fraud Prediction Models, and Driver Incentives Optimization remain
                    bounded while the platform scales across cities, currencies, and locales.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Multi-City Management: {novaridePhase12Status.global_scale_workspace?.multi_city_management?.mode || "global_held"}
                    </span>
                    <span className="surface-chip">
                      Geo-Fencing: {novaridePhase12Status.global_scale_workspace?.geo_fencing?.geo_fence_ready ? "ready" : "standby"}
                    </span>
                    <span className="surface-chip">
                      Currency Support: {novaridePhase12Status.global_scale_workspace?.currency_support?.supported_currencies?.join(", ") || "AUD"}
                    </span>
                    <span className="surface-chip">
                      Localization: {novaridePhase12Status.global_scale_workspace?.localization?.supported_languages?.join(", ") || "en"}
                    </span>
                  </div>
                </article>

                <div className="metric-grid">
                  <KeyValue
                    label="Region-Based Pricing"
                    value={novaridePhase12Status.global_scale_workspace?.region_pricing?.region_pricing_ready ? "Ready" : "Pending"}
                    tone={novaridePhase12Status.global_scale_workspace?.region_pricing?.region_pricing_ready ? "success" : "warning"}
                  />
                  <KeyValue
                    label="Distributed Infrastructure"
                    value={novaridePhase12Status.global_scale_workspace?.distributed_infrastructure?.deployment_mode || "single_region"}
                  />
                  <KeyValue
                    label="Auto Decision Engine"
                    value={novaridePhase12Status.global_scale_workspace?.auto_decision_engine?.decision_lane || "hold"}
                  />
                  <KeyValue
                    label="Fraud Prediction"
                    value={novaridePhase12Status.global_scale_workspace?.fraud_prediction?.risk_band || "low"}
                  />
                  <KeyValue
                    label="Driver Incentives"
                    value={novaridePhase12Status.global_scale_workspace?.driver_incentives?.incentive_focus || "balance"}
                  />
                  <KeyValue
                    label="Global Scale Score"
                    value={novaridePhase12Status.global_scale_workspace?.global_scale_score || 0}
                  />
                </div>

                <article className="record-card">
                  <strong>City topology</strong>
                  <div className="chip-row">
                    {(novaridePhase12Status.global_scale_workspace?.multi_city_management?.city_topology || []).map((city) => (
                      <span key={city.city} className="surface-chip">
                        {city.city}: {city.currency} · {city.language} · {city.mode}
                      </span>
                    ))}
                  </div>
                </article>

                <article className="record-card">
                  <strong>Global decisions</strong>
                  <div className="stack compact-stack">
                    <div className="reason-chip reason-chip-success">
                      {novaridePhase12Status.global_scale_workspace?.auto_decision_engine?.decision_summary ||
                        "The global decision engine remains review-bound."}
                    </div>
                    <div className="reason-chip">
                      {novaridePhase12Status.global_scale_workspace?.fraud_prediction?.predictive_signals?.join(" • ") ||
                        "Fraud prediction stays bounded until more cities are active."}
                    </div>
                    <div className="reason-chip">
                      {novaridePhase12Status.global_scale_workspace?.global_learning?.recommendation ||
                        "Global learning remains projection-backed."}
                    </div>
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Phase 12 multi-city and global scaling status will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Phase 13 Global Execution & AWS">
            {novaridePhase13Status ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Global Deployment Plan</strong>
                    <span>
                      {novaridePhase13Status.readiness?.global_deployment_plan_ready
                        ? "deployment_ready"
                        : "plan_review"}
                    </span>
                  </div>
                  <p>
                    The Real Execution Layer turns projections into controlled actions while the AWS
                    production infra remains plan-bound, operator-gated, and replay-backed.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Controlled AI Decision Engine: {novaridePhase13Status.global_execution_workspace?.controlled_ai_decision_engine?.decision_lane || "hold"}
                    </span>
                    <span className="surface-chip">
                      AWS Production Infra: {novaridePhase13Status.global_execution_workspace?.aws_production_infra?.deployment_mode || "single_region"}
                    </span>
                    <span className="surface-chip">
                      Real Execution Layer: {novaridePhase13Status.global_execution_workspace?.real_execution_layer?.execution_mode || "review_only"}
                    </span>
                    <span className="surface-chip">
                      AI Optimization: {novaridePhase13Status.global_execution_workspace?.ai_optimization?.optimization_mode || "bounded_balance"}
                    </span>
                  </div>
                </article>

                <div className="metric-grid">
                  <KeyValue
                    label="Auto Pricing Adjustments"
                    value={novaridePhase13Status.global_execution_workspace?.ai_optimization?.pricing_adjustment_pct || "0.0%"}
                  />
                  <KeyValue
                    label="Live Incentives Tuning"
                    value={novaridePhase13Status.global_execution_workspace?.ai_optimization?.incentive_adjustment_pct || "0.0"}
                  />
                  <KeyValue
                    label="NovaConnect Expansion"
                    value={novaridePhase13Status.global_execution_workspace?.novaconnect_expansion?.deployment_state || "planned"}
                  />
                  <KeyValue
                    label="NovaPay Expansion"
                    value={novaridePhase13Status.global_execution_workspace?.novapay_expansion?.expansion_stage || "controlled_review"}
                  />
                  <KeyValue
                    label="Execution Score"
                    value={novaridePhase13Status.global_execution_workspace?.global_execution_score || 0}
                  />
                  <KeyValue
                    label="Global Deployment"
                    value={novaridePhase13Status.readiness?.global_deployment_plan_ready ? "Ready" : "Held"}
                  />
                </div>

                <article className="record-card">
                  <strong>Controlled actions</strong>
                  <div className="chip-row">
                    {(novaridePhase13Status.global_execution_workspace?.real_execution_layer?.controlled_actions || []).map((action) => (
                      <span key={action} className="surface-chip">
                        {action}
                      </span>
                    ))}
                  </div>
                </article>

                <article className="record-card">
                  <strong>AWS production infra</strong>
                  <div className="chip-row">
                    {(novaridePhase13Status.global_execution_workspace?.aws_production_infra?.networking || []).map((component) => (
                      <span key={component} className="surface-chip">
                        {component}
                      </span>
                    ))}
                  </div>
                </article>

                <article className="record-card">
                  <strong>Expansion surfaces</strong>
                  <div className="stack compact-stack">
                    <div className="reason-chip reason-chip-success">
                      {novaridePhase13Status.global_execution_workspace?.novaconnect_expansion?.surface?.status || "PLANNED"}
                    </div>
                    <div className="reason-chip">
                      {novaridePhase13Status.global_execution_workspace?.novaconnect_expansion?.authority_boundary || "replay_only"}
                    </div>
                    <div className="reason-chip">
                      {novaridePhase13Status.global_execution_workspace?.novapay_expansion?.expansion_summary ||
                        "NovaPay expansion remains controlled."}
                    </div>
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Phase 13 global execution and AWS status will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Partner Portal">
            {novaridePartnerPortalContract ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novaridePartnerPortalContract.role || "PARTNER"}</strong>
                    <span>{novaridePartnerPortalContract.status || "controlled_pilot_contract_ready"}</span>
                  </div>
                  <p>
                    Partners can book guest rides, manage bulk transport, review usage,
                    and configure booking settings while dispatch, pricing, and billing
                    stay governed by backend services.
                  </p>
                  <div className="chip-row">
                    {(novaridePartnerPortalContract.navigation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Partner modules</strong>
                  <div className="chip-row">
                    {(novaridePartnerPortalContract.modules || NOVARIDE_PARTNER_MODULE_FALLBACKS).map((module) => (
                      <span key={module.key} className="surface-chip">
                        {module.name}: {module.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Partner authority</strong>
                    <span>{novaridePartnerPortalContract.authority_model?.payments || "NovaPay_backend_only"}</span>
                  </div>
                  <div className="stack compact-stack">
                    {(novaridePartnerPortalContract.rbac?.allowed ||
                      NOVARIDE_PARTNER_ALLOWED_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Allowed: {action}
                      </div>
                    ))}
                    {(novaridePartnerPortalContract.rbac?.forbidden ||
                      NOVARIDE_PARTNER_FORBIDDEN_ACTION_FALLBACKS).map((action) => (
                      <div key={action} className="reason-chip">
                        Blocked: {action}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide partner portal contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide App Ecosystem">
            {novarideEcosystem ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideEcosystem.platform || "NovaRide"}</strong>
                    <span>{novarideEcosystem.status || "controlled_pilot_ready"}</span>
                  </div>
                  <p>
                    {novarideEcosystem.app_count || 0} dedicated apps share centralized dispatch,
                    NovaPay, trust, analytics, notification, and replay services.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Apps {novarideEcosystem.app_count || 0}
                    </span>
                    <span className="surface-chip">
                      Payments {novarideEcosystem.authority_boundary?.payments || "NovaPay_backend_only"}
                    </span>
                    <span className="surface-chip">
                      Mobile {novarideEcosystem.authority_boundary?.mobile_apps || "request_and_observe_only"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Application surfaces</strong>
                  <div className="chip-row">
                    {(novarideEcosystem.apps || NOVARIDE_APP_FALLBACKS).map((appSurface) => (
                      <span key={appSurface.key || appSurface} className="surface-chip">
                        {appSurface.name || appSurface}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Ride lifecycle</strong>
                  <div className="stack compact-stack">
                    {(novarideEcosystem.lifecycle || []).slice(0, 6).map((step) => (
                      <div key={step} className="reason-chip">
                        {step}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide ecosystem contract will appear after the API is reachable." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaPay MFS Live Test">
            {novapayLiveTestReadiness ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novapayLiveTestReadiness.provider?.network || "MFS Africa / Onafriq"}</strong>
                    <span>{novapayLiveTestReadiness.live_ready ? "live-ready" : "dry-run"}</span>
                  </div>
                  <p>
                    Provider mode {novapayLiveTestReadiness.provider?.mode || "controlled_partner_pilot"} with{" "}
                    {novapayLiveTestReadiness.ready_corridors?.length || 0} live-ready corridors.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Live {novapayLiveTestReadiness.provider?.live_mode_enabled ? "enabled" : "off"}
                    </span>
                    <span className="surface-chip">
                      Config {novapayLiveTestReadiness.provider?.configured ? "ready" : "missing"}
                    </span>
                    <span className="surface-chip">
                      Money movement {novapayLiveTestReadiness.real_money_movement_blocked ? "blocked" : "armed"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Ready corridors</strong>
                  <div className="chip-row">
                    {(novapayLiveTestReadiness.ready_corridors || []).length > 0 ? (
                      novapayLiveTestReadiness.ready_corridors.map((corridor) => (
                        <span key={corridor} className="surface-chip">
                          {corridor}
                        </span>
                      ))
                    ) : (
                      <span className="surface-chip">No live corridor armed</span>
                    )}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Required live controls</strong>
                  <div className="stack compact-stack">
                    {(novapayLiveTestReadiness.required_live_controls || []).slice(0, 6).map((control) => (
                      <div key={control} className="reason-chip">
                        {control}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaPay live-test readiness will appear after the core platform API responds." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Documentation Compliance">
            {novatechDocumentationCompliance ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>
                      {novatechDocumentationCompliance.compliance_registry?.classification ||
                        "DOCUMENTATION_COMPLIANCE_PRODUCT"}
                    </strong>
                    <span>{novatechDocumentationCompliance.compliance_registry?.status || "active"}</span>
                  </div>
                  <p>
                    {novatechDocumentationCompliance.compliance_registry?.positioning?.certification_layer ||
                      "ISO-style certification layer"} with
                    {" "}
                    {novatechDocumentationCompliance.compliance_registry?.positioning?.government_compliance ||
                      "government compliance positioning"}.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Documents {novatechDocumentationCompliance.summary?.document_count || 0}
                    </span>
                    <span className="surface-chip">
                      Policies {novatechDocumentationCompliance.summary?.policy_count || 0}
                    </span>
                    <span className="surface-chip">
                      Trust {novatechDocumentationCompliance.summary?.trust_score || 0}
                    </span>
                    <span className="surface-chip">
                      Training {Number(novatechDocumentationCompliance.summary?.training_completion_rate || 0).toFixed(2)}%
                    </span>
                    <span className="surface-chip">
                      Assurance {novatechDocumentationCompliance.summary?.assurance_status || "unknown"}
                    </span>
                    <span className="surface-chip">
                      Standard {novatechDocumentationCompliance.summary?.standard_protocol || "AfriCPPT"}
                    </span>
                    <span className="surface-chip">
                      Tenants {novatechDocumentationCompliance.summary?.tenant_count || 0}
                    </span>
                    <span className="surface-chip">
                      Tenant {novatechDocumentationCompliance.summary?.current_tenant_status || "unknown"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Organization OS and governance</strong>
                  <div className="chip-row">
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.organization_governance?.directory_surface || "/v1/novatech/organizations"}
                    >
                      Organization directory
                    </a>
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.organization_governance?.detail_surface || "/v1/novatech/organizations/org-nova"}
                    >
                      Tenant detail
                    </a>
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.organization_governance?.billing_surface || "/v1/novatech/organizations/org-nova/billing"}
                    >
                      Billing
                    </a>
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.organization_governance?.execution_surface || "/v1/novatech/organizations/org-nova/execution"}
                    >
                      Execution
                    </a>
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.organization_governance?.public_documentation_portal || "/public/documentation/portal"}
                    >
                      Public docs portal
                    </a>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Certification and public verification</strong>
                  <div className="chip-row">
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.certification_issuance?.issue_surface || "/v1/novatech/documentation/certification/issue"}
                    >
                      Issue certification
                    </a>
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.public_verification?.portal_surface || "/public/verify/portal"}
                    >
                      Public verification
                    </a>
                    <a
                      className="surface-chip"
                      href={novatechDocumentationCompliance.public_verification?.documentation_portal_surface || "/public/documentation/portal"}
                    >
                      Documentation portal
                    </a>
                    <span className="surface-chip">
                      Policy {novatechDocumentationCompliance.summary?.policy_count || 0}
                    </span>
                    <span className="surface-chip">
                      Trust {novatechDocumentationCompliance.summary?.trust_score || 0}
                    </span>
                    <span className="surface-chip">
                      Assurance {novatechDocumentationCompliance.summary?.assurance_status || "unknown"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Marketplace and onboarding</strong>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Services {novatechDocumentationCompliance.summary?.marketplace_services || 0}
                    </span>
                    <span className="surface-chip">
                      Onboarding {novatechDocumentationCompliance.marketplace_onboarding?.phases?.length || 0} phases
                    </span>
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Documentation compliance will appear after the registry is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Current Tenant Detail">
            {novatechCurrentTenant ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novatechCurrentTenant.organization_name}</strong>
                    <span>{novatechCurrentTenant.status}</span>
                  </div>
                  <p>{novatechCurrentTenant.legal_name || novatechCurrentTenant.organization_name}</p>
                  <div className="chip-row">
                    <span className="surface-chip">{novatechCurrentTenant.tenant_model}</span>
                    <span className="surface-chip">{novatechCurrentTenant.source}</span>
                    <span className="surface-chip">{novatechCurrentTenant.trust_domain}</span>
                  </div>
                  <div className="chip-row">
                    <span className="surface-chip">{novatechCurrentTenant.certification_label || "Uncertified"}</span>
                    <span className="surface-chip">{novatechCurrentTenant.billing_status}</span>
                    <span className="surface-chip">Trust {novatechCurrentTenant.trust_score}</span>
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Current tenant details will appear after the first organization snapshot." />
            )}
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band outcome-band" id="outcomes">
        <SectionIntro
          eyebrow="Outcome Intelligence"
          title="Outcome registry, learning, scoring, and replay"
          question="The platform measures results, keeps the memory, and recalibrates without taking authority away from the operator."
        />
        <p className="section-note">
          Outcome intelligence stays projection-only. It composes trust, replay, and evidence into
          a persistent operating memory that operators can review, trend, and exchange across
          tenants.
        </p>
        <div className="metric-grid">
          <TrustMetric
            label="Outcome score"
            value={novatechOutcomeCurrent?.outcome_score || 0}
            helper={novatechOutcomeCurrent?.measurement_summary || "Measured from trust, replay, and evidence."}
            tone={novatechOutcomeCurrent?.outcome_band === "excellent" ? "success" : "neutral"}
          />
          <TrustMetric
            label="Learning band"
            value={novatechOutcomeLearning?.band || "hold"}
            helper="Observe → decide → recommend → measure outcome → learn → recalibrate."
            tone={novatechOutcomeLearning?.band === "recalibrate" ? "success" : "warning"}
          />
          <TrustMetric
            label="Trust network"
            value={novatechTrustNetwork?.member_count || novatechTrustNetwork?.global_trust?.member_count || 0}
            helper="Federated organizations exchanging trust, proof, and certification."
          />
          <TrustMetric
            label="Marketplace services"
            value={novatechMarketplace?.summary?.service_count || novatechMarketplace?.service_count || 0}
            helper="Trust, verification, certification, and replay services."
          />
        </div>
        <div className="operator-grid">
          <OperatorPanel title="Outcome Registry">
            <div className="stack">
              <AnalyticsTrendPanel
                title="Outcome score trend"
                description="Historical outcome scores are persisted and replayable."
                history={novatechOutcomeRegistry?.items || []}
                valueKey="outcome_score"
                currentValue={novatechOutcomeCurrent?.outcome_score || 0}
                accent="#195d8a"
                unit=""
                stats={[
                  { label: "Status", value: novatechOutcomeCurrent?.outcome_status || "learning" },
                  { label: "Band", value: novatechOutcomeCurrent?.outcome_band || "guarded" },
                  { label: "History", value: novatechOutcomeRegistry?.count || 0 },
                ]}
              />
              {novatechOutcomeCurrent ? (
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novatechOutcomeCurrent.outcome_type}</strong>
                    <span>{novatechOutcomeCurrent.outcome_status}</span>
                  </div>
                  <p>{novatechOutcomeCurrent.measurement_summary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">Band {novatechOutcomeCurrent.outcome_band}</span>
                    <span className="surface-chip">Learning {novatechOutcomeCurrent.learning_band}</span>
                    <span className="surface-chip">Replay {novatechOutcomeReplay?.status || "ready"}</span>
                    <span className="surface-chip">
                      Score {novatechOutcomeScoring?.score || novatechOutcomeCurrent.outcome_score || 0}
                    </span>
                  </div>
                </article>
              ) : (
                <EmptyState label="Outcome registry will appear after the first outcome snapshot." />
              )}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Outcome Learning">
            {novatechOutcomeLearning ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novatechOutcomeLearning.band}</strong>
                    <span>{novatechOutcomeLearning.cycle?.length || 0} steps</span>
                  </div>
                  <p>
                    {novatechOutcomeCurrent?.measurement_summary ||
                      "Outcome learning keeps the platform ready for recalibration."}
                  </p>
                  <div className="chip-row">
                    {(novatechOutcomeLearning.cycle || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Recommendations</strong>
                  <div className="stack compact-stack">
                    {(novatechOutcomeLearning.recommendations || []).map((recommendation) => (
                      <div key={recommendation} className="reason-chip">
                        {recommendation}
                      </div>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Recalibration notes</strong>
                  <div className="chip-row">
                    {(novatechOutcomeLearning.recalibration_notes || []).map((note) => (
                      <span key={note} className="surface-chip">
                        {note}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Watch items</strong>
                  <div className="chip-row">
                    {(novatechOutcomeLearning.watch_items || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Outcome learning will appear after a measured outcome is stored." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Federated Trust Network">
            {novatechTrustNetwork ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Global trust</strong>
                    <span>{novatechTrustNetwork.status || "ready"}</span>
                  </div>
                  <p>
                    Members {novatechTrustNetwork.member_count || 0} and exchanges{" "}
                    {novatechTrustNetwork.exchange_catalog?.length || 0}.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Nodes {novatechTrustNetwork.distributed_trust_network?.peers?.length || 0}
                    </span>
                    <span className="surface-chip">
                      Trust graph {novatechTrustNetwork.trust_graph?.node_count || 0} nodes
                    </span>
                    <span className="surface-chip">
                      Exchanges {novatechTrustNetwork.trust_graph?.edge_count || 0}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Exchange catalog</strong>
                  <div className="stack compact-stack">
                    {(novatechTrustNetwork.exchange_catalog || []).map((entry) => (
                      <article key={entry.service_id} className="record-card">
                        <div className="record-card-header">
                          <strong>{entry.name}</strong>
                          <span>{entry.service_type}</span>
                        </div>
                        <p>{entry.description}</p>
                        <div className="chip-row">
                          {entry.routes.map((route) => (
                            <span key={route} className="surface-chip">
                              {route}
                            </span>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Tenant exchange pairs</strong>
                  <div className="stack compact-stack">
                    {(novatechTrustNetwork.tenant_pairs || []).slice(0, 4).map((pair) => (
                      <div key={`${pair.issuer_org}:${pair.subject_org}`} className="reason-chip">
                        {pair.issuer_org} &rarr; {pair.subject_org}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Federated trust network will appear after organizations are onboarded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Trust Marketplace">
            {novatechMarketplace ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Marketplace status</strong>
                    <span>{novatechMarketplace.status || "ready"}</span>
                  </div>
                  <p>
                    {novatechMarketplace.summary?.service_count || novatechMarketplace.service_count || 0} services
                    available across {novatechMarketplace.summary?.tenant_count || novatechMarketplace.tenant_count || 0} tenants.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Trust network {novatechMarketplace.summary?.trust_member_count || 0}
                    </span>
                    {(novatechMarketplace.summary?.exchange_modes || []).map((mode) => (
                      <span key={mode} className="surface-chip">
                        {mode.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <div className="stack compact-stack">
                  {(novatechMarketplace.services || []).map((service) => (
                    <article key={service.service_id} className="record-card">
                      <div className="record-card-header">
                        <strong>{service.name}</strong>
                        <span>{service.service_type}</span>
                      </div>
                      <p>{service.summary}</p>
                      <div className="chip-row">
                        <span className="surface-chip">
                          {service.consumable_across_tenants ? "cross-tenant" : "tenant-only"}
                        </span>
                        {service.routes.map((route) => (
                          <span key={route} className="surface-chip">
                            {route}
                          </span>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState label="Trust marketplace services will appear after the marketplace surface is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Partner Onboarding Strategy">
            {novatechMarketplaceOnboarding ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Marketplace rollout</strong>
                    <span>{novatechMarketplaceOnboarding.status || "ready"}</span>
                  </div>
                  <p>
                    {novatechMarketplaceOnboarding.summary?.service_count || 0} services across{" "}
                    {novatechMarketplaceOnboarding.summary?.tenant_count || 0} tenants with{" "}
                    {novatechMarketplaceOnboarding.summary?.trust_member_count || 0} trust members.
                  </p>
                  <div className="chip-row">
                    {(novatechMarketplaceOnboarding.summary?.exchange_modes || []).map((mode) => (
                      <span key={mode} className="surface-chip">
                        {mode.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <div className="stack compact-stack">
                  {(novatechMarketplaceOnboarding.phases || []).map((phase) => (
                    <article key={phase.phase} className="record-card">
                      <div className="record-card-header">
                        <strong>{phase.title}</strong>
                        <span>{phase.phase}</span>
                      </div>
                      <p>{phase.goal}</p>
                      <div className="chip-row">
                        {(phase.entry_criteria || []).map((criterion) => (
                          <span key={criterion} className="surface-chip">
                            {criterion}
                          </span>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
                <div className="stack compact-stack">
                  {(novatechMarketplaceOnboarding.partner_cohort || FIRST_PARTNER_COHORT).map(
                    (partner) => (
                      <article key={partner.name} className="record-card">
                        <div className="record-card-header">
                          <strong>{partner.name}</strong>
                          <span>{partner.role}</span>
                        </div>
                        <p>{partner.goal}</p>
                      </article>
                    ),
                  )}
                </div>
              </div>
            ) : (
              <EmptyState label="Partner onboarding strategy will appear after the marketplace surface is loaded." />
            )}
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
        <OperatorPanel title="NovaTrust Public Explorer UI">
          <div className="stack">
            <TrustExplorerFrontend explorer={NOVATRUST_PUBLIC_EXPLORER} />
            <article className="record-card">
              <div className="record-card-header">
                <strong>{NOVATRUST_PUBLIC_EXPLORER.route}</strong>
                <span>public verification</span>
              </div>
              <p>
                External verifiers can inspect a receipt or trust identifier without
                gaining execution authority. The API packet is available at {NOVATRUST_PUBLIC_EXPLORER.apiRoute}.
              </p>
              <div className="chip-row">
                {NOVATRUST_PUBLIC_EXPLORER.zones.map((zone) => (
                  <span key={zone} className="surface-chip">{zone}</span>
                ))}
              </div>
            </article>
            <article className="record-card">
              <div className="record-card-header">
                <strong>Deploy one pilot flow</strong>
                <span>{NOVATRUST_PUBLIC_EXPLORER.pilotFlow}</span>
              </div>
              <p>
                Run one authenticated core-platform payment flow, persist the proof
                packet, then open the generated NovaTrust explorer link.
              </p>
            </article>
          </div>
        </OperatorPanel>
        <OperatorPanel title="Live Verifier API">
          <LiveVerifierPanel apiBaseUrl={API_BASE_URL} />
        </OperatorPanel>
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

      <section className="section-band novapay-apps-band" id="payments">
        <SectionIntro
          eyebrow="NovaPay UI/UX Platform"
          title="Role-based apps over one governed financial runtime"
          question="Consumer, agent, merchant, business, operations, compliance, support, administration, and developer surfaces share the same transfer engine, ledger, event platform, audit, and proof model."
        />
        <OperatorPanel title="NovaPay Ecosystem Control Plane">
          <div className="stack">
            <article className="record-card novapay-control-card">
              <div className="record-card-header">
                <strong>NovaPay Core Control Plane</strong>
                <span>single governed runtime</span>
              </div>
              <p>
                Transfer Engine, Ledger, Event Platform, Audit & Proof remain central. Each NovaPay
                app is a role-specific interface over the same governed transfer lifecycle.
              </p>
              <div className="chip-row">
                {NOVAPAY_CONTROL_PLANE_GUARANTEES.map((guarantee) => (
                  <span key={guarantee} className="surface-chip">{guarantee}</span>
                ))}
              </div>
            </article>
            <div className="operator-grid dense-grid">
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Shared Platform Services</strong>
                  <span>{NOVAPAY_SHARED_SERVICES.length} services</span>
                </div>
                <div className="flow-line" aria-label="NovaPay shared platform services">
                  {NOVAPAY_SHARED_SERVICES.map((service) => (
                    <span key={service}>{service}</span>
                  ))}
                </div>
              </article>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>Unified Domain Model</strong>
                  <span>{NOVAPAY_UNIFIED_DOMAIN_MODEL.length} domains</span>
                </div>
                <div className="flow-line" aria-label="NovaPay unified domain model">
                  {NOVAPAY_UNIFIED_DOMAIN_MODEL.map((domain) => (
                    <span key={domain}>{domain}</span>
                  ))}
                </div>
              </article>
            </div>
          </div>
        </OperatorPanel>

        <OperatorPanel title="NovaPay Role-Based Applications">
          <div className="novapay-app-grid">
            {NOVAPAY_ROLE_APPS.map((app) => (
              <article key={app.name} className="record-card novapay-app-card">
                <div className="record-card-header">
                  <strong>{app.name}</strong>
                  <span>{app.surface}</span>
                </div>
                <p>{app.audience}</p>
                <div className="chip-row" aria-label={`${app.name} navigation`}>
                  {app.navigation.map((item) => (
                    <span key={item} className="surface-chip">{item}</span>
                  ))}
                </div>
                <div className="stack compact-stack">
                  <strong>Expected capabilities</strong>
                  <div className="chip-row">
                    {app.capabilities.map((capability) => (
                      <span key={capability} className="reason-chip">{capability}</span>
                    ))}
                  </div>
                </div>
                <div className="record-card-footer">
                  <span>{app.primaryFlow}</span>
                </div>
              </article>
            ))}
          </div>
        </OperatorPanel>

        <OperatorPanel title="NovaPay Priority App Build Specifications">
          <div className="novapay-build-grid">
            {NOVAPAY_PRIORITY_APP_BUILDS.map((app) => (
              <article key={app.name} className="record-card novapay-build-card">
                <div className="record-card-header">
                  <strong>{app.productLabel}</strong>
                  <span>{app.surface}</span>
                </div>
                <p>{app.persona}</p>
                <p>{app.promise}</p>
                <div className="novapay-build-section">
                  <strong>Primary screens</strong>
                  <div className="chip-row">
                    {app.screens.map((screen) => (
                      <span key={screen} className="surface-chip">{screen}</span>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Core workflow</strong>
                  <div className="flow-line" aria-label={`${app.name} workflow`}>
                    {app.workflow.map((step) => (
                      <span key={step}>{step}</span>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Governed backend bindings</strong>
                  <div className="git-pull-list">
                    {app.backendBindings.map((binding) => (
                      <code key={binding}>{binding}</code>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Trust and proof widgets</strong>
                  <div className="chip-row">
                    {app.proofWidgets.map((widget) => (
                      <span key={widget} className="reason-chip reason-chip-success">{widget}</span>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </OperatorPanel>

        <OperatorPanel title="NovaPay Merchant and Agent Web Portals">
          <div className="novapay-portal-grid">
            {NOVAPAY_PORTAL_APP_BUILDS.map((portal) => (
              <article key={portal.name} className="record-card novapay-portal-card">
                <div className="record-card-header">
                  <strong>{portal.productLabel}</strong>
                  <span>{portal.surface}</span>
                </div>
                <p>{portal.audience}</p>
                <p>{portal.outcome}</p>
                <div className="novapay-build-section">
                  <strong>Portal pages</strong>
                  <div className="chip-row">
                    {portal.pages.map((page) => (
                      <span key={page} className="surface-chip">{page}</span>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Command center actions</strong>
                  <div className="chip-row">
                    {portal.commandCenter.map((action) => (
                      <span key={action} className="reason-chip">{action}</span>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Web workflow</strong>
                  <div className="flow-line" aria-label={`${portal.name} web workflow`}>
                    {portal.webWorkflow.map((step) => (
                      <span key={step}>{step}</span>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Governed backend bindings</strong>
                  <div className="git-pull-list">
                    {portal.backendBindings.map((binding) => (
                      <code key={binding}>{binding}</code>
                    ))}
                  </div>
                </div>
                <div className="novapay-build-section">
                  <strong>Portal proof controls</strong>
                  <div className="chip-row">
                    {portal.proofControls.map((control) => (
                      <span key={control} className="reason-chip reason-chip-success">{control}</span>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </OperatorPanel>

        <OperatorPanel title="NovaPay Implementation Roadmap">
          <div className="roadmap-lane">
            {NOVAPAY_IMPLEMENTATION_ROADMAP.map((step, index) => (
              <article key={step} className="record-card roadmap-step">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{step}</strong>
              </article>
            ))}
          </div>
        </OperatorPanel>
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

function AnalyticsTrendPanel({
  title,
  description,
  history,
  valueKey,
  currentValue,
  accent = "#1f7a55",
  unit = "",
  stats = [],
  emptyLabel = "Collecting live samples...",
}) {
  const values = chartPoints(history, valueKey);
  const latest = values.length > 0 ? values[values.length - 1] : 0;
  const min = values.length > 0 ? Math.min(...values) : 0;
  const max = values.length > 0 ? Math.max(...values) : 0;
  const svgWidth = 360;
  const svgHeight = 128;

  return (
    <div className="analytics-trend-panel">
      <div className="record-card-header">
        <div>
          <span className="surface-chip">Live analytics</span>
          <h4>{title}</h4>
        </div>
        <strong>{currentValue}</strong>
      </div>
      <p>{description}</p>
      {values.length > 0 ? (
        <svg
          className="analytics-chart"
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          role="img"
          aria-label={title}
        >
          <defs>
            <linearGradient id={`analytics-area-${valueKey}`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={accent} stopOpacity="0.24" />
              <stop offset="100%" stopColor={accent} stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <rect x="0" y="0" width={svgWidth} height={svgHeight} rx="8" fill="#f8fbfc" />
          <path d={buildAreaPath(values, svgWidth, svgHeight, 12)} fill={`url(#analytics-area-${valueKey})`} />
          <path
            d={buildPolylinePath(values, svgWidth, svgHeight, 12)}
            fill="none"
            stroke={accent}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ) : (
        <EmptyState label={emptyLabel} />
      )}
      <div className="analytics-stat-row" aria-label={`${title} summary stats`}>
        <div>
          <span>Latest</span>
          <strong>
            {latest}
            {unit}
          </strong>
        </div>
        <div>
          <span>Low</span>
          <strong>
            {min}
            {unit}
          </strong>
        </div>
        <div>
          <span>High</span>
          <strong>
            {max}
            {unit}
          </strong>
        </div>
      </div>
      {stats.length > 0 && (
        <div className="analytics-stat-row analytics-stat-row-secondary">
          {stats.map((stat) => (
            <div key={stat.label}>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function NotificationFeed({ notifications }) {
  if (notifications.length === 0) {
    return <EmptyState label="No operator notifications yet." />;
  }

  return (
    <div className="stack">
      {notifications.map((notification) => (
        <article key={notification.id} className={`record-card notification-card notification-${notification.severity}`}>
          <div className="record-card-header">
            <strong>{notification.title}</strong>
            <span>{notification.severity}</span>
          </div>
          <p>{notification.detail}</p>
          <div className="chip-row">
            <span className="surface-chip">{notification.source}</span>
            <span className="surface-chip">{notification.timestamp || "live"}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function AnalyticsInsightFeed({ insights }) {
  if (!insights || insights.length === 0) {
    return <EmptyState label="AI insights will appear after the first persisted analytics snapshot." />;
  }

  return (
    <div className="stack">
      {insights.map((insight) => (
        <article
          key={insight.id}
          className={`record-card insight-card insight-${insight.severity || "info"}`}
        >
          <div className="record-card-header">
            <strong>{insight.title}</strong>
            <span>{insight.severity || "info"}</span>
          </div>
          <p>{insight.detail}</p>
          <div className="chip-row">
            <span className="surface-chip">AI insight</span>
            {insight.id && <span className="surface-chip">{insight.id}</span>}
          </div>
        </article>
      ))}
    </div>
  );
}

function PredictionPanel({ prediction, latest, trend }) {
  if (!prediction) {
    return (
      <EmptyState label="Predictive analytics will appear once the history store contains enough snapshots." />
    );
  }

  const riskTone =
    (prediction.riskLevel || prediction.risk_level) === "low"
      ? "success"
      : (prediction.riskLevel || prediction.risk_level) === "medium"
        ? "warning"
        : "warning";
  const forecastTrust =
    prediction.predictedTrustScore ?? prediction.predicted_trust_score ?? 0;
  const forecastCoverage =
    prediction.predictedEvidenceCoverage ?? prediction.predicted_evidence_coverage ?? 0;
  const forecastException =
    prediction.predictedExceptionPressure ?? prediction.predicted_exception_pressure ?? 0;
  const watchItems = prediction.watchItems || prediction.watch_items || [];

  return (
    <div className="stack">
      <article
        className={`record-card prediction-card prediction-${
          prediction.riskLevel || prediction.risk_level || "low"
        }`}
      >
        <div className="record-card-header">
          <strong>{prediction.headline || "Predictive outlook"}</strong>
          <span>{prediction.riskLevel || prediction.risk_level || "unknown"}</span>
        </div>
        <p>{prediction.confidence ? `Confidence ${Math.round(prediction.confidence * 100)}%` : ""}</p>
        <div className="prediction-metrics">
          <KeyValue
            label="Forecast trust"
            value={forecastTrust}
            tone={riskTone}
          />
          <KeyValue
            label="Forecast coverage"
            value={`${forecastCoverage}%`}
            tone={forecastCoverage >= 95 ? "success" : "warning"}
          />
          <KeyValue
            label="Exception pressure"
            value={forecastException}
            tone={riskTone}
          />
        </div>
        {Array.isArray(watchItems) && watchItems.length > 0 && (
          <div className="chip-row">
            {watchItems.map((item) => (
              <span key={item} className="surface-chip">
                {item}
              </span>
            ))}
          </div>
        )}
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Forecast context</strong>
          <span>{trend?.trust?.direction || "stable"}</span>
        </div>
        <p>
          Latest trust {latest?.trustScore ?? 0}, coverage {latest?.evidenceCoverage ?? 0}%, pressure{" "}
          {latest?.exceptionPressure ?? 0}. The forecast is derived from the persisted analytics trail.
        </p>
      </article>
    </div>
  );
}

function DemandForecastPanel({ demandForecast }) {
  if (!demandForecast) {
    return <EmptyState label="Predictive demand ML will appear after the first live demand forecast snapshot." />;
  }

  const liveState = demandForecast.realtime_analytics?.live_state || {};
  const cityForecasts = demandForecast.city_forecasts || [];
  const forecastWindows = demandForecast.forecast_windows || [];
  const recommendation = demandForecast.recommendation || {};
  const model = demandForecast.model || {};

  return (
    <div className="stack">
      <article className="record-card">
        <div className="record-card-header">
          <strong>{model.name || "bounded_demand_forecast_ml"}</strong>
          <span>{model.mode || "deterministic_heuristic"}</span>
        </div>
        <div className="prediction-metrics">
          <KeyValue label="Primary city" value={recommendation.primary_city || liveState.zone || "CBD"} />
          <KeyValue label="Demand level" value={liveState.demand_level || "low"} />
          <KeyValue label="Demand index" value={liveState.demand_index ?? 0} tone={liveState.demand_level === "high" ? "warning" : "success"} />
          <KeyValue label="Supply gap" value={liveState.supply_gap ?? 0} tone={liveState.supply_gap > 0 ? "warning" : "success"} />
        </div>
        <div className="chip-row">
          <span className="surface-chip">{recommendation.urgency || "monitor"}</span>
          <span className="surface-chip">{recommendation.action || "Maintain watch"}</span>
          <span className="surface-chip">Trust {liveState.trust_score || 0}</span>
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Forecast windows</strong>
          <span>next operating windows</span>
        </div>
        <div className="stack">
          {forecastWindows.map((window) => (
            <div key={window.horizon} className="row-between">
              <span>{window.horizon}</span>
              <span>
                {window.expected_rides} rides / gap {window.expected_supply_gap}
              </span>
            </div>
          ))}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Top city pressure</strong>
          <span>{cityForecasts[0]?.city || liveState.zone || "CBD"}</span>
        </div>
        <div className="stack">
          {cityForecasts.slice(0, 4).map((city) => (
            <div key={city.city} className="row-between">
              <span>{city.city}</span>
              <span>
                {city.demand_level} · gap {city.supply_gap}
              </span>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}

function RealtimeAnalyticsPanel({ demandForecast, liveAnalyticsSnapshot }) {
  const liveState = demandForecast?.realtime_analytics?.live_state || {};
  const alerts = demandForecast?.realtime_analytics?.alerts || [];
  const snapshot = liveAnalyticsSnapshot || {};

  return (
    <div className="stack">
      <article className="record-card">
        <div className="record-card-header">
          <strong>Live state</strong>
          <span>{liveState.zone || "CBD"}</span>
        </div>
        <div className="prediction-metrics">
          <KeyValue label="Active rides" value={liveState.active_rides ?? snapshot.activeRides ?? 0} />
          <KeyValue label="Active drivers" value={liveState.active_drivers ?? snapshot.onlineDrivers ?? 0} />
          <KeyValue label="Completed rides" value={liveState.completed_rides ?? snapshot.completedRides ?? 0} />
          <KeyValue label="Demand index" value={liveState.demand_index ?? 0} tone={liveState.demand_level === "high" ? "warning" : "success"} />
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Realtime alerts</strong>
          <span>bounded</span>
        </div>
        <div className="stack">
          {(alerts.length > 0 ? alerts : ["No active alerts in the demand feed."]).map((item) => (
            <div key={item} className="row-between">
              <span>{item}</span>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}

function StrategyEnginePanel({ strategyEngine }) {
  if (!strategyEngine) {
    return <EmptyState label="Phase 5 autonomous strategy will appear after the first bounded strategy snapshot." />;
  }

  const strategy = strategyEngine.strategy || {};
  const guardrails = strategy.guardrails || {};
  const cityPriorities = strategy.city_priorities || [];
  const recommendation = strategy.recommendation || {};
  const budgetAllocation = strategyEngine.budget_allocation?.budget_allocation || {};
  const profitOptimization = strategyEngine.profit_optimization?.profit_optimization || {};

  return (
    <div className="stack">
      <article className="record-card">
        <div className="record-card-header">
          <strong>{strategyEngine.model?.name || "bounded_autonomous_strategy_engine"}</strong>
          <span>{strategy.mode || "supervised"}</span>
        </div>
        <div className="prediction-metrics">
          <KeyValue label="Primary city" value={strategy.primary_city || recommendation.primary_city || "CBD"} />
          <KeyValue label="Strategy lane" value={strategy.strategy_lane || "monitor"} />
          <KeyValue label="Priority score" value={strategy.priority_score ?? 0} tone="warning" />
          <KeyValue label="Mode" value={strategy.mode || "supervised"} />
        </div>
        <div className="chip-row">
          <span className="surface-chip">{recommendation.action || "Maintain watch"}</span>
          <span className="surface-chip">{recommendation.next_step || "Review operator strategy plan"}</span>
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>City priorities</strong>
          <span>{strategy.city_count || 0} cities</span>
        </div>
        <div className="stack">
          {cityPriorities.slice(0, 4).map((city) => (
            <div key={city.city} className="row-between">
              <span>{city.city}</span>
              <span>
                {city.strategy_lane} · {city.demand_level} · {city.priority_score}
              </span>
            </div>
          ))}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Budget and profit context</strong>
          <span>{budgetAllocation.mode || "supervised"}</span>
        </div>
        <div className="prediction-metrics">
          <KeyValue label="Budget pool" value={budgetAllocation.budget_pool || "0.00"} />
          <KeyValue label="Projected profit" value={profitOptimization.projected_profit || "0.00"} />
          <KeyValue label="Profit uplift" value={profitOptimization.profit_uplift || "0.00"} />
          <KeyValue label="Target margin" value={profitOptimization.target_margin ?? 0.35} />
        </div>
      </article>
    </div>
  );
}

function StrategyGuardrailsPanel({ strategyEngine }) {
  if (!strategyEngine) {
    return <EmptyState label="Strategy guardrails will appear after the first operator strategy snapshot." />;
  }

  const guardrails = strategyEngine.strategy?.guardrails || {};
  const readiness = strategyEngine.readiness || {};
  const decisionHistory = strategyEngine.decision_history || {};

  return (
    <div className="stack">
      <article className="record-card">
        <div className="record-card-header">
          <strong>Guardrails</strong>
          <span>{strategyEngine.strategy?.mode || "advisory"}</span>
        </div>
        <div className="stack">
          {Object.entries(guardrails).map(([label, value]) => (
            <div key={label} className="row-between">
              <span>{label.replace(/_/g, " ")}</span>
              <span>{String(value)}</span>
            </div>
          ))}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Readiness</strong>
          <span>bounded</span>
        </div>
        <div className="stack">
          {Object.entries(readiness).map(([label, value]) => (
            <div key={label} className="row-between">
              <span>{label.replace(/_/g, " ")}</span>
              <span>{String(value)}</span>
            </div>
          ))}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Decision history</strong>
          <span>{decisionHistory.updated_at || "live"}</span>
        </div>
        <div className="stack">
          {(decisionHistory.decision_chain || []).map((item) => (
            <div key={item} className="row-between">
              <span>{item}</span>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}

function AnalyticsHistoryFeed({ history, sourceBreakdown }) {
  if (!history || history.length === 0) {
    return <EmptyState label="No persistent analytics history yet. The dashboard will seed it automatically." />;
  }

  const recentHistory = history.slice(-8).reverse();

  return (
    <div className="stack">
      <div className="chip-row">
        {Object.entries(sourceBreakdown || {}).map(([source, count]) => (
          <span key={source} className="surface-chip">
            {source}: {count}
          </span>
        ))}
      </div>
      {recentHistory.map((snapshot) => (
        <article key={snapshot.snapshotId} className="record-card history-card">
          <div className="record-card-header">
            <strong>
              {snapshot.createdAt
                ? new Date(snapshot.createdAt).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })
                : snapshot.windowBucket || "live"}
            </strong>
            <span>{snapshot.source}</span>
          </div>
          <div className="chip-row">
            <span className="surface-chip">Trust {snapshot.trustScore}</span>
            <span className="surface-chip">Coverage {snapshot.evidenceCoverage}%</span>
            <span className="surface-chip">Pressure {snapshot.exceptionPressure}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function decisionLaneTone(lane) {
  if (lane === "escalate") {
    return "critical";
  }
  if (lane === "review") {
    return "warning";
  }
  if (lane === "watch") {
    return "neutral";
  }
  return "success";
}

function DecisionSummaryPanel({ decision, latest }) {
  if (!decision) {
    return <EmptyState label="No decision snapshots are available yet. The operator dashboard seeds one automatically." />;
  }

  const laneTone = decisionLaneTone(decision.decisionLane);
  const reasoning = decision.reasoning || {};
  const trustTrend = reasoning.trust_trend || {};
  const evidenceTrend = reasoning.evidence_trend || {};
  const exceptionTrend = reasoning.exception_trend || {};
  const riskPrediction = reasoning.risk_prediction || {};

  return (
    <div className="stack">
      <article className={`record-card decision-card decision-${decision.decisionLane || "observe"}`}>
        <div className="record-card-header">
          <div>
            <strong>{decision.decisionLane || "observe"}</strong>
            <span className="decision-action-label">
              {decision.decisionAction || "continue_monitoring"}
            </span>
          </div>
          <span>{decision.decisionPriority || "low"}</span>
        </div>
        <p>{decision.decisionSummary || "The decision engine is waiting for a persisted operating window."}</p>
        <div className="decision-stat-row">
          <KeyValue label="Confidence" value={`${Math.round((decision.confidence || 0) * 100)}%`} tone={laneTone} />
          <KeyValue label="Stability" value={decision.stabilityIndex || 0} tone={laneTone} />
          <KeyValue label="Risk" value={`${decision.riskLevel || "unknown"} / ${decision.riskScore || 0}`} />
          <KeyValue label="Latest record" value={latest?.decisionId || decision.latestRecordId || "pending"} />
        </div>
        <div className="chip-row">
          <span className="surface-chip">{decision.advisoryOnly ? "Advisory only" : "Execution ready"}</span>
          <span className="surface-chip">{decision.readOnly ? "Read only" : "Writable"}</span>
          <span className="surface-chip">{decision.projectionOnly ? "Projection only" : "Authority"}</span>
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Why this lane was chosen</strong>
          <span>{riskPrediction.risk_level || decision.riskLevel || "unknown"}</span>
        </div>
        <div className="stack compact-stack">
          {trustTrend.direction && (
            <div className="reason-chip">
              Trust trend: {trustTrend.direction} {trustTrend.slope ?? 0}
            </div>
          )}
          {evidenceTrend.direction && (
            <div className="reason-chip">
              Evidence trend: {evidenceTrend.direction} {evidenceTrend.slope ?? 0}
            </div>
          )}
          {exceptionTrend.direction && (
            <div className="reason-chip">
              Exception trend: {exceptionTrend.direction} {exceptionTrend.slope ?? 0}
            </div>
          )}
          {riskPrediction.confidence !== undefined && (
            <div className="reason-chip">
              Risk confidence: {Math.round((riskPrediction.confidence || 0) * 100)}%
            </div>
          )}
          {(!trustTrend.direction && !evidenceTrend.direction && !exceptionTrend.direction && !riskPrediction.confidence) && (
            <div className="reason-chip reason-chip-success">
              Awaiting the first persisted decision explanation.
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

function OperationAIDecisionPanel({
  decision,
  action,
  liveAnalyticsSnapshot,
  liveNotifications,
  novarideOperatorDashboardContract,
  novarideEcosystem,
  operatorAutonomy,
  operatorCityAutomation,
  operatorMultiCityOrchestration,
  operatorDigitalTwin,
  operatorMetaLearningRedesign,
  operatorBusinessPricing,
  activeRidesCount,
  operationState: providedOperationState = null,
}) {
  const operationState =
    providedOperationState ||
    deriveOperationAIDecisionState({
      decision,
      action,
      liveAnalyticsSnapshot,
      novarideOperatorDashboardContract,
      novarideEcosystem,
      liveNotifications,
      activeRidesCount,
    });
  const autonomy = operatorAutonomy?.autonomy || operatorAutonomy || action?.autonomy || {};
  const driverAllocation =
    operatorAutonomy?.driver_allocation ||
    autonomy.driver_allocation ||
    action?.driver_allocation ||
    action?.autonomy?.driver_allocation ||
    {};
  const cityAutomation =
    operatorCityAutomation?.city_automation ||
    operatorAutonomy?.city_automation ||
    autonomy.city_automation ||
    action?.city_automation ||
    {};
  const multiCityOrchestration =
    operatorMultiCityOrchestration?.multi_city_orchestration ||
    operatorAutonomy?.multi_city_orchestration ||
    action?.multi_city_orchestration ||
    {};
  const digitalTwin =
    operatorDigitalTwin?.digital_twin ||
    operatorDigitalTwin ||
    operatorMultiCityOrchestration?.digital_twin ||
    operatorAutonomy?.digital_twin ||
    action?.digital_twin ||
    {};
  const selfImprovingLoop =
    operatorDigitalTwin?.self_improving_loop ||
    operatorDigitalTwin?.digital_twin?.self_improving_loop ||
    operatorMultiCityOrchestration?.self_improving_loop ||
    operatorAutonomy?.self_improving_loop ||
    action?.self_improving_loop ||
    digitalTwin.self_improving_loop ||
    {};
  const metaLearningRedesign =
    operatorMetaLearningRedesign?.candidate_redesign ||
    operatorMetaLearningRedesign?.meta_learning_redesign ||
    operatorMetaLearningRedesign ||
    {};
  const metaLearningMode =
    operatorMetaLearningRedesign?.mode ||
    (metaLearningRedesign?.review?.admitted ? "adaptive_redesign" : "design_hold");
  const safeThresholds = autonomy.thresholds || action?.autonomy?.thresholds || {};
  const thresholdChecks = autonomy.checks || action?.autonomy?.checks || {};

  return (
    <div className="stack">
      <article className={`record-card operation-ai-card decision-${operationState.lane}`}>
        <div className="record-card-header">
          <div>
            <strong>{operationState.dispatchPosture}</strong>
            <span className="decision-action-label">{operationState.controlSignal}</span>
          </div>
          <span>{autonomy.release_status || operationState.priority}</span>
        </div>
        <p>{operationState.summary}</p>
        <div className="decision-stat-row">
          <KeyValue label="Confidence" value={`${Math.round(operationState.confidence * 100)}%`} tone={operationState.laneTone} />
          <KeyValue label="Trust health" value={operationState.trustHealth || 0} tone={operationState.laneTone} />
          <KeyValue label="Replay health" value={operationState.replayHealth || 0} tone={operationState.laneTone} />
          <KeyValue label="Evidence" value={`${operationState.evidenceCoverage || 0}%`} tone={operationState.laneTone} />
        </div>
        <div className="chip-row">
          <span className="surface-chip">Dispatch pressure {operationState.demandPressure}</span>
          <span className="surface-chip">Demand {operationState.demandLabel}</span>
          <span className="surface-chip">Driver supply {operationState.driverSupplyLabel}</span>
          <span className="surface-chip">Active rides {operationState.activeRidesCount || 0}</span>
          <span className="surface-chip">
            Autonomy {autonomy.mode || "advisory"}
          </span>
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Operator move</strong>
          <span>Read only</span>
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">{operationState.operatorMove}</div>
          {(operationState.recommendedActions || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
          {(!operationState.recommendedActions || operationState.recommendedActions.length === 0) && (
            <div className="reason-chip reason-chip-success">
              Maintain the current replay-backed operating band.
            </div>
          )}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Safe thresholds</strong>
          <span>{autonomy.safe_to_autorun ? "clear" : "held"}</span>
        </div>
        <div className="chip-row">
          {Object.entries(safeThresholds).map(([key, value]) => (
            <span key={key} className="surface-chip">
              {key} {value}
            </span>
          ))}
        </div>
        <div className="stack compact-stack">
          {Object.entries(thresholdChecks).map(([key, passed]) => (
            <div key={key} className={`reason-chip ${passed ? "reason-chip-success" : ""}`}>
              {passed ? "PASS" : "HOLD"}: {key}
            </div>
          ))}
          {autonomy.summary && <div className="reason-chip reason-chip-success">{autonomy.summary}</div>}
          {autonomy.recommended_next_step && <div className="reason-chip">{autonomy.recommended_next_step}</div>}
          {(operationState.watchItems || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
          {(!operationState.watchItems || operationState.watchItems.length === 0) && (
            <div className="reason-chip reason-chip-success">No active watch items</div>
          )}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Mobility signals</strong>
          <span>{operationState.lane}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue label="Demand" value={operationState.demandLabel} tone={operationState.laneTone} />
          <KeyValue label="Supply" value={operationState.driverSupplyLabel} tone={operationState.laneTone} />
          <KeyValue label="Pressure" value={operationState.demandPressure} tone={operationState.laneTone} />
          <KeyValue label="Safety" value={Math.round(operationState.confidence * 100)} tone={operationState.laneTone} />
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Driver auto-allocation</strong>
          <span>{driverAllocation.readiness || "held"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Selected driver"
            value={driverAllocation.selected_driver_id || "none"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Allocation mode"
            value={driverAllocation.mode || "supervised"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Available drivers"
            value={driverAllocation.available_drivers || 0}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Trust score"
            value={driverAllocation.selected_driver_trust_score || 0}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className={`reason-chip ${driverAllocation.enabled ? "reason-chip-success" : ""}`}>
            {driverAllocation.reason || "Autonomous allocation remains read-only until safe thresholds clear."}
          </div>
          {(driverAllocation.candidate_drivers || []).map((driver) => (
            <div key={driver.driver_id} className="reason-chip">
              {driver.driver_id} • trust {driver.trust_score}
            </div>
          ))}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Predictive positioning</strong>
          <span>{driverAllocation.predictive_positioning?.mode || autonomy.mode || "held"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Target zone"
            value={driverAllocation.predictive_positioning?.target_zone || "CBD"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Confidence"
            value={`${Math.round((driverAllocation.predictive_positioning?.confidence || 0) * 100)}%`}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">
            {driverAllocation.predictive_positioning?.instruction || "Predictive positioning remains advisory."}
          </div>
          <div className="reason-chip">
            {driverAllocation.predictive_positioning?.reason || "No predictive positioning recommendation yet."}
          </div>
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>City AI Automation</strong>
          <span>{cityAutomation.mode || "city_held"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Zero-operator"
            value={cityAutomation.zero_operator_mode ? "enabled" : "held"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Coverage"
            value={`${Math.round(cityAutomation.coverage_score || 0)}%`}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Active drivers"
            value={cityAutomation.active_drivers || 0}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Active rides"
            value={cityAutomation.active_rides || 0}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className={`reason-chip ${cityAutomation.zero_operator_mode ? "reason-chip-success" : ""}`}>
            {cityAutomation.instruction || "City-wide automation remains read-only until safe thresholds clear."}
          </div>
          <div className="reason-chip">
            {cityAutomation.reason || "No city automation recommendation yet."}
          </div>
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Multi-City Orchestration</strong>
          <span>{multiCityOrchestration.mode || "global_held"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Cities"
            value={multiCityOrchestration.city_count || 0}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Active cities"
            value={multiCityOrchestration.active_city_count || 0}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Coverage"
            value={`${Math.round(multiCityOrchestration.global_coverage_score || 0)}%`}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Trust"
            value={multiCityOrchestration.global_trust_score || 0}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className={`reason-chip ${multiCityOrchestration.mode === "global_zero_operator" ? "reason-chip-success" : ""}`}>
            {multiCityOrchestration.instruction || "Multi-city orchestration remains read-only until safe thresholds clear."}
          </div>
          <div className="reason-chip">
            {multiCityOrchestration.reason || "No multi-city orchestration recommendation yet."}
          </div>
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Real-time Digital Twin</strong>
          <span>{digitalTwin.mode || "shadow_sync"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Live sync"
            value={`${Math.round(digitalTwin.live_sync_score || 0)}%`}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Twin health"
            value={`${Math.round(digitalTwin.twin_health_score || 0)}%`}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Next state"
            value={digitalTwin.prediction?.next_state || "supervised_shadow"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Loop"
            value={selfImprovingLoop.mode || "watching"}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className={`reason-chip ${digitalTwin.mode === "global_closed_loop" ? "reason-chip-success" : ""}`}>
            {digitalTwin.recommendation || "The digital twin is mirroring live signals in projection-only mode."}
          </div>
          <div className="reason-chip">
            {digitalTwin.reason || "Digital twin reasoning will appear after the first projection cycle."}
          </div>
          <div className="reason-chip reason-chip-success">
            {digitalTwin.live_state
              ? `Live state: ${digitalTwin.live_state.zone} • drivers ${digitalTwin.live_state.active_drivers || 0} • rides ${digitalTwin.live_state.active_rides || 0}`
              : "Live state unavailable"}
          </div>
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Self-improving AI loop</strong>
          <span>{selfImprovingLoop.mode || "watching"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Outcome score"
            value={selfImprovingLoop.outcome_score || 0}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Band"
            value={selfImprovingLoop.band || "hold"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Trend"
            value={selfImprovingLoop.trend?.direction || "stable"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Cycle"
            value={selfImprovingLoop.cycle?.length || 0}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">
            {selfImprovingLoop.measurement_summary || "Learning remains projection-only."}
          </div>
          {(selfImprovingLoop.recommendations || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
          {(selfImprovingLoop.recalibration_notes || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Meta-learning redesign</strong>
          <span>{metaLearningMode}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Review"
            value={metaLearningRedesign?.review?.admitted ? "admitted" : "held"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Authority"
            value={metaLearningRedesign?.authority_boundary || "proposal_only"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Modules"
            value={metaLearningRedesign?.architecture?.modules?.modules?.length || 0}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Tasks"
            value={metaLearningRedesign?.implementation_plan?.tasks?.length || 0}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">
            {metaLearningRedesign?.architecture_change_summary?.join(" ") ||
              "Meta-learning keeps redesign proposal-only and human-reviewed."}
          </div>
          {(operatorMetaLearningRedesign?.redesign_triggers || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
          {(operatorMetaLearningRedesign?.self_redesign_rules || []).map((item) => (
            <div key={item} className="reason-chip">
              {item.replaceAll("_", " ")}
            </div>
          ))}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Business layer pricing + incentives</strong>
          <span>{operatorBusinessPricing?.pricing?.pricing_posture || "balanced"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Multiplier"
            value={operatorBusinessPricing?.pricing?.price_multiplier || 1}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Adjusted price"
            value={`${operatorBusinessPricing?.pricing?.adjusted_price || "0.00"} ${operatorBusinessPricing?.pricing?.currency || ""}`.trim()}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Take rate"
            value={`${Math.round((operatorBusinessPricing?.incentives?.commercial_take_rate || 0) * 100)}%`}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Incentive focus"
            value={operatorBusinessPricing?.incentives?.focus || "neutral"}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">
            {operatorBusinessPricing?.pricing?.explanation ||
              "Pricing remains deterministic and incentives remain bounded."}
          </div>
          <div className="reason-chip">
            {operatorBusinessPricing?.incentives?.driver_message ||
              "Driver incentives remain read-only until the pricing engine projects them."}
          </div>
          <div className="reason-chip">
            {operatorBusinessPricing?.incentives?.rider_message ||
              "Rider transparency will appear once the pricing projection is available."}
          </div>
          {(operatorBusinessPricing?.incentives?.plan || []).map((item) => (
            <div key={item} className="reason-chip">
              {item.replaceAll("_", " ")}
            </div>
          ))}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Autonomous budget allocation + profit optimization</strong>
          <span>{operatorCityProfitOptimization?.budget_allocation?.mode || "supervised"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Budget pool"
            value={`${operatorCityProfitOptimization?.budget_allocation?.budget_pool || "0.00"} ${operatorBusinessPricing?.pricing?.currency || ""}`.trim()}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Projected profit"
            value={`${operatorCityProfitOptimization?.profit_optimization?.projected_profit || "0.00"} ${operatorBusinessPricing?.pricing?.currency || ""}`.trim()}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Profit uplift"
            value={`${operatorCityProfitOptimization?.profit_optimization?.profit_uplift || "0.00"} ${operatorBusinessPricing?.pricing?.currency || ""}`.trim()}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Mode"
            value={operatorCityProfitOptimization?.profit_optimization?.mode || "held"}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">
            {operatorCityProfitOptimization?.profit_optimization?.focus ||
              "Budget allocation remains read-only until the profit model is projected."}
          </div>
          {(operatorCityProfitOptimization?.budget_allocation?.city_allocations || []).map((item) => (
            <div key={item.city} className="reason-chip">
              {item.city}: {item.strategy || "maintain"} · budget {item.recommended_budget || "0.00"} · margin{" "}
              {Math.round((item.projected_margin || 0) * 100)}%
            </div>
          ))}
          {(operatorCityProfitOptimization?.profit_optimization?.optimization_actions || []).map((item) => (
            <div key={item} className="reason-chip">
              {item.replaceAll("_", " ")}
            </div>
          ))}
        </div>
      </article>

      <article className="record-card">
        <div className="record-card-header">
          <strong>Global Learning</strong>
          <span>{multiCityOrchestration.global_learning?.band || "hold"}</span>
        </div>
        <div className="decision-stat-row">
          <KeyValue
            label="Outcome band"
            value={multiCityOrchestration.global_learning?.outcome_band || "guarded"}
            tone={operationState.laneTone}
          />
          <KeyValue
            label="Outcome score"
            value={multiCityOrchestration.global_learning?.outcome_score || 0}
            tone={operationState.laneTone}
          />
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip reason-chip-success">
            {multiCityOrchestration.global_learning?.measurement_summary || "Global learning remains projection-only."}
          </div>
          {(multiCityOrchestration.global_learning?.recommendations || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
          {(multiCityOrchestration.global_learning?.watch_items || []).map((item) => (
            <div key={item} className="reason-chip">
              {item}
            </div>
          ))}
          {selfImprovingLoop.measurement_summary && (
            <div className="reason-chip reason-chip-success">{selfImprovingLoop.measurement_summary}</div>
          )}
        </div>
      </article>
    </div>
  );
}

function DecisionGuidancePanel({ decision }) {
  if (!decision) {
    return <EmptyState label="Decision guidance appears after the engine records the first snapshot." />;
  }

  const metrics = [
    { label: "Trust health", value: decision.trustHealth || 0 },
    { label: "Replay health", value: decision.replayHealthScore || 0 },
    { label: "Evidence coverage", value: `${decision.evidenceCoverage || 0}%` },
    { label: "Exception pressure", value: decision.exceptionPressure || 0 },
    { label: "Alert count", value: decision.alertCount || 0 },
    { label: "Guard count", value: decision.guardCount || 0 },
    { label: "Replay failures", value: decision.replayFailures || 0 },
    { label: "Missing traces", value: decision.missingTraces || 0 },
  ];

  return (
    <div className="stack">
      <article className="record-card">
        <div className="decision-key-grid">
          {metrics.map((metric) => (
            <KeyValue key={metric.label} label={metric.label} value={metric.value} />
          ))}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Recommended actions</strong>
          <span>{decision.decisionLane || "observe"}</span>
        </div>
        <div className="stack compact-stack">
          {(decision.recommendedActions || []).map((action) => (
            <div key={action} className="reason-chip reason-chip-success">
              {action}
            </div>
          ))}
          {(!decision.recommendedActions || decision.recommendedActions.length === 0) && (
            <div className="reason-chip reason-chip-success">
              Keep the current replay-backed operating band.
            </div>
          )}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Watch items</strong>
          <span>{(decision.watchItems || []).length}</span>
        </div>
        <div className="chip-row">
          {(decision.watchItems || []).map((item) => (
            <span key={item} className="surface-chip">
              {item}
            </span>
          ))}
          {(!decision.watchItems || decision.watchItems.length === 0) && (
            <span className="surface-chip">No active watch items</span>
          )}
        </div>
      </article>
    </div>
  );
}

function DecisionHistoryFeed({ history, sourceBreakdown }) {
  if (!history || history.length === 0) {
    return <EmptyState label="No persistent decision history yet. The decision engine will seed on the next operator dashboard run." />;
  }

  const recentHistory = history.slice(-8).reverse();

  return (
    <div className="stack">
      <div className="chip-row">
        {Object.entries(sourceBreakdown || {}).map(([source, count]) => (
          <span key={source} className="surface-chip">
            {source}: {count}
          </span>
        ))}
      </div>
      {recentHistory.map((snapshot) => (
        <article
          key={snapshot.decisionId}
          className={`record-card decision-history-card decision-${snapshot.decisionLane || "observe"}`}
        >
          <div className="record-card-header">
            <strong>
              {snapshot.createdAt
                ? new Date(snapshot.createdAt).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })
                : snapshot.windowBucket || "live"}
            </strong>
            <span>{snapshot.decisionPriority || "low"}</span>
          </div>
          <p>{snapshot.decisionSummary}</p>
          <div className="chip-row">
            <span className="surface-chip">{snapshot.decisionLane}</span>
            <span className="surface-chip">{snapshot.decisionAction}</span>
            <span className="surface-chip">Stability {snapshot.stabilityIndex}</span>
            <span className="surface-chip">Risk {snapshot.riskLevel}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function actionLaneTone(lane) {
  if (lane === "safeguard") {
    return "critical";
  }
  if (lane === "prepare") {
    return "warning";
  }
  if (lane === "notify") {
    return "neutral";
  }
  return "success";
}

function ActionSummaryPanel({ action, latest }) {
  if (!action) {
    return <EmptyState label="No action snapshots are available yet. The controlled autonomous action engine seeds one automatically." />;
  }

  const actionTone = actionLaneTone(action.actionLane);
  const decisionQuality = action.decisionQuality || {};
  const decision = action.decision || {};
  const calibrationReasoning = action.reasoning?.calibration || {};

  return (
    <div className="stack">
      <article className={`record-card action-card action-${action.actionLane || "monitor"}`}>
        <div className="record-card-header">
          <div>
            <strong>{action.actionLane || "monitor"}</strong>
            <span className="action-action-label">
              {action.actionMode || "guided_control"}
            </span>
          </div>
          <span>{action.actionPriority || "low"}</span>
        </div>
        <p>{action.actionSummary || "Decision quality calibration is awaiting the first persisted action window."}</p>
        <div className="action-stat-row">
          <KeyValue label="Quality" value={`${action.decisionQualityScore || 0}/100`} tone={actionTone} />
          <KeyValue
            label="Confidence"
            value={`${Math.round((action.calibratedConfidence || 0) * 100)}%`}
            tone={actionTone}
          />
          <KeyValue
            label="Gate"
            value={action.safetyGate || "pass"}
            tone={action.safetyGate === "hold" ? "warning" : "neutral"}
          />
          <KeyValue
            label="Execution tier"
            value={action.executionTier || "advisory"}
            tone={action.executionTierReady ? "success" : action.executionTier === "controlled" ? "warning" : "neutral"}
          />
          <KeyValue label="Latest record" value={latest?.actionId || action.actionId || "pending"} />
        </div>
        <div className="chip-row">
          <span className="surface-chip">{action.advisoryOnly ? "Advisory only" : "Execution ready"}</span>
          <span className="surface-chip">{action.readOnly ? "Read only" : "Writable"}</span>
          <span className="surface-chip">{action.projectionOnly ? "Projection only" : "Authority"}</span>
          <span className="surface-chip">{action.controlSignal || "maintain_monitoring"}</span>
          <span className="surface-chip">{action.executionTier || "advisory"}</span>
        </div>
        {action.executionTierSummary && (
          <div className="reason-chip reason-chip-success">{action.executionTierSummary}</div>
        )}
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Calibration rationale</strong>
          <span>{action.qualityBand || "unknown"}</span>
        </div>
        <div className="stack compact-stack">
          <div className="reason-chip">
            Decision lane: {action.decisionLane || "observe"} / {action.decisionPriority || "low"}
          </div>
          <div className="reason-chip">
            Calibration score: {action.decisionQualityScore || 0}/100
          </div>
          <div className="reason-chip">
            Evidence alignment: {action.evidenceAlignmentScore || 0}
          </div>
          <div className="reason-chip">
            History alignment: {action.historyAlignmentScore || 0}
          </div>
          {calibrationReasoning.quality_band && (
            <div className="reason-chip">
              Calibration band: {calibrationReasoning.quality_band}
            </div>
          )}
          {calibrationReasoning.safety_gate && (
            <div className="reason-chip">
              Safety gate: {calibrationReasoning.safety_gate}
            </div>
          )}
          {calibrationReasoning.execution_tier && (
            <div className="reason-chip">
              Execution tier: {calibrationReasoning.execution_tier}
            </div>
          )}
          {decisionQuality.summary && <div className="reason-chip">{decisionQuality.summary}</div>}
          {decision.decisionSummary && <div className="reason-chip">{decision.decisionSummary}</div>}
          {(!decisionQuality.summary && !decision.decisionSummary) && (
            <div className="reason-chip reason-chip-success">
              Awaiting more persistent evidence to refine the calibration trail.
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

function ActionGuidancePanel({ action }) {
  if (!action) {
    return <EmptyState label="Action guidance appears after the engine records the first calibrated snapshot." />;
  }

  const metrics = [
    { label: "Trust health", value: action.trustHealth || 0 },
    { label: "Replay health", value: action.replayHealthScore || 0 },
    { label: "Evidence coverage", value: `${action.evidenceCoverage || 0}%` },
    { label: "Exception pressure", value: action.exceptionPressure || 0 },
    { label: "Guard count", value: action.guardCount || 0 },
    { label: "Decision quality", value: action.decisionQualityScore || 0 },
    { label: "Calibrated confidence", value: `${Math.round((action.calibratedConfidence || 0) * 100)}%` },
    { label: "Execution tier", value: action.executionTier || "advisory" },
    { label: "Automation tier", value: action.automationTier || 0 },
  ];

  return (
    <div className="stack">
      <article className="record-card">
        <div className="action-key-grid">
          {metrics.map((metric) => (
            <KeyValue key={metric.label} label={metric.label} value={metric.value} />
          ))}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Recommended control actions</strong>
          <span>{action.actionLane || "monitor"}</span>
        </div>
        <div className="stack compact-stack">
          {(action.controlActions || []).map((controlAction) => (
            <div key={controlAction} className="reason-chip reason-chip-success">
              {controlAction}
            </div>
          ))}
          {(action.executionTierControls || []).map((control) => (
            <div key={control} className="reason-chip">
              {control}
            </div>
          ))}
          {action.executionTierReady && (
            <div className="reason-chip reason-chip-success">
              Controlled execution tier is ready for operator-supervised limited automation proposals.
            </div>
          )}
          {(!action.controlActions || action.controlActions.length === 0) && (
            <div className="reason-chip reason-chip-success">
              Maintain the current replay-backed operating band.
            </div>
          )}
        </div>
      </article>
      <article className="record-card">
        <div className="record-card-header">
          <strong>Watch items</strong>
          <span>{(action.watchItems || []).length}</span>
        </div>
        <div className="chip-row">
          {(action.watchItems || []).map((item) => (
            <span key={item} className="surface-chip">
              {item}
            </span>
          ))}
          {(!action.watchItems || action.watchItems.length === 0) && (
            <span className="surface-chip">No active watch items</span>
          )}
        </div>
      </article>
    </div>
  );
}

function ActionHistoryFeed({ history, sourceBreakdown }) {
  if (!history || history.length === 0) {
    return <EmptyState label="No persistent action history yet. The action engine will seed on the next dashboard run." />;
  }

  const recentHistory = history.slice(-8).reverse();

  return (
    <div className="stack">
      <div className="chip-row">
        {Object.entries(sourceBreakdown || {}).map(([source, count]) => (
          <span key={source} className="surface-chip">
            {source}: {count}
          </span>
        ))}
      </div>
      {recentHistory.map((snapshot) => (
        <article
          key={snapshot.actionId}
          className={`record-card action-history-card action-${snapshot.actionLane || "monitor"}`}
        >
          <div className="record-card-header">
            <strong>
              {snapshot.createdAt
                ? new Date(snapshot.createdAt).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })
                : snapshot.windowBucket || "live"}
            </strong>
            <span>{snapshot.actionPriority || "low"}</span>
          </div>
          <p>{snapshot.actionSummary}</p>
          <div className="chip-row">
            <span className="surface-chip">{snapshot.actionLane}</span>
            <span className="surface-chip">{snapshot.actionMode}</span>
            <span className="surface-chip">Quality {snapshot.decisionQualityScore}</span>
            <span className="surface-chip">Confidence {Math.round((snapshot.calibratedConfidence || 0) * 100)}%</span>
            <span className="surface-chip">Gate {snapshot.safetyGate}</span>
            <span className="surface-chip">Tier {snapshot.executionTier || "advisory"}</span>
          </div>
        </article>
      ))}
    </div>
  );
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
