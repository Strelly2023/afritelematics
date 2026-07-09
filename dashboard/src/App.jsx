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
  novatechPartnerGovernance: null,
  novapayLiveTestReadiness: null,
  novapayTreasuryIntelligence: null,
  novapayGlobalTreasuryIntelligence: null,
  novarideDaoEconomy: null,
  novarideAppStore: null,
  novarideProtocolMarketplace: null,
  novarideSuperApp: null,
  novaidIdentity: null,
  novaidGenSovereign: null,
  novaidDigitalNation: null,
  novarideDigitalConstitution: null,
  novarideRegulatoryAlignment: null,
  novarideGlobalExpansion: null,
  novarideEcosystem: null,
  novaridePlatformArchitectureContract: null,
  architectureCompliance: null,
  architectureRemediation: null,
  architectureLearning: null,
  architecturePredictive: null,
  architectureAutonomous: null,
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

const ARCHITECTURE_COMPLIANCE_FALLBACK = {
  classification: "NOVARIDE_ARCHITECTURE_COMPLIANCE_REPORT",
  status: "pending",
  score: 0,
  mode: "dashboard_fallback",
  rules_total: 5,
  rules_passed: 0,
  rules_failed: 5,
  report: [
    { name: "Architecture Invariants", passed: false, issues: ["Waiting for validator report"] },
    { name: "Multi-Language AST Validation", passed: false, issues: ["Waiting for validator report"] },
    { name: "Semantic OpenAPI Diff", passed: false, issues: ["Waiting for validator report"] },
    { name: "Blockchain Proof Verification", passed: false, issues: ["Waiting for validator report"] },
    { name: "Replay Integrity", passed: false, issues: ["Waiting for validator report"] },
  ],
  capabilities: [
    "multi_language_ast_validation",
    "semantic_openapi_diff",
    "architecture_anchor_v2_verification",
    "replay_integrity",
    "ci_report_artifact",
  ],
};

const ARCHITECTURE_REMEDIATION_FALLBACK = {
  classification: "NOVARIDE_AUTONOMOUS_REMEDIATION_REPORT",
  mode: "plan",
  initial_passed: false,
  final_passed: false,
  fixes_total: 0,
  manual_review_required: 0,
  fixes: [],
  executions: [],
  source: "dashboard_fallback",
};

const ARCHITECTURE_LEARNING_FALLBACK = {
  classification: "NOVARIDE_CONTINUOUS_LEARNING_REPORT",
  mode: "plan",
  source: "dashboard_fallback",
  risk_profile: {
    risk: "unknown",
    score: 0,
    total: 0,
    success: 0,
    fail: 0,
  },
  patterns: {},
  knowledge_graph: {},
  optimizer_suggestions: [],
  learning_memory_path: "architecture_learning_memory.json",
  remediation: ARCHITECTURE_REMEDIATION_FALLBACK,
};

const ARCHITECTURE_PREDICTIVE_FALLBACK = {
  classification: "NOVARIDE_PREDICTIVE_GOVERNANCE_REPORT",
  mode: "configured_control",
  source: "dashboard_fallback",
  authority_boundary: "predictive_governance_is_advisory_and_simulation_only",
  digital_twin: {
    state: {},
    scenario_count: 0,
    twin_health_score: 0,
    mirrored_components: [],
  },
  scenarios: [],
  predictions: [],
  preventive_actions: [],
  predicted_risks: 0,
  prevented_violations: 0,
  risk_score: 0,
  metrics: {
    predicted_risks: 0,
    prevented_violations: 0,
    scenario_count: 0,
    twin_health_score: 0,
  },
  compliance: ARCHITECTURE_COMPLIANCE_FALLBACK,
  remediation: ARCHITECTURE_REMEDIATION_FALLBACK,
  learning: ARCHITECTURE_LEARNING_FALLBACK,
};

const ARCHITECTURE_AUTONOMOUS_FALLBACK = {
  classification: "NOVARIDE_AUTONOMOUS_MULTI_AGENT_GOVERNANCE_REPORT",
  mode: "configured_control",
  source: "dashboard_fallback",
  authority_boundary: "multi_agent_governance_is_advisory_and_simulation_only",
  digital_twin: ARCHITECTURE_PREDICTIVE_FALLBACK.digital_twin,
  multi_agent: {
    findings: [],
    agent_count: 0,
    severity_breakdown: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    },
  },
  crisis: [],
  crisis_summary: {
    max_risk_score: 0,
    critical_scenarios: [],
    scenario_count: 0,
    black_swan: {
      event: "GLOBAL_PAYMENT_FAILURE",
      impact: "CRITICAL",
      requires: "manual_intervention",
      authority_boundary: "simulation_only",
    },
  },
  economic_optimization: {
    action: "hold",
    decision: { action: "hold", method: "monitor", reason: "Metrics remain within tolerance." },
    actions: [],
    cost_efficiency: 100,
    authority_boundary: "advisory_only",
  },
  refactor_suggestions: [],
  metrics: {
    predicted_risks: 0,
    prevented_violations: 0,
    multi_agent_findings: 0,
    critical_crisis_scenarios: 0,
    economic_efficiency: 100,
    refactor_suggestions_total: 0,
    twin_health_score: 0,
  },
  predictive: ARCHITECTURE_PREDICTIVE_FALLBACK,
};

const NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK = {
  classification: "NOVAPAY_TREASURY_AI_REPORT",
  authority_boundary: "advisory_only_and_policy_gated",
  risk_level: "LOW",
  cash_balance: "0.00",
  reserved_balance: "0.00",
  settlement_obligations: "0.00",
  prefunding_gap: "0.00",
  coverage_ratio: "99.99",
  settlement_pressure: "0.00",
  reserve_headroom: "0.00",
  decision: {
    action: "maintain_buffer",
    method: "keep_current_treasury_policy",
    reason: "Treasury intelligence is unavailable.",
    priority: "low",
  },
  recommendations: [],
  stress_tests: [],
  provider_snapshot: [],
};

const NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK = {
  classification: "NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_REPORT",
  authority_boundary: "advisory_only_and_policy_gated",
  core: NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK,
  multi_currency: {
    base_currency: "USD",
    currency_totals: {},
    currency_distribution: [],
    fx_exposure: "0.00",
    stablecoin_ratio: "0.00",
    stablecoin_target: {
      currency: "STABLE_RESERVE_USD",
      amount: "0.00",
      strategy: "reserve_to_stablecoin",
    },
    hedge_actions: ["hold_position"],
    action: "hold_position",
  },
  onchain: {
    batch_strategy: "anchorBatchV2",
    verification_mode: "advisory_only",
    snapshot_root: "",
    anchor_batch_plan: [],
    batch_size: 0,
    onchain_coverage: "0.00",
    ledger_anchor_context: "TREASURY_SNAPSHOT",
  },
  recommendations: [],
  metrics: {
    currency_count: 0,
    fx_exposure: "0.00",
    stablecoin_ratio: "0.00",
    onchain_coverage: "0.00",
    anchor_count: 0,
  },
};

const NOVARIDE_DAO_ECONOMY_FALLBACK = {
  classification: "NOVARIDE_DAO_TOKEN_ECONOMY_REPORT",
  authority_boundary: "advisory_only_and_policy_gated",
  token_economy: {
    symbol: "NVT",
    name: "NovaToken",
    utility: ["governance", "rewards", "incentives", "ecosystem staking"],
    total_supply: "10000000.00",
    circulating_supply: "6000000.00",
    staked_supply: "1800000.00",
    community_pool: "1200000.00",
    rewards_distributed: "1200000.00",
    treasury_allocation: "0.00",
    driver_incentive_pool: "0.00",
    rider_reward_pool: "0.00",
    partner_incentive_pool: "0.00",
    governance_reserve: "0.00",
    reward_actions: ["hold_reward_policy"],
  },
  governance: {
    active_proposals: 0,
    total_votes: 0,
    participation_rate: "0.00",
    governance_score: "0.00",
    voting_model: "token_weighted_proposal_governance",
    proposal_queue: [],
  },
  treasury: {
    treasury_balance: "0.00",
    treasury_reserve: "0.00",
    allocatable_budget: "0.00",
    allocation_plan: [],
  },
  onchain: {
    authority_boundary: "advisory_only_and_policy_gated",
    proposal_batch_plan: [],
    treasury_batch_plan: [],
    batch_size: 0,
    verification_mode: "advisory_only",
  },
  metrics: {
    token_supply: "10000000.00",
    circulating_supply: "6000000.00",
    active_proposals: 0,
    governance_score: "0.00",
    participation_rate: "0.00",
    treasury_balance: "0.00",
  },
  recommendations: [],
};

const NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK = {
  view: "novaride_developer_marketplace",
  status: "governed_beta",
  platform: "NovaRide",
  marketplace: {
    platform: "NovaRide",
    protocol_version: "2026.07.0",
    classification: "governed_protocol_marketplace_catalog",
    status: "governed_beta",
    storefronts: [
      {
        key: "app_store",
        name: "NovaRide App Store",
        audience: "customers, drivers, operators, partners",
        status: "catalog_ready",
        purpose: "Publish governed NovaRide experiences and partner-built apps.",
        listing_types: ["first_party_app", "partner_app", "trusted_integration"],
      },
      {
        key: "developer_marketplace",
        name: "NovaRide Developer Marketplace",
        audience: "developers, integrators, startups",
        status: "sandbox_ready",
        purpose: "Publish SDKs, webhooks, sample apps, and integration packages.",
        listing_types: ["sdk", "webhook", "sample_app", "integration"],
      },
    ],
    catalog: [],
    publishing_pipeline: [],
    developer_program: {
      api_keys: true,
      sandbox: "required",
      webhooks: true,
      documentation: true,
      sdk_registry: true,
      trust_review: "required",
      compatibility_review: "required",
      usage_analytics: true,
    },
    governance: {
      authority: "NovaPower",
      verification: "NovaTrust",
      execution: "backend_only",
      policy_gates: [
        "authentication",
        "rbac",
        "signature_verification",
        "replay_validation",
        "compatibility_check",
      ],
    },
    economics: {
      revenue_share_model: "policy_gated",
      listing_fee: "optional",
      developer_rewards: "usage_based",
      treasury_split: ["developer", "platform", "reserve"],
    },
    metrics: {
      storefront_count: 1,
      catalog_count: 0,
      publishing_step_count: 0,
    },
  },
};

const NOVARIDE_APP_STORE_FALLBACK = {
  view: "novaride_app_store",
  status: "governed_beta",
  platform: "NovaRide",
  app_store: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "governed_app_store_catalog",
    status: "governed_beta",
    categories: [
      { key: "mobility", name: "Mobility", examples: ["ride apps", "taxi services", "dispatch extensions"] },
    ],
    apps: [],
    publishing_pipeline: [],
    developer_flow: [
      "sign_up",
      "get_api_key",
      "build_app",
      "test_in_sandbox",
      "publish_to_app_store",
      "earn_revenue",
    ],
    governance: {
      authority: "NovaPower",
      verification: "NovaTrust",
      execution: "backend_only",
      policy_gates: [
        "authentication",
        "rbac",
        "security_scan",
        "contract_validation",
        "sandbox_test",
        "policy_approval",
      ],
    },
    monetization: {
      revenue_streams: ["app_sales", "subscriptions", "transaction_fee", "api_usage", "token_economy"],
      revenue_split: { developer: "70%", platform: "30%" },
      token_payment: "NVT_supported",
    },
    metrics: {
      app_count: 0,
      developer_count: 0,
      city_count: 0,
      new_apps_per_week: 0,
      user_installs_growth: "0%",
    },
  },
};

const NOVARIDE_SUPER_APP_FALLBACK = {
  view: "novaride_super_app",
  status: "contract_ready",
  platform: "NovaRide",
  super_app: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "global_super_app_operating_system_contract",
    status: "contract_ready",
    purpose: "Global digital operating system for mobility, finance, identity, apps, and governance.",
    authority_boundary: "super_app_is_interface_only_backend_services_keep_authority",
    modules: [
      { key: "mobility", name: "Mobility", route: "/super-app/mobility", authority: "NovaRide Core", capabilities: ["book_ride", "schedule_ride", "driver_verification"] },
      { key: "delivery", name: "Delivery", route: "/super-app/delivery", authority: "NovaRide Core", capabilities: ["parcel_delivery", "proof_tracking", "courier_identity"] },
      { key: "wallet", name: "Wallet / NovaPay", route: "/super-app/wallet", authority: "NovaPay", capabilities: ["multi_currency_wallet", "send_money", "token_balance"] },
      { key: "finance", name: "Finance", route: "/super-app/finance", authority: "NovaPay", capabilities: ["loans", "treasury_access", "staking"] },
      { key: "app_store", name: "App Store", route: "/super-app/app-store", authority: "NovaPower", capabilities: ["install_app", "launch_partner_app", "permission_review"] },
      { key: "identity", name: "Identity / NovaID", route: "/super-app/identity", authority: "NovaID", capabilities: ["login_with_novaid", "privacy_controls", "device_security"] },
      { key: "ai_assistant", name: "AI Assistant / NovaAI", route: "/super-app/assistant", authority: "advisory_only", capabilities: ["ride_recommendations", "spending_insights", "governance_prompts"] },
    ],
    profile: {
      novaid: "NOVA-84729",
      wallet_balance_usd: 850,
      token_balance: "2,400 NVT",
      trust_score: "92%",
      activity: { rides: 120, deliveries: 15 },
    },
    wallet: {
      balances: { USD: "500.00", KES: "20000.00", USDC: "200.00", NVT: "1500.00" },
      authority: "NovaPay",
    },
    governance: {
      can_vote: true,
      active_proposals: 42,
      staking: "NVT_supported",
      authority: "DAO_policy_gated",
    },
    ai_assistant: {
      authority_boundary: "NovaAI_recommendations_are_advisory_only",
      recommendations: ["Take a ride now: high demand nearby", "Earn extra today as driver", "Vote on proposal #42"],
    },
    ecosystem_loop: ["users", "super_app_activity", "payments_and_tokens", "treasury", "dao_governance", "platform_evolution", "developer_build", "ecosystem_growth"],
    metrics: {
      users: "2.5M",
      apps: 7200,
      transactions_per_day: "$5M",
      token_circulation: "growing",
    },
  },
};

const NOVAID_IDENTITY_FALLBACK = {
  view: "novaid_global_identity",
  status: "standard_ready",
  platform: "NovaRide",
  identity: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "global_identity_layer_contract",
    status: "standard_ready",
    positioning: "Login with NovaID",
    authority_boundary: "NovaID_owns_identity_authentication_reputation_device_and_governance_identity",
    capabilities: [
      { key: "identity", name: "Universal identity", capability: "Cross-app account identity with DID-ready identifiers." },
      { key: "authentication", name: "Secure authentication", capability: "Login with NovaID for NovaRide and partner applications." },
      { key: "reputation", name: "Reputation", capability: "Trust score, ride history, delivery activity, and verification state." },
      { key: "wallet_linkage", name: "Wallet linkage", capability: "NovaPay wallet binding for financial identity and settlements." },
      { key: "device_identity", name: "Device identity", capability: "Device binding, session risk checks, and replay-aware security." },
      { key: "governance", name: "Governance rights", capability: "DAO voting, proposal participation, and token-weighted access." },
    ],
    verification: {
      cryptographic_verification: true,
      onchain_proofs: true,
      cross_app_identity: true,
      privacy_control: true,
      replay_auditing: true,
    },
    sample_profile: {
      id: "NOVA-84729",
      did: "did:nova:84729",
      wallet: "novapay_wallet_84729",
      trust_score: 92,
      reputation: ["120_rides", "15_deliveries", "wallet_verified"],
    },
    login_button: {
      label: "Login with NovaID",
      contract: "novaride.identity.login.v1",
      policy_gates: ["credential_verification", "device_binding", "privacy_consent", "replay_receipt"],
    },
    use_cases: ["login_across_apps", "driver_verification", "payments_identity", "governance_voting", "reputation_scoring"],
    metrics: {
      identity_profiles: 2500000,
      wallet_link_rate: "92%",
      verified_devices: 1800000,
      cross_app_sessions: 7200,
    },
  },
};

const NOVAID_GEN_SOVEREIGN_FALLBACK = {
  view: "novaid_gen_sovereign",
  status: "architecture_contract_ready",
  platform: "NovaRide",
  gen_sovereign: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "novaid_gen_sovereign_infrastructure_contract",
    status: "architecture_contract_ready",
    positioning: "Sovereign digital identity and global crypto-financial infrastructure",
    authority_boundary: "gen_sovereign_is_architecture_and_policy_gated_infrastructure_not_live_state_authority",
    core_layers: [
      { key: "sovereign_identity", name: "NovaID SSI", role: "Self-sovereign identity, DID documents, and verifiable credentials.", authority: "NovaID" },
      { key: "crypto_finance", name: "NovaToken / Crypto Layer", role: "NVT, stablecoin support, CBDC adapters, and on-chain treasury plans.", authority: "NovaPay_policy_gated" },
      { key: "governance", name: "NovaDAO", role: "Token, reputation, and activity-weighted proposal governance.", authority: "DAO_policy_gated" },
      { key: "verification", name: "NovaTrust", role: "Credential, payment, replay, and on-chain audit verification.", authority: "NovaTrust" },
      { key: "decision_intelligence", name: "NovaAI", role: "Proposal analysis, manipulation detection, and outcome simulation.", authority: "advisory_only" },
      { key: "federation", name: "Open Protocol Ecosystem", role: "Federated identity, payments, trust, app, bank, and government integrations.", authority: "federation_policy_gated" },
    ],
    identity: {
      model: "self_sovereign_identity",
      did_method: "did:nova",
      credential_standard: "verifiable_credentials",
      sample_did_document: { id: "did:nova:847392", publicKey: "0xABC...", credentials: ["KYC_verified", "Driver_licensed"] },
      auth_flow: ["user_signs_with_private_key", "network_verifies_signature", "policy_checks_credentials", "access_granted_with_replay_receipt"],
    },
    government_integration: {
      status: "credential_adapter_contract",
      credential_types: ["national_id_verification", "driver_license", "tax_identity", "public_transport_access"],
      authority_boundary: "governments_remain_credential_issuers_novaid_verifies_and_binds_claims",
    },
    crypto_finance: {
      components: ["NovaToken_NVT", "stablecoins", "optional_CBDC_adapters", "onchain_treasury_contracts"],
      payment_stack: ["wallet", "crypto_or_fiat", "novapay", "settlement", "onchain_verification"],
      metrics: { token_circulation: "50M NVT", daily_transactions: "$20M", treasury: "$10M" },
    },
    federation: {
      apis: [
        { path: "/v1/federation/identity", purpose: "Verify DID, credential, and identity assertions across trusted peers." },
        { path: "/v1/federation/payments", purpose: "Route fiat, stablecoin, token, CBDC, and settlement proofs through NovaPay." },
        { path: "/v1/federation/trust", purpose: "Exchange NovaTrust verification packets, receipts, and replay anchors." },
      ],
    },
    ai_governance: {
      model: "tokens_reputation_activity_weighted",
      formula: { tokens: 0.5, reputation: 0.3, activity: 0.2 },
      sample_analysis: { proposal: "Expand to Kigali", roi: "24%", risk: "LOW", recommendation: "APPROVE" },
      authority_boundary: "NovaAI_recommends_only_DAO_and_policy_execute",
    },
    dashboard: {
      identity: { novaids: "10M+", verified: "95%", active: "growing" },
      economy: { token_circulation: "50M NVT", daily_transactions: "$20M", treasury: "$10M" },
      governance: { proposals: 120, participation: "70%", ai_assisted_decisions: true },
    },
    capabilities: ["sovereign_identity", "global_crypto_finance", "dao_governance", "ai_assisted_decisions", "cross_platform_federation", "token_economy", "open_protocol", "super_app"],
  },
};

const NOVAID_DIGITAL_NATION_FALLBACK = {
  view: "novaid_digital_nation",
  status: "architecture_contract_ready",
  platform: "NovaRide",
  digital_nation: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "novaid_gen_sovereign_plus_plus_digital_nation_contract",
    status: "architecture_contract_ready",
    positioning: "Digital Citizenship + NovaID Passport System",
    authority_boundary: "digital_nation_is_platform_citizenship_not_legal_nationality_or_immigration_authority",
    what_this_is: ["platform_level_citizenship", "digital_identity_system", "economic_ecosystem", "governance_participation_layer"],
    what_this_is_not: ["government_issued_citizenship", "legal_passport", "immigration_authority", "state_sovereignty_claim"],
    core_layers: [
      { key: "digital_citizenship", name: "NovaID Digital Citizenship", role: "Platform citizenship, wallet linkage, reputation, activity, and governance eligibility.", authority: "NovaID_policy_gated" },
      { key: "novapassport", name: "NovaPassport", role: "Cross-platform access, service eligibility, trusted credential storage, and mobility access.", authority: "NovaTrust_credential_gated" },
      { key: "token_economy", name: "NovaToken Economy", role: "Rewards, contribution incentives, staking, treasury participation, and governance weight.", authority: "NovaDAO_policy_gated" },
      { key: "financial_system", name: "NovaPay Financial System", role: "Wallets, payments, settlement proofs, and economic identity.", authority: "NovaPay_compliance_gated" },
      { key: "global_protocol", name: "Global Protocol Layer", role: "Federation with apps, financial networks, and credential issuers.", authority: "federation_policy_gated" },
    ],
    citizenship: {
      name: "NovaCitizens",
      purpose: "Digital citizens with identity, wallet, reputation, activity, and governance rights.",
      profile: {
        nova_id: "did:nova:00087423",
        citizenship_status: "verified",
        wallet: "0xABC123",
        trust_score: 94,
        reputation: "high",
        roles: ["rider", "developer"],
        governance_power: 2450,
      },
      tiers: [
        { tier: "Basic", access: "Identity + wallet" },
        { tier: "Verified", access: "Full platform access" },
        { tier: "Trusted", access: "Governance power" },
        { tier: "Elite", access: "Ecosystem influence" },
      ],
    },
    passport: {
      name: "NovaPassport",
      authority_boundary: "novapassport_is_platform_access_not_a_legal_travel_document",
      sample: {
        passport_id: "NVP-992384",
        holder: "did:nova:00087423",
        credentials: ["KYC_verified", "licensed_driver", "trusted_user"],
        validity: "global",
        signature: "cryptographic_proof",
      },
      capabilities: ["cross_platform_access", "cross_border_identity_verification", "service_eligibility", "trusted_credential_storage", "platform_level_mobility_rights"],
    },
    ssi: {
      model: "self_sovereign_identity",
      auth_flow: ["user_signs_challenge", "public_key_verifies_signature", "policy_checks_credentials", "access_granted_with_replay_receipt"],
    },
    governance: {
      formula: { tokens: 0.5, trust_score: 0.3, activity: 0.2 },
      proposal_types: ["economic_policy", "app_store_rules", "treasury_allocation", "platform_upgrades"],
      dashboard: { active_voters: "2.5M", participation: "72%", ai_assisted_decisions: true },
    },
    ai_governance: {
      sample_analysis: { proposal: "Increase driver incentives", impact: "Positive", cost: "Moderate", recommendation: "APPROVE" },
      authority_boundary: "NovaAI_recommends_only_citizens_and_DAO_execute",
    },
    dashboard: {
      identity: { novacitizens: "12M", verified: "95%", trusted: "60%" },
      economy: { token_supply: "100M NVT", daily_transactions: "$25M", treasury: "$15M" },
      governance: { active_voters: "2.5M", participation: "72%", ai_assisted_decisions: true },
    },
    capabilities: ["digital_citizenship", "passport_system", "global_identity_layer", "token_economy", "dao_governance", "ai_assisted_decisions", "cross_platform_federation", "financial_infrastructure"],
  },
};

const NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK = {
  view: "novaride_digital_constitution",
  status: "architecture_contract_ready",
  platform: "NovaRide",
  constitution: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "novaride_digital_constitution_governance_contract",
    status: "architecture_contract_ready",
    positioning: "Digital Constitution + Legal Governance Framework",
    authority_boundary: "digital_constitution_is_platform_governance_not_statutory_law_or_regulator_substitute",
    core_statement:
      "NovaRide shall operate as a governed digital system in which identity is sovereign, authority is bounded, rules are enforceable, actions are auditable, and governance is participatory.",
    articles: [
      { article: "I", title: "Sovereign Identity", principle: "All participants possess a NovaID representing citizenship, access, economy, and governance." },
      { article: "II", title: "Digital Citizenship", principle: "A NovaCitizen is any NovaID holder with verified participation in the ecosystem." },
      { article: "III", title: "Rights of Users", principle: "Every NovaCitizen receives identity, finance, governance, transparency, and record rights." },
    ],
    authority_structure: {
      fundamental_rule: "execution_authority_shall_remain_with_NovaPower_and_authorized_subsystems_only",
      authorities: [
        { authority: "NovaPower", role: "Execution authority" },
        { authority: "NovaRide Core", role: "Operational truth" },
        { authority: "NovaPay", role: "Financial authority" },
        { authority: "NovaTrust", role: "Verification authority" },
        { authority: "DAO", role: "Governance authority" },
      ],
    },
    governance: {
      legislative_layer: "NovaDAO",
      powers: ["change_protocol_rules", "define_economic_policies", "approve_treasury_allocations", "govern_ecosystem_evolution"],
      voting_model: ["token_holdings", "trust_score", "participation_level"],
      ai_role: {
        shall_provide: ["recommendations", "predictive_analysis", "fraud_detection"],
        shall_not: ["directly_vote", "supersede_governance", "execute_authority"],
      },
    },
    economic_constitution: {
      principles: ["economy_shall_be_token_driven", "value_creation_shall_be_rewarded", "treasury_shall_be_governed_transparently", "financial_actions_shall_be_auditable"],
      treasury_rules: ["funds_shall_be_verifiable", "allocations_shall_require_governance_approval", "transactions_shall_be_replayable"],
    },
    trust_verification_law: {
      truth_model: ["replay_shall_be_source_of_operational_truth", "novatrust_shall_validate_all_critical_actions", "cryptographic_proof_shall_be_required_for_verification"],
      legal_equivalent: "replay_is_digital_audit_record",
    },
    contract_law: {
      rule: "all_system_behavior_shall_be_governed_by_contracts",
      types: ["api_contracts", "smart_contracts", "governance_rules", "identity_credentials"],
      enforcement: ["contracts_shall_be_versioned", "contracts_shall_be_test_validated", "violations_shall_be_rejected_automatically"],
    },
    ai_governance_law: {
      required_behavior: ["explain_decisions", "provide_confidence_scores", "identify_data_sources", "record_audit_logs"],
      restrictions: ["execute_payments", "modify_trust_evidence", "supersede_authority_systems", "make_irreversible_decisions"],
    },
    federation_law: {
      rules: ["external_systems_shall_integrate_via_contracts", "identity_shall_remain_novaid_based", "trust_verification_shall_be_required", "cross_platform_operations_shall_be_auditable"],
    },
    dispute_resolution: {
      mechanisms: ["automated_validation", "ai_analysis", "dao_arbitration"],
      example_flow: ["transaction_dispute", "replay_verification", "ai_review", "dao_vote", "decision_enforced"],
    },
    compliance_enforcement: {
      rule: "violations_are_architecture_defects_and_system_violations",
      layers: ["validator_engine", "ci_compliance_system", "governance_ai", "dao_enforcement"],
    },
    amendment_process: ["proposal_submitted", "ai_impact_analysis", "public_review", "dao_vote", "enactment_via_contract_update"],
    guarantees: {
      identity_sovereignty: true,
      governance_participation: true,
      financial_transparency: true,
      security_enforcement: true,
      contract_integrity: true,
      ai_safety: true,
      trust_verification: true,
    },
  },
};

const NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK = {
  view: "novaride_regulatory_alignment",
  status: "architecture_contract_ready",
  platform: "NovaRide",
  regulatory_alignment: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "novaride_regulatory_alignment_contract",
    status: "architecture_contract_ready",
    positioning: "Regulatory-Aligned Digital Infrastructure Layer",
    authority_boundary: "regulatory_alignment_is_control_mapping_not_legal_advice_certification_or_regulatory_approval",
    core_principle:
      "NovaRide shall operate within applicable legal frameworks while preserving its constitutional invariants and autonomy.",
    alignment_model: [
      { domain: "Identity", novaride_layer: "NovaID", real_world_equivalent: "National ID / eID", control: "KYC, AML, eKYC, DID, selective disclosure" },
      { domain: "Finance", novaride_layer: "NovaPay", real_world_equivalent: "Banking / payments law", control: "auditability, anti-fraud controls, monitoring, traceable settlement" },
      { domain: "Token", novaride_layer: "NovaToken", real_world_equivalent: "Securities / digital assets", control: "jurisdictional classification and transfer restrictions" },
      { domain: "Governance", novaride_layer: "DAO", real_world_equivalent: "Corporate + cooperative governance", control: "transparent voting, legal wrapper readiness, enforceable contract mapping" },
      { domain: "Trust", novaride_layer: "NovaTrust", real_world_equivalent: "Audit / compliance systems", control: "replay evidence, cryptographic proof, audit readiness" },
    ],
    identity_compliance: {
      aligns_with: ["KYC", "AML", "eKYC", "W3C_DID", "government_document_verification"],
      rule: "identity_verification_required_for_high_risk_financial_or_governance_actions",
    },
    payments_regulation: {
      requirements: ["transactions_shall_be_auditable", "suspicious_activity_shall_be_flagged", "cross_border_payments_shall_be_compliant", "settlement_systems_shall_be_traceable"],
      treasury_rule: "treasury_operations_shall_comply_with_financial_risk_and_audit_standards",
    },
    token_regulation: {
      classification_model: [
        { type: "utility_token", treatment: "platform_usage" },
        { type: "governance_token", treatment: "DAO_participation" },
        { type: "payment_token", treatment: "financial_rules_apply" },
      ],
      rule: "novatoken_shall_comply_with_applicable_digital_asset_regulations_per_jurisdiction",
    },
    privacy_law: {
      aligns_with: ["GDPR", "Privacy_Act_AU", "global_data_protection_standards"],
      principles: ["data_shall_be_user_controlled", "consent_shall_be_explicit", "sensitive_data_shall_be_protected", "data_portability_shall_be_supported"],
      implementation: ["zero_knowledge_proofs_where_needed", "offchain_sensitive_storage", "permission_based_data_sharing"],
    },
    governance_legalization: {
      recognition_model: "digital_cooperative_or_governance_body",
      optional_structures: ["registered_DAO_entity", "foundation", "association"],
    },
    cross_border_framework: {
      rule: "novaride_shall_implement_jurisdiction_aware_compliance_layers",
      flow: ["user_location", "region_detected", "applicable_rules_enforced", "system_adapts"],
      regions: [
        { region: "EU", active_rule: "GDPR enforced" },
        { region: "US", active_rule: "financial reporting" },
        { region: "Africa", active_rule: "mobile money integration" },
      ],
    },
    liability_model: {
      rule: "liability_attributed_by_layer_of_control_and_authority",
      responsibilities: [
        { component: "NovaRide Protocol", responsibility: "Infrastructure" },
        { component: "App developers", responsibility: "Application behavior" },
        { component: "Users", responsibility: "Actions" },
        { component: "DAO", responsibility: "Governance decisions" },
      ],
    },
    ai_regulation_compliance: {
      rules: ["ai_decisions_shall_be_explainable", "ai_shall_not_execute_high_risk_actions_autonomously", "human_or_governance_review_shall_exist"],
    },
    compliance_engine: {
      model: "jurisdiction_aware_policy_enforcement",
      flow: ["load_regulations_for_region", "evaluate_action_against_rules", "block_non_compliant_action", "approve_compliant_action_with_replay_evidence"],
    },
    dashboard: {
      regulatory_status: { identity: "mapped", finance: "mapped", crypto: "mapped", privacy: "mapped" },
      jurisdictions: { EU: "GDPR active", US: "financial rules active", Africa: "mobile money integration" },
      risk_monitor: { fraud_risk: "LOW", compliance_risk: "LOW", audit_readiness: "HIGH" },
    },
    properties: {
      legal_compliance: "control_mapped",
      identity_recognition: "integration_ready",
      financial_regulation_alignment: "policy_gated",
      cross_border_operation: "jurisdiction_aware",
      governance_legality: "legal_wrapper_ready",
      ai_safety_compliance: "human_or_governance_review_required",
    },
  },
};

const NOVARIDE_GLOBAL_EXPANSION_FALLBACK = {
  view: "novaride_global_expansion",
  status: "strategy_contract_ready",
  platform: "NovaRide",
  expansion: {
    platform: "NovaRide",
    version: "2026.07.0",
    classification: "novaride_global_regulatory_expansion_strategy_contract",
    status: "strategy_contract_ready",
    positioning: "Global Regulatory Expansion Strategy",
    authority_boundary: "expansion_strategy_is_rollout_planning_not_country_launch_authorization_or_legal_approval",
    objective: "globally_compliant_identity_mobility_fintech_protocol",
    core_principle: "Global standard architecture plus local regulatory adaptation equals scalable deployment.",
    expansion_model: ["Global Core Platform", "Regional Compliance Layer", "Country-Specific Adaptation", "Local Market Deployment"],
    phases: [
      { phase: "0", name: "Foundation", status: "done", markets: ["Global core platform"], note: "NovaID, NovaPay, NovaTrust, and DAO." },
      { phase: "1", name: "Regulatory ready markets", status: "target", markets: ["Australia", "UK", "Singapore", "UAE"], note: "Clear fintech regulations and stable legal systems." },
      { phase: "2", name: "High growth markets", status: "target", markets: ["Kenya", "Rwanda", "Nigeria", "India"], note: "Mobile-first economies with strong mobility and payments demand." },
      { phase: "3", name: "Complex regulations", status: "target", markets: ["EU", "USA"], note: "Strict compliance and licensing requirements." },
    ],
    country_entry_playbook: {
      regulatory_mapping: ["identify_financial_regulators", "identify_identity_requirements", "identify_transport_rules", "identify_data_protection_laws"],
      legal_structure: ["local_entity", "compliance_officer", "partner_contracts"],
      partnership_model: ["integrate_with_local_banks", "integrate_with_psps_and_mobile_money", "integrate_with_gov_id_or_kyc_providers", "integrate_with_fleet_operators"],
      integration_strategy: "replace_nothing_integrate_with_existing_systems",
    },
    novaid_deployment: {
      basic_id: ["email_and_phone", "platform_access"],
      verified_id: ["KYC", "document_verification"],
      trusted_id: ["government_credential_integration"],
      government_integration_path: ["start_with_KYC_providers", "integrate_gov_APIs", "become_trusted_identity_layer"],
    },
    novapay_deployment: {
      partner_based: ["Stripe", "Adyen", "mobile_money", "banks"],
      licensed_later: ["payment_institution_license", "e_money_license", "crypto_compliance"],
      multi_currency_rollout: ["fiat_only", "stablecoins", "full_on_chain_treasury"],
    },
    token_strategy: {
      rule: "token_must_not_be_treated_as_a_security_without_jurisdiction_review",
      launch_model: [
        { region: "strict_regulation", strategy: "utility_only" },
        { region: "flexible_regulation", strategy: "full_token_model" },
        { region: "DeFi_friendly", strategy: "on_chain_economy" },
      ],
    },
    dao_structure: {
      model: ["on_chain_DAO", "legal_wrapper_foundation_or_association", "local_operations_entity"],
      why_it_matters: ["legal_enforceability", "liability_protection", "regulatory_clarity"],
    },
    cross_border_architecture: {
      compliance_engine: ["detect_user_location", "load_rules_for_region", "enforce_rules"],
      region_examples: [
        { region: "EU", feature: "GDPR mode" },
        { region: "US", feature: "reporting mode" },
        { region: "Africa", feature: "mobile money" },
      ],
    },
    ai_alignment: {
      requirements: ["explainability", "transparency", "audit_logs", "no_autonomous_financial_execution"],
      implementation: "all_ai_decisions_logged_auditable_explainable",
    },
    go_to_market: {
      entry_model: ["launch_pilot_city", "partner_with_local_operators", "acquire_early_users", "expand_region"],
      growth_strategy: ["incentives_token_plus_fiat", "driver_onboarding", "developer_ecosystem", "app_store_expansion"],
    },
    risk_management: {
      top_risks: [
        { risk: "Regulatory rejection", mitigation: "Partner model" },
        { risk: "Financial compliance", mitigation: "Licensed partners" },
        { risk: "Data privacy", mitigation: "Regional storage" },
        { risk: "Token scrutiny", mitigation: "Staged rollout" },
      ],
    },
    dashboard: {
      expansion_status: { Australia: "Live", Kenya: "Live", India: "Pilot", EU: "Preparation" },
      compliance_status: { identity: "OK", finance: "OK", privacy: "OK", token: "Restricted" },
      financial: { transactions_per_day: "$1.5M", revenue: "Growing", cost: "Controlled" },
    },
    execution_blueprint: {
      hub_model: [
        { hub: "Melbourne", role: "regulatory_base_and_funding_hq" },
        { hub: "Burundi", role: "controlled_low_cost_pilot" },
        { hub: "DRC", role: "scale_opportunity_market" },
        { hub: "East Africa", role: "expansion_corridor_kenya_rwanda_uganda" },
      ],
      phase_sequence: [
        { phase: "1", market: "Melbourne", objective: "compliance_and_pilot" },
        { phase: "2", market: "Burundi", objective: "controlled_launch" },
        { phase: "3", market: "DRC", objective: "scaled_deployment" },
        { phase: "4", market: "East Africa", objective: "regional_expansion" },
      ],
      melbourne_pilot: {
        legal_setup: ["Pty Ltd", "global_hq"],
        compliance_checklist: ["KYC_provider", "Privacy_Act", "payment_partner", "licensed_drivers_or_fleets"],
        target: ["airport_transfers", "courier_logistics"],
        pilot_flow: [
          "launch_small_fleet",
          "onboard_10_to_20_drivers",
          "invite_200_to_500_users",
          "test_ride_payment_loop",
          "collect_data",
          "iterate",
        ],
        success_metrics: [
          "1000_plus_rides_per_month",
          "payment_reliability_above_99_percent",
          "user_retention_above_30_percent",
        ],
      },
      burundi_launch: {
        structure: ["local_partner_or_entity", "ops_manager"],
        compliance: ["basic_KYC", "mobile_money", "partner_first"],
        services: ["ride_hailing", "delivery", "mobile_money_payments"],
        pilot_size: ["10_to_30_drivers", "200_to_1000_users"],
      },
      drc_launch: {
        structure: ["partner_led", "local_operator_execution"],
        compliance: ["progressive_KYC", "mobile_money_first", "partnership_adaptation"],
        priorities: ["motorbike_taxis", "delivery_and_logistics", "business_transport"],
        scale_plan: ["pilot_city", "city_expansion", "regional_hubs", "national_coverage"],
      },
      east_africa_expansion: {
        markets: ["Kenya", "Rwanda", "Uganda"],
        kenya: ["M_Pesa_integration", "fintech_plus_delivery_plus_rides"],
        rwanda: ["government_friendly", "NovaID_plus_governance_pilots"],
      },
      legal_entity_template: {
        step_1: "register_local_company_or_partner",
        step_2: ["identity_KYC", "payment_partner", "privacy_laws", "local_licensing"],
        step_3: ["driver_agreements", "partner_agreements", "API_SDK_terms"],
      },
      novaid_rollout: [
        "phone_based_login",
        "verified_KYC",
        "trust_and_reputation",
        "passport_level_system",
      ],
      novapay_rollout: ["payment_partners", "internal_wallet", "multi_currency", "token_layer_later"],
      team_structure: {
        founder: "Australia",
        tech_team: "remote",
        ops_manager: "each_country",
        compliance_advisor: "per_region",
      },
      ninety_day_plan: [
        "register_AU_entity",
        "build_production_ready_app",
        "secure_payment_partner",
        "launch_Melbourne_pilot",
        "begin_Burundi_setup",
        "launch_Burundi_pilot",
        "prepare_DRC_entry",
      ],
    },
  },
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
  { label: "Platform", href: "#platform", detail: "NovaTech map" },
  { label: "Journey", href: "#trust-journey", detail: "Live proof flow" },
  { label: "Score", href: "#trust-score", detail: "Evidence score" },
  { label: "NovaCodePro", href: "#novacodepro", detail: "AI engineering" },
  { label: "Global", href: "#global", detail: "Expansion map" },
  { label: "Pilots", href: "#pilots", detail: "Field evidence" },
  { label: "Trust Center", href: "#trust-center", detail: "Security + governance" },
  { label: "Cases", href: "#case-studies", detail: "Proof stories" },
  { label: "Developers", href: "#developers", detail: "APIs + SDKs" },
  { label: "Downloads", href: "#downloads", detail: "Enterprise assets" },
];

const PLATFORM_PRODUCTS = [
  {
    name: "NovaRide",
    purpose: "Trusted mobility operations",
    features: ["Dispatch", "Fleet monitoring", "Ride replay", "Incident evidence"],
    useCases: ["City pilots", "Fleet operators", "Driver verification"],
    industries: ["Mobility", "Logistics", "Public transport"],
    docs: "/v1/operator/dashboard",
  },
  {
    name: "NovaPay",
    purpose: "Auditable payments and receipts",
    features: ["Payment proof", "Settlement visibility", "Treasury controls", "Receipt replay"],
    useCases: ["Wallets", "Merchant payments", "Agent networks"],
    industries: ["Fintech", "Retail", "Remittance"],
    docs: "#payments",
  },
  {
    name: "NovaID",
    purpose: "Verified identity and device trust",
    features: ["Digital identity", "Device binding", "Roles", "KYC posture"],
    useCases: ["Rider onboarding", "Driver checks", "Enterprise access"],
    industries: ["Identity", "Mobility", "Financial services"],
    docs: "#identity",
  },
  {
    name: "NovaTrust",
    purpose: "Proof, replay, and audit evidence",
    features: ["Evidence packets", "Replay validation", "Audit trails", "Trust scores"],
    useCases: ["Disputes", "Compliance reviews", "Partner verification"],
    industries: ["Enterprise", "Government", "Insurance"],
    docs: "/public/trust/dashboard",
  },
  {
    name: "NovaAI",
    purpose: "Human-approved operational intelligence",
    features: ["Fleet insights", "Payment insights", "Risk insights", "Support intelligence"],
    useCases: ["Recommendations", "Anomaly review", "Decision support"],
    industries: ["Operations", "Compliance", "Customer support"],
    docs: "/v1/novascript/dashboard",
  },
  {
    name: "NovaCodePro",
    purpose: "AI engineering platform",
    features: ["AI coding", "Governance", "CI/CD", "Security", "Deployments"],
    useCases: ["Enterprise engineering", "DevOps", "Regulated software delivery"],
    industries: ["Software", "Government", "Universities", "Enterprise"],
    docs: "#novacodepro",
  },
];

const HERO_FLOW_PRODUCTS = ["NovaID", "NovaRide", "NovaPay", "NovaTrust", "NovaAI"];

const HERO_FLOW_STEPS = [
  "Identity",
  "Operations",
  "Payments",
  "Evidence",
  "AI Insights",
  "Trust Score",
];

const PLATFORM_HOVER_FEATURES = {
  NovaRide: ["Trips", "Dispatch", "Drivers", "Replay Events"],
  NovaPay: ["Payments", "Wallets", "Refunds", "Settlement"],
  NovaID: ["Identity", "Device Trust", "KYC", "Access Controls"],
  NovaTrust: ["Evidence", "Replay", "Audit", "Compliance"],
  NovaAI: ["Insights", "Recommendations", "Risk Detection", "Decision Support"],
  NovaCodePro: ["Code", "Review", "Deploy", "Verify"],
};

const AUDIENCE_PORTALS = [
  {
    audience: "Operators",
    promise: "Run live mobility operations with replay, monitoring, and incident control.",
    capabilities: ["Dispatch", "Fleet management", "Monitoring", "Replay", "Incidents"],
  },
  {
    audience: "Enterprises",
    promise: "Adopt trusted identity, payments, compliance records, and auditable workflows.",
    capabilities: ["Digital identity", "Payments", "Auditability", "Compliance"],
  },
  {
    audience: "Developers",
    promise: "Build integrations with APIs, SDKs, sandbox flows, and proof documentation.",
    capabilities: ["APIs", "SDKs", "Sandbox", "Documentation"],
  },
  {
    audience: "Investors & Partners",
    promise: "See the platform vision, market wedge, roadmap, pilots, and growth strategy.",
    capabilities: ["Vision", "Market", "Roadmap", "Pilot results", "Growth strategy"],
  },
];

const RIDE_REPLAY_STEPS = [
  { step: "Ride Requested", product: "NovaRide", proof: "Request Event Generated" },
  { step: "Driver Verified", product: "NovaID", proof: "NovaID panel lights up" },
  { step: "Ride Started", product: "NovaRide", proof: "NovaRide state updates" },
  { step: "Payment Processed", product: "NovaPay", proof: "NovaPay receipt activates" },
  { step: "Evidence Created", product: "NovaTrust", proof: "Evidence Packet generated" },
  { step: "AI Review", product: "NovaAI", proof: "Trust Insights produced" },
];

const TRUST_SCORE_DETAILS = [
  { label: "Identity Confidence", value: "98%" },
  { label: "Device Binding", value: "100%" },
  { label: "Replay Integrity", value: "99.9%" },
  { label: "Missing Events", value: "0" },
  { label: "Audit Coverage", value: "100%" },
];

const PLATFORM_STATUS = [
  { system: "NovaRide", value: "99.9%", state: "Operational", tone: "active" },
  { system: "NovaPay", value: "99.98%", state: "Operational", tone: "active" },
  { system: "NovaID", value: "100%", state: "Operational", tone: "active" },
  { system: "NovaTrust", value: "100%", state: "Operational", tone: "active" },
  { system: "NovaAI", value: "Advisory Mode", state: "Human approval required", tone: "pilot" },
];

const PILOT_METRICS = [
  { label: "Approved users", value: "57" },
  { label: "Trusted devices", value: "40" },
  { label: "Drivers", value: "10" },
  { label: "Riders", value: "30" },
  { label: "Merchants", value: "2" },
  { label: "Agents", value: "3" },
  { label: "Businesses", value: "2" },
  { label: "PRR", value: "Completed" },
];

const TRUST_CENTER_PILLARS = [
  {
    title: "Security",
    items: ["Device trust", "Identity controls", "RBAC", "Encryption"],
  },
  {
    title: "Governance",
    items: ["Replay validation", "Audit trails", "Evidence integrity", "State machines"],
  },
  {
    title: "Compliance",
    items: ["Audit records", "Data protection", "Financial controls", "Operator approvals"],
  },
];

const WHY_AFRITECHNOLOGY = [
  {
    title: "Verified Identity",
    example: "Drivers, riders, staff, and partners operate with identity and device checks.",
  },
  {
    title: "Trusted Payments",
    example: "Payments produce receipts that can be replayed and audited.",
  },
  {
    title: "Replayable Operations",
    example: "Every key workflow can be reconstructed from events, not assumptions.",
  },
  {
    title: "Governed AI",
    example: "AI recommends. Humans approve. Critical actions remain controlled.",
  },
  {
    title: "Audit-Ready Evidence",
    example: "Operators and partners can export proof packets for review.",
  },
];

const EXPANSION_PATH = [
  "Australia",
  "Burundi",
  "DR Congo",
  "East Africa",
  "Africa",
  "Global Platform",
];

const GLOBAL_PRESENCE = [
  { market: "Australia", status: "Public Pilot", tone: "pilot", x: 78, y: 72 },
  { market: "Burundi", status: "Agricultural Expansion", tone: "partner", x: 52, y: 58 },
  { market: "DRC", status: "Strategic Market", tone: "future", x: 48, y: 61 },
  { market: "East Africa", status: "Expansion Pipeline", tone: "active", x: 55, y: 54 },
];

const CASE_STUDIES = [
  {
    title: "Driver Verification",
    problem: "Unknown driver identity",
    solution: "NovaID verification",
    result: "Verified onboarding",
  },
  {
    title: "Payment Dispute",
    problem: "Customer dispute",
    solution: "NovaPay receipt replay",
    result: "Evidence produced in seconds",
  },
  {
    title: "Ride Investigation",
    problem: "Ride complaint",
    solution: "NovaRide + NovaTrust replay",
    result: "Full event reconstruction",
  },
];

const ENTERPRISE_DOWNLOADS = [
  "Architecture Whitepaper",
  "Trust Framework",
  "Security Overview",
  "Governance Guide",
  "API Book",
];

const DOCS_PORTAL_SECTIONS = [
  "Getting Started",
  "NovaRide",
  "NovaPay",
  "NovaID",
  "NovaTrust",
  "NovaAI",
  "SDKs",
  "APIs",
  "Architecture",
  "Replay Engine",
  "Security",
];

const TRUST_CENTER_PAGES = [
  { path: "/trust", title: "Trust Center", items: ["Security", "Governance", "Compliance", "Evidence"] },
  { path: "/trust/security", title: "Security", items: ["Device Trust", "RBAC", "Encryption", "Identity Controls"] },
  { path: "/trust/governance", title: "Governance", items: ["Replay", "State Machines", "Audit Controls", "Approvals"] },
  { path: "/trust/compliance", title: "Compliance", items: ["Records", "Retention", "Data Protection", "Financial Controls"] },
  { path: "/trust/evidence", title: "Evidence", items: ["Evidence Packets", "Replay Hashes", "Receipts", "Audit Exports"] },
];

const NOVACODEPRO_TARGET_USERS = [
  "Individual developers",
  "Enterprise engineering teams",
  "DevOps engineers",
  "AI engineers",
  "Platform engineers",
  "Government and regulated organizations",
  "Universities and research institutions",
];

const NOVACODEPRO_APPS = [
  {
    name: "NovaCodePro Desktop",
    type: "Cross-platform IDE",
    summary: "A governed local development environment for serious engineering teams.",
    features: [
      "AI-assisted coding",
      "Multi-language support",
      "Intelligent refactoring",
      "Project explorer",
      "Terminal",
      "Git integration",
      "Integrated debugger",
      "Plugin marketplace",
      "Local AI support",
      "Remote development",
    ],
  },
  {
    name: "NovaCodePro Mobile",
    type: "Developer companion",
    summary: "Review, approve, monitor, and coordinate engineering work from mobile.",
    features: [
      "Code review",
      "Notifications",
      "Build monitoring",
      "Merge approval",
      "Deployment status",
      "GitHub/GitLab integration",
      "AI chat",
      "Project management",
    ],
  },
  {
    name: "NovaCloud IDE",
    type: "Browser workspace",
    summary: "Zero-install cloud workspaces with collaborative engineering and instant preview.",
    features: [
      "Zero installation",
      "Cloud workspaces",
      "Collaborative editing",
      "AI programming",
      "Terminal",
      "Containers",
      "Kubernetes access",
      "Instant preview",
    ],
  },
  {
    name: "NovaAI Assistant",
    type: "Engineering AI",
    summary: "AI support for code, tests, architecture, security, documentation, SQL, and DevOps.",
    features: [
      "Code generation",
      "Bug fixing",
      "Architecture reviews",
      "Security analysis",
      "Documentation generation",
      "Test generation",
      "API design",
      "SQL generation",
      "DevOps assistance",
    ],
  },
  {
    name: "NovaFlow",
    type: "Workflow automation",
    summary: "Governed CI/CD, build orchestration, testing, release automation, and rollbacks.",
    features: [
      "CI/CD pipelines",
      "Build orchestration",
      "Testing",
      "Release automation",
      "Infrastructure provisioning",
      "GitOps",
      "Rollbacks",
    ],
  },
  {
    name: "NovaDeploy",
    type: "Deployment platform",
    summary: "Deploy across Docker, Kubernetes, hyperscalers, on-premises, and edge targets.",
    features: ["Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "On-premises", "Edge deployments"],
  },
  {
    name: "NovaMonitor",
    type: "Observability",
    summary: "Logs, metrics, traces, dashboards, anomalies, and incident timelines.",
    features: [
      "Logs",
      "Metrics",
      "Traces",
      "Error monitoring",
      "Performance dashboards",
      "AI anomaly detection",
      "Incident timelines",
    ],
  },
  {
    name: "NovaSecurity",
    type: "Security platform",
    summary: "Security and compliance controls across source, dependencies, containers, and runtime.",
    features: [
      "SAST",
      "DAST",
      "Dependency scanning",
      "Secret detection",
      "License compliance",
      "SBOM generation",
      "Container scanning",
      "Runtime protection",
    ],
  },
  {
    name: "NovaDocs",
    type: "Developer portal",
    summary: "Versioned documentation, architecture diagrams, ADRs, tutorials, and SDK references.",
    features: [
      "API documentation",
      "Architecture diagrams",
      "ADR management",
      "Tutorials",
      "SDK references",
      "Knowledge base",
      "Versioned documentation",
    ],
  },
  {
    name: "NovaMarketplace",
    type: "Engineering marketplace",
    summary: "Extensions, templates, themes, AI agents, SDKs, components, and enterprise connectors.",
    features: ["Extensions", "Templates", "Themes", "AI agents", "SDKs", "Components", "Enterprise connectors"],
  },
];

const NOVACODEPRO_AI_AGENTS = [
  "Autonomous coding agents",
  "Code review agents",
  "Test generation agents",
  "Security agents",
  "Documentation agents",
  "Refactoring agents",
  "Performance optimization agents",
  "Infrastructure agents",
  "Database agents",
  "Release management agents",
];

const NOVACODEPRO_ENTERPRISE_FEATURES = [
  "Multi-tenant organizations",
  "SSO (SAML/OIDC)",
  "Role-based access control",
  "Audit logging",
  "Governance policies",
  "Approval workflows",
  "Compliance reporting",
  "Cost management",
  "Workspace templates",
];

const NOVACODEPRO_DEVELOPER_SERVICES = [
  "Git repositories",
  "Package registry",
  "Container registry",
  "Artifact storage",
  "Build cache",
  "Secrets management",
  "API gateway",
  "Webhooks",
];

const NOVACODEPRO_LANGUAGES = [
  "Python",
  "TypeScript",
  "JavaScript",
  "Java",
  "Kotlin",
  "C#",
  "Go",
  "Rust",
  "C++",
  "Swift",
  "Dart",
  "PHP",
  "Ruby",
];

const NOVACODEPRO_ECOSYSTEM = [
  { product: "NovaRide", role: "Mobility application development and APIs" },
  { product: "NovaPay", role: "Payment services, SDKs, and financial integrations" },
  { product: "NovaID", role: "Identity, authentication, and access management" },
  { product: "NovaTrust", role: "Governance, compliance, and verification workflows" },
  { product: "NovaAI", role: "AI services and model integration" },
  { product: "NovaCloud", role: "Infrastructure, containers, and deployment" },
  { product: "NovaMonitor", role: "Observability and operational insights" },
];

const NOVACODEPRO_X_MODULES = [
  { name: "NovaCloud IDE", role: "Browser-based engineering environment", features: ["Remote development", "Python", "JavaScript", "TypeScript", "Django", "React", "Flutter", "Go", "Rust", "Java", "C#"] },
  { name: "NovaAI Engineering", role: "AI engineering brain", features: ["Architecture", "Code", "Review", "Audit", "Documentation"] },
  { name: "NovaFlow CI/CD", role: "Pipeline engine", features: ["Build", "Test", "Lint", "Security Scan", "Policy Validation", "Deploy"] },
  { name: "NovaDeploy", role: "Release platform", features: ["Docker", "Kubernetes", "Azure", "AWS", "GCP", "On-Premise"] },
  { name: "NovaMonitor", role: "Observability", features: ["CPU", "Memory", "Latency", "Errors", "Deployments", "Availability"] },
  { name: "NovaSecurity", role: "Security and compliance", features: ["SAST", "DAST", "Secrets Detection", "Dependency Scanning", "Container Scanning"] },
  { name: "NovaDocs", role: "Documentation platform", features: ["Technical Docs", "Architecture Docs", "Governance Docs", "Runbooks", "API Docs", "Developer Guides"] },
  { name: "NovaMarketplace", role: "Extension ecosystem", features: ["AI Extensions", "Themes", "Language Packs", "Deployment Connectors", "Monitoring Tools", "Enterprise Plugins"] },
  { name: "NovaGit", role: "Enterprise source control", features: ["Repositories", "Branch protection", "Pull requests", "Review workflows", "Signed commits", "Repository policies"] },
  { name: "NovaWorkspaces", role: "Cloud dev environments", features: ["Python Workspace", "React Workspace", "Django Workspace", "Flutter Workspace"] },
  { name: "NovaGovernance", role: "Evidence-driven governance", features: ["Feature Request", "ADR", "Implementation", "Review", "Evidence", "Approval", "Audit Trail"] },
];

const NOVACODEPRO_AI_ROLES = [
  { role: "Nova Architect", action: "Design systems", outputs: ["Architecture diagrams", "Technical decisions", "ADRs", "Domain models"] },
  { role: "Nova Developer", action: "Generate code", outputs: ["Services", "APIs", "Tests", "Refactoring"] },
  { role: "Nova Reviewer", action: "Validate engineering quality", outputs: ["Standards", "Performance", "Security", "Compliance"] },
  { role: "Nova Auditor", action: "Check trust readiness", outputs: ["Evidence", "Replayability", "Governance", "Trust controls"] },
];

const NOVACODEPRO_ENGINEERING_JOURNEY = [
  { step: "Create Repository", product: "NovaGit", result: "Repository policies attached" },
  { step: "Generate Code", product: "NovaAI", result: "Service, tests, and docs proposed" },
  { step: "Run Pipeline", product: "NovaFlow", result: "Build, test, lint, and policy checks complete" },
  { step: "Security Validation", product: "NovaSecurity", result: "SAST, dependencies, and secrets pass" },
  { step: "Deploy", product: "NovaDeploy", result: "Approval gate releases controlled deployment" },
  { step: "Evidence Generated", product: "NovaTrust", result: "Evidence Packet stored for audit" },
];

const NOVACODEPRO_STATUS = [
  { system: "NovaCloud IDE", state: "Operational" },
  { system: "NovaAI", state: "Operational" },
  { system: "NovaFlow", state: "Operational" },
  { system: "NovaDeploy", state: "Operational" },
  { system: "NovaMonitor", state: "Operational" },
  { system: "NovaSecurity", state: "Operational" },
  { system: "NovaDocs", state: "Operational" },
  { system: "NovaMarketplace", state: "Operational" },
];

const NOVACODEPRO_ENTERPRISE_CONTROL_CENTER = [
  "Organizations",
  "Teams",
  "Projects",
  "Billing",
  "Roles",
  "Permissions",
  "Audit Logs",
];

const NOVACODEPRO_TENANT_MODEL = [
  "Users",
  "Repositories",
  "Workspaces",
  "Pipelines",
  "Deployments",
  "Evidence",
  "Billing",
];

const NOVACODEPRO_DOCS_PORTAL = [
  "Quick Start",
  "API Reference",
  "SDKs",
  "Extensions",
  "Governance",
  "Security",
  "CI/CD",
  "Deployments",
  "Observability",
];

const NOVACODEPRO_MARKETPLACE_ECONOMY = [
  { category: "Extensions", model: "Free" },
  { category: "Templates", model: "Professional" },
  { category: "Agents", model: "Enterprise" },
  { category: "Themes", model: "Free" },
  { category: "Deploy Connectors", model: "Marketplace Revenue Share" },
  { category: "Automation Packs", model: "Enterprise" },
];

const TRUSTED_PRODUCT_POSITIONING = [
  ["NovaRide", "Trusted Mobility"],
  ["NovaPay", "Trusted Payments"],
  ["NovaID", "Trusted Identity"],
  ["NovaTrust", "Trusted Evidence"],
  ["NovaAI", "Trusted Intelligence"],
  ["NovaCodePro", "Trusted Engineering"],
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
  "NovaRide Passenger",
  "NovaRide Driver",
  "NovaRide Operator App / Portal",
  "NovaRide Fleet",
  "NovaRide Business",
  "NovaRide Merchant Portal",
  "NovaRide Corporate Portal",
  "NovaRide Admin",
  "NovaRide Inspector App / Portal",
  "NovaRide Trust Portal",
  "NovaRide Support",
  "NovaRide Finance Portal",
  "NovaRide Partner",
  "NovaRide Developer Portal",
  "NovaRide Executive Dashboard",
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

const NOVARIDE_OPERATIONS_KPIS = [
  { label: "Live Rides", value: "1,284", trend: "+18.5%", detail: "citywide active trips" },
  { label: "Active Drivers", value: "2,341", trend: "+15.2%", detail: "online supply" },
  { label: "Bookings Today", value: "3,562", trend: "+12.7%", detail: "completed + active" },
  { label: "Revenue", value: "AUD 45,982", trend: "+20.1%", detail: "gross booking value" },
  { label: "Completion Rate", value: "98.6%", trend: "+2.3%", detail: "ride lifecycle success" },
];

const NOVARIDE_MAP_CLUSTERS = [
  { label: "Parramatta", count: 24, x: 22, y: 58, tone: "cluster" },
  { label: "North Sydney", count: 18, x: 58, y: 24, tone: "cluster" },
  { label: "Central", count: 31, x: 64, y: 52, tone: "cluster" },
  { label: "South West", count: 16, x: 36, y: 78, tone: "cluster" },
];

const NOVARIDE_MAP_DRIVERS = [
  { id: "DRV-104", x: 46, y: 34, status: "available" },
  { id: "DRV-227", x: 70, y: 43, status: "busy" },
  { id: "DRV-318", x: 51, y: 65, status: "available" },
  { id: "DRV-421", x: 78, y: 63, status: "offline" },
  { id: "DRV-502", x: 29, y: 42, status: "busy" },
  { id: "DRV-616", x: 44, y: 81, status: "available" },
  { id: "DRV-730", x: 63, y: 72, status: "at-risk" },
];

const NOVARIDE_ACTIVITY_FEED = [
  { time: "19:42", event: "New ride accepted", actor: "DRV-104", value: "AUD 23.40", tone: "success" },
  { time: "19:40", event: "Ride picked up", actor: "RIDE-67231", value: "AUD 18.75", tone: "info" },
  { time: "19:38", event: "Ride completed", actor: "RIDE-67212", value: "AUD 27.60", tone: "success" },
  { time: "19:35", event: "Driver online", actor: "DRV-616", value: "CBD", tone: "neutral" },
  { time: "19:33", event: "Incident reported", actor: "INC-9912", value: "Review", tone: "warning" },
];

const NOVARIDE_OPERATION_ALERTS = [
  { title: "High Demand Zone", detail: "Sydney CBD demand spike at 185%.", severity: "critical" },
  { title: "Driver Shortage", detail: "Northern Beaches has only 12 drivers available.", severity: "warning" },
  { title: "System Maintenance", detail: "Scheduled maintenance window 02:00-04:00 AM.", severity: "info" },
];

const NOVARIDE_FLEET_STATUS = [
  { label: "Available", value: "1,245", percent: "53%" },
  { label: "Busy", value: "876", percent: "37%" },
  { label: "Offline", value: "220", percent: "9%" },
];

const NOVARIDE_PAYMENT_OVERVIEW = [
  { label: "Revenue", value: "AUD 45,982" },
  { label: "Payouts", value: "AUD 32,156" },
  { label: "Pending", value: "AUD 4,821" },
];

const NOVARIDE_TRUST_SAFETY = [
  { label: "Trust Score", value: "98.7 / 100" },
  { label: "Verified Drivers", value: "2,156 / 2,341" },
  { label: "Verified Rides", value: "3,512 / 3,562" },
  { label: "Open Incidents", value: "3" },
];

const NOVARIDE_OPERATION_MODULES = [
  {
    name: "Operator Module",
    focus: "Real-time dispatch and monitoring",
    capabilities: ["Live map", "Manual dispatch intervention", "Incident monitoring", "Ride replay"],
  },
  {
    name: "Admin Module",
    focus: "Pricing, compliance, and configuration",
    capabilities: ["Pricing rules", "Surge multiplier graph", "KYC 98%", "Vehicle compliance 96%"],
  },
  {
    name: "Support Module",
    focus: "Resolution workflow",
    capabilities: ["Ride lookup #67231", "Issue refund", "Apply promo", "Open dispute"],
  },
  {
    name: "Inspector Module",
    focus: "Vehicle and driver verification",
    capabilities: ["License", "Registration", "Insurance", "Roadworthiness", "Pass / fail decision"],
  },
];

const NOVARIDE_APP_INTEGRATIONS = [
  {
    name: "Driver App",
    detail: "Earnings AUD 240, 12 trips, 96% acceptance, accept / decline flow",
  },
  {
    name: "Rider App",
    detail: "Trip booking, live tracking, Economy AUD 18, Comfort AUD 25, XL AUD 35",
  },
  {
    name: "Operator Portal",
    detail: "City command, fleet health, trust evidence, incident decisions",
  },
];

const NOVARIDE_ECOSYSTEM_APPS = [
  { name: "NovaID", detail: "identity and verification" },
  { name: "NovaPay", detail: "payments and settlements" },
  { name: "NovaConnect", detail: "logistics and deliveries" },
  { name: "NovaHealth", detail: "emergency support" },
  { name: "NovaLearn", detail: "training and certification" },
];

const NOVARIDE_AI_ENHANCEMENTS = [
  "AI Dispatch Insights Panel",
  "Incident Heatmap Layer",
  "Driver Incentive Automation",
  "Voice Command for Operators",
  "Real-Time Profit Dashboard",
];

const NOVARIDE_OPERATOR_RBAC = [
  { role: "Operator", scope: "Observe, broadcast, contact, track route" },
  { role: "Senior Operator", scope: "Reassign driver, trigger surge, lock zones" },
  { role: "Admin", scope: "Pricing, RBAC, city configuration" },
  { role: "Compliance Officer", scope: "Audit log, replay evidence, incident review" },
  { role: "Support Agent", scope: "Passenger contact, refund workflow, dispute intake" },
];

const NOVARIDE_OPERATOR_BACKEND_MODULES = [
  "OperatorMetricsService",
  "DispatchService",
  "GeoService",
  "RealtimeGateway",
  "IncidentService",
  "AlertEngine",
  "AnalyticsAggregator",
];

function displayArchitectureToken(value) {
  return String(value || "")
    .split("_")
    .filter(Boolean)
    .map((part) => {
      const upper = part.toUpperCase();
      if (["AI", "API", "DR", "ETA", "HSM", "KMS", "RBAC", "SDK", "SLA", "SLO"].includes(upper)) {
        return upper;
      }
      return `${part.charAt(0).toUpperCase()}${part.slice(1)}`;
    })
    .join(" ")
    .replace("Aml Kyc", "AML/KYC");
}


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

function normalizeComplianceReport(report) {
  if (!report || typeof report !== "object") {
    return ARCHITECTURE_COMPLIANCE_FALLBACK;
  }
  const rows = Array.isArray(report.report) ? report.report : [];
  const total = Number(report.rules_total ?? rows.length);
  const passed = Number(
    report.rules_passed ?? rows.filter((item) => item?.passed === true).length,
  );
  const score =
    Number.isFinite(Number(report.score)) && Number(report.score) >= 0
      ? Number(report.score)
      : total > 0
        ? Math.round((passed / total) * 100)
        : 0;

  return {
    ...ARCHITECTURE_COMPLIANCE_FALLBACK,
    ...report,
    score,
    rules_total: total,
    rules_passed: passed,
    rules_failed: Number(report.rules_failed ?? Math.max(0, total - passed)),
    report: rows,
    capabilities: Array.isArray(report.capabilities)
      ? report.capabilities
      : ARCHITECTURE_COMPLIANCE_FALLBACK.capabilities,
  };
}

function normalizeRemediationReport(report) {
  if (!report || typeof report !== "object") {
    return ARCHITECTURE_REMEDIATION_FALLBACK;
  }
  return {
    ...ARCHITECTURE_REMEDIATION_FALLBACK,
    ...report,
    fixes: Array.isArray(report.fixes) ? report.fixes : [],
    executions: Array.isArray(report.executions) ? report.executions : [],
  };
}

function normalizeLearningReport(report) {
  if (!report || typeof report !== "object") {
    return ARCHITECTURE_LEARNING_FALLBACK;
  }
  return {
    ...ARCHITECTURE_LEARNING_FALLBACK,
    ...report,
    risk_profile:
      report.risk_profile && typeof report.risk_profile === "object"
        ? {
            ...ARCHITECTURE_LEARNING_FALLBACK.risk_profile,
            ...report.risk_profile,
          }
        : ARCHITECTURE_LEARNING_FALLBACK.risk_profile,
    patterns:
      report.patterns && typeof report.patterns === "object" && !Array.isArray(report.patterns)
        ? report.patterns
        : ARCHITECTURE_LEARNING_FALLBACK.patterns,
    knowledge_graph:
      report.knowledge_graph &&
      typeof report.knowledge_graph === "object" &&
      !Array.isArray(report.knowledge_graph)
        ? report.knowledge_graph
        : ARCHITECTURE_LEARNING_FALLBACK.knowledge_graph,
    optimizer_suggestions: Array.isArray(report.optimizer_suggestions)
      ? report.optimizer_suggestions
      : ARCHITECTURE_LEARNING_FALLBACK.optimizer_suggestions,
    remediation:
      report.remediation && typeof report.remediation === "object"
        ? normalizeRemediationReport(report.remediation)
      : ARCHITECTURE_LEARNING_FALLBACK.remediation,
  };
}

function normalizePredictiveReport(report) {
  if (!report || typeof report !== "object") {
    return ARCHITECTURE_PREDICTIVE_FALLBACK;
  }
  return {
    ...ARCHITECTURE_PREDICTIVE_FALLBACK,
    ...report,
    digital_twin:
      report.digital_twin && typeof report.digital_twin === "object"
        ? {
            ...ARCHITECTURE_PREDICTIVE_FALLBACK.digital_twin,
            ...report.digital_twin,
          }
        : ARCHITECTURE_PREDICTIVE_FALLBACK.digital_twin,
    scenarios: Array.isArray(report.scenarios) ? report.scenarios : ARCHITECTURE_PREDICTIVE_FALLBACK.scenarios,
    predictions: Array.isArray(report.predictions)
      ? report.predictions
      : ARCHITECTURE_PREDICTIVE_FALLBACK.predictions,
    preventive_actions: Array.isArray(report.preventive_actions)
      ? report.preventive_actions
      : ARCHITECTURE_PREDICTIVE_FALLBACK.preventive_actions,
    metrics:
      report.metrics && typeof report.metrics === "object"
        ? {
            ...ARCHITECTURE_PREDICTIVE_FALLBACK.metrics,
            ...report.metrics,
          }
        : ARCHITECTURE_PREDICTIVE_FALLBACK.metrics,
    compliance:
      report.compliance && typeof report.compliance === "object"
        ? report.compliance
        : ARCHITECTURE_PREDICTIVE_FALLBACK.compliance,
    remediation:
      report.remediation && typeof report.remediation === "object"
        ? normalizeRemediationReport(report.remediation)
        : ARCHITECTURE_PREDICTIVE_FALLBACK.remediation,
    learning:
      report.learning && typeof report.learning === "object"
        ? normalizeLearningReport(report.learning)
        : ARCHITECTURE_PREDICTIVE_FALLBACK.learning,
  };
}

function normalizeAutonomousReport(report) {
  if (!report || typeof report !== "object") {
    return ARCHITECTURE_AUTONOMOUS_FALLBACK;
  }
  return {
    ...ARCHITECTURE_AUTONOMOUS_FALLBACK,
    ...report,
    digital_twin:
      report.digital_twin && typeof report.digital_twin === "object"
        ? {
            ...ARCHITECTURE_AUTONOMOUS_FALLBACK.digital_twin,
            ...report.digital_twin,
          }
        : ARCHITECTURE_AUTONOMOUS_FALLBACK.digital_twin,
    multi_agent:
      report.multi_agent && typeof report.multi_agent === "object"
        ? {
            ...ARCHITECTURE_AUTONOMOUS_FALLBACK.multi_agent,
            ...report.multi_agent,
            severity_breakdown:
              report.multi_agent.severity_breakdown &&
              typeof report.multi_agent.severity_breakdown === "object"
                ? {
                    ...ARCHITECTURE_AUTONOMOUS_FALLBACK.multi_agent.severity_breakdown,
                    ...report.multi_agent.severity_breakdown,
                  }
                : ARCHITECTURE_AUTONOMOUS_FALLBACK.multi_agent.severity_breakdown,
            findings: Array.isArray(report.multi_agent.findings)
              ? report.multi_agent.findings
              : ARCHITECTURE_AUTONOMOUS_FALLBACK.multi_agent.findings,
          }
        : ARCHITECTURE_AUTONOMOUS_FALLBACK.multi_agent,
    crisis: Array.isArray(report.crisis) ? report.crisis : ARCHITECTURE_AUTONOMOUS_FALLBACK.crisis,
    crisis_summary:
      report.crisis_summary && typeof report.crisis_summary === "object"
        ? {
            ...ARCHITECTURE_AUTONOMOUS_FALLBACK.crisis_summary,
            ...report.crisis_summary,
            critical_scenarios: Array.isArray(report.crisis_summary.critical_scenarios)
              ? report.crisis_summary.critical_scenarios
              : ARCHITECTURE_AUTONOMOUS_FALLBACK.crisis_summary.critical_scenarios,
          }
        : ARCHITECTURE_AUTONOMOUS_FALLBACK.crisis_summary,
    economic_optimization:
      report.economic_optimization && typeof report.economic_optimization === "object"
        ? {
            ...ARCHITECTURE_AUTONOMOUS_FALLBACK.economic_optimization,
            ...report.economic_optimization,
            actions: Array.isArray(report.economic_optimization.actions)
              ? report.economic_optimization.actions
              : ARCHITECTURE_AUTONOMOUS_FALLBACK.economic_optimization.actions,
          }
        : ARCHITECTURE_AUTONOMOUS_FALLBACK.economic_optimization,
    refactor_suggestions: Array.isArray(report.refactor_suggestions)
      ? report.refactor_suggestions
      : ARCHITECTURE_AUTONOMOUS_FALLBACK.refactor_suggestions,
    metrics:
      report.metrics && typeof report.metrics === "object"
        ? {
            ...ARCHITECTURE_AUTONOMOUS_FALLBACK.metrics,
            ...report.metrics,
          }
        : ARCHITECTURE_AUTONOMOUS_FALLBACK.metrics,
    predictive:
      report.predictive && typeof report.predictive === "object"
        ? normalizePredictiveReport(report.predictive)
        : ARCHITECTURE_AUTONOMOUS_FALLBACK.predictive,
  };
}

function normalizeTreasuryIntelligence(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.treasury_intelligence || payload.treasuryIntelligence || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK;
  }

  return {
    ...NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK,
    ...report,
    decision:
      report.decision && typeof report.decision === "object"
        ? {
            ...NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK.decision,
            ...report.decision,
          }
        : NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK.decision,
    recommendations: Array.isArray(report.recommendations)
      ? report.recommendations
      : NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK.recommendations,
    stress_tests: Array.isArray(report.stress_tests)
      ? report.stress_tests
      : NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK.stress_tests,
    provider_snapshot: Array.isArray(report.provider_snapshot)
      ? report.provider_snapshot
      : NOVAPAY_TREASURY_INTELLIGENCE_FALLBACK.provider_snapshot,
  };
}

function normalizeGlobalTreasuryIntelligence(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.treasury_intelligence || payload.treasuryIntelligence || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK;
  }

  const core = normalizeTreasuryIntelligence(report.core);
  const multiCurrency =
    report.multi_currency && typeof report.multi_currency === "object"
      ? {
          ...NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.multi_currency,
          ...report.multi_currency,
          currency_distribution: Array.isArray(report.multi_currency.currency_distribution)
            ? report.multi_currency.currency_distribution
            : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.multi_currency.currency_distribution,
          hedge_actions: Array.isArray(report.multi_currency.hedge_actions)
            ? report.multi_currency.hedge_actions
            : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.multi_currency.hedge_actions,
        }
      : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.multi_currency;
  const onchain =
    report.onchain && typeof report.onchain === "object"
      ? {
          ...NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.onchain,
          ...report.onchain,
          anchor_batch_plan: Array.isArray(report.onchain.anchor_batch_plan)
            ? report.onchain.anchor_batch_plan
            : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.onchain.anchor_batch_plan,
        }
      : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.onchain;

  return {
    ...NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK,
    ...report,
    core,
    multi_currency: multiCurrency,
    onchain,
    recommendations: Array.isArray(report.recommendations)
      ? report.recommendations
      : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.recommendations,
    metrics:
      report.metrics && typeof report.metrics === "object"
        ? {
            ...NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.metrics,
            ...report.metrics,
          }
        : NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_FALLBACK.metrics,
  };
}

function normalizeDaoEconomy(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.economy_intelligence || payload.economyIntelligence || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_DAO_ECONOMY_FALLBACK;
  }

  return {
    ...NOVARIDE_DAO_ECONOMY_FALLBACK,
    ...report,
    token_economy:
      report.token_economy && typeof report.token_economy === "object"
        ? {
            ...NOVARIDE_DAO_ECONOMY_FALLBACK.token_economy,
            ...report.token_economy,
            utility: Array.isArray(report.token_economy.utility)
              ? report.token_economy.utility
              : NOVARIDE_DAO_ECONOMY_FALLBACK.token_economy.utility,
            reward_actions: Array.isArray(report.token_economy.reward_actions)
              ? report.token_economy.reward_actions
              : NOVARIDE_DAO_ECONOMY_FALLBACK.token_economy.reward_actions,
          }
        : NOVARIDE_DAO_ECONOMY_FALLBACK.token_economy,
    governance:
      report.governance && typeof report.governance === "object"
        ? {
            ...NOVARIDE_DAO_ECONOMY_FALLBACK.governance,
            ...report.governance,
            proposal_queue: Array.isArray(report.governance.proposal_queue)
              ? report.governance.proposal_queue
              : NOVARIDE_DAO_ECONOMY_FALLBACK.governance.proposal_queue,
          }
        : NOVARIDE_DAO_ECONOMY_FALLBACK.governance,
    treasury:
      report.treasury && typeof report.treasury === "object"
        ? {
            ...NOVARIDE_DAO_ECONOMY_FALLBACK.treasury,
            ...report.treasury,
            allocation_plan: Array.isArray(report.treasury.allocation_plan)
              ? report.treasury.allocation_plan
              : NOVARIDE_DAO_ECONOMY_FALLBACK.treasury.allocation_plan,
          }
        : NOVARIDE_DAO_ECONOMY_FALLBACK.treasury,
    onchain:
      report.onchain && typeof report.onchain === "object"
        ? {
            ...NOVARIDE_DAO_ECONOMY_FALLBACK.onchain,
            ...report.onchain,
            proposal_batch_plan: Array.isArray(report.onchain.proposal_batch_plan)
              ? report.onchain.proposal_batch_plan
              : NOVARIDE_DAO_ECONOMY_FALLBACK.onchain.proposal_batch_plan,
            treasury_batch_plan: Array.isArray(report.onchain.treasury_batch_plan)
              ? report.onchain.treasury_batch_plan
              : NOVARIDE_DAO_ECONOMY_FALLBACK.onchain.treasury_batch_plan,
          }
        : NOVARIDE_DAO_ECONOMY_FALLBACK.onchain,
    metrics:
      report.metrics && typeof report.metrics === "object"
        ? {
            ...NOVARIDE_DAO_ECONOMY_FALLBACK.metrics,
            ...report.metrics,
          }
        : NOVARIDE_DAO_ECONOMY_FALLBACK.metrics,
    recommendations: Array.isArray(report.recommendations)
      ? report.recommendations
      : NOVARIDE_DAO_ECONOMY_FALLBACK.recommendations,
  };
}

function normalizeProtocolMarketplace(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.marketplace || payload.protocol_marketplace || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK;
  }

  return {
    ...NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK,
    ...report,
    marketplace: {
      ...NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace,
      ...report,
      storefronts: Array.isArray(report.storefronts)
        ? report.storefronts
        : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.storefronts,
      catalog: Array.isArray(report.catalog)
        ? report.catalog
        : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.catalog,
      publishing_pipeline: Array.isArray(report.publishing_pipeline)
        ? report.publishing_pipeline
        : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.publishing_pipeline,
      developer_program:
        report.developer_program && typeof report.developer_program === "object"
          ? {
              ...NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.developer_program,
              ...report.developer_program,
            }
          : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.developer_program,
      governance:
        report.governance && typeof report.governance === "object"
          ? {
              ...NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.governance,
              ...report.governance,
              policy_gates: Array.isArray(report.governance.policy_gates)
                ? report.governance.policy_gates
                : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.governance.policy_gates,
            }
          : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.governance,
      economics:
        report.economics && typeof report.economics === "object"
          ? {
              ...NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.economics,
              ...report.economics,
              treasury_split: Array.isArray(report.economics.treasury_split)
                ? report.economics.treasury_split
                : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.economics.treasury_split,
            }
          : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.economics,
      metrics:
        report.metrics && typeof report.metrics === "object"
          ? {
              ...NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.metrics,
              ...report.metrics,
            }
          : NOVARIDE_PROTOCOL_MARKETPLACE_FALLBACK.marketplace.metrics,
    },
  };
}

function normalizeAppStore(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.app_store || payload.appStore || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_APP_STORE_FALLBACK;
  }

  return {
    ...NOVARIDE_APP_STORE_FALLBACK,
    ...report,
    app_store: {
      ...NOVARIDE_APP_STORE_FALLBACK.app_store,
      ...report,
      categories: Array.isArray(report.categories)
        ? report.categories
        : NOVARIDE_APP_STORE_FALLBACK.app_store.categories,
      apps: Array.isArray(report.apps) ? report.apps : NOVARIDE_APP_STORE_FALLBACK.app_store.apps,
      publishing_pipeline: Array.isArray(report.publishing_pipeline)
        ? report.publishing_pipeline
        : NOVARIDE_APP_STORE_FALLBACK.app_store.publishing_pipeline,
      developer_flow: Array.isArray(report.developer_flow)
        ? report.developer_flow
        : NOVARIDE_APP_STORE_FALLBACK.app_store.developer_flow,
      governance:
        report.governance && typeof report.governance === "object"
          ? {
              ...NOVARIDE_APP_STORE_FALLBACK.app_store.governance,
              ...report.governance,
              policy_gates: Array.isArray(report.governance.policy_gates)
                ? report.governance.policy_gates
                : NOVARIDE_APP_STORE_FALLBACK.app_store.governance.policy_gates,
            }
          : NOVARIDE_APP_STORE_FALLBACK.app_store.governance,
      monetization:
        report.monetization && typeof report.monetization === "object"
          ? {
              ...NOVARIDE_APP_STORE_FALLBACK.app_store.monetization,
              ...report.monetization,
              revenue_streams: Array.isArray(report.monetization.revenue_streams)
                ? report.monetization.revenue_streams
                : NOVARIDE_APP_STORE_FALLBACK.app_store.monetization.revenue_streams,
            }
          : NOVARIDE_APP_STORE_FALLBACK.app_store.monetization,
      metrics:
        report.metrics && typeof report.metrics === "object"
          ? {
              ...NOVARIDE_APP_STORE_FALLBACK.app_store.metrics,
              ...report.metrics,
            }
          : NOVARIDE_APP_STORE_FALLBACK.app_store.metrics,
    },
  };
}

function normalizeSuperApp(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.super_app || payload.superApp || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_SUPER_APP_FALLBACK;
  }

  return {
    ...NOVARIDE_SUPER_APP_FALLBACK,
    ...report,
    super_app: {
      ...NOVARIDE_SUPER_APP_FALLBACK.super_app,
      ...report,
      modules: Array.isArray(report.modules)
        ? report.modules
        : NOVARIDE_SUPER_APP_FALLBACK.super_app.modules,
      ecosystem_loop: Array.isArray(report.ecosystem_loop)
        ? report.ecosystem_loop
        : NOVARIDE_SUPER_APP_FALLBACK.super_app.ecosystem_loop,
      profile:
        report.profile && typeof report.profile === "object"
          ? {
              ...NOVARIDE_SUPER_APP_FALLBACK.super_app.profile,
              ...report.profile,
            }
          : NOVARIDE_SUPER_APP_FALLBACK.super_app.profile,
      wallet:
        report.wallet && typeof report.wallet === "object"
          ? {
              ...NOVARIDE_SUPER_APP_FALLBACK.super_app.wallet,
              ...report.wallet,
              balances:
                report.wallet.balances && typeof report.wallet.balances === "object"
                  ? report.wallet.balances
                  : NOVARIDE_SUPER_APP_FALLBACK.super_app.wallet.balances,
            }
          : NOVARIDE_SUPER_APP_FALLBACK.super_app.wallet,
      governance:
        report.governance && typeof report.governance === "object"
          ? {
              ...NOVARIDE_SUPER_APP_FALLBACK.super_app.governance,
              ...report.governance,
            }
          : NOVARIDE_SUPER_APP_FALLBACK.super_app.governance,
      ai_assistant:
        report.ai_assistant && typeof report.ai_assistant === "object"
          ? {
              ...NOVARIDE_SUPER_APP_FALLBACK.super_app.ai_assistant,
              ...report.ai_assistant,
              recommendations: Array.isArray(report.ai_assistant.recommendations)
                ? report.ai_assistant.recommendations
                : NOVARIDE_SUPER_APP_FALLBACK.super_app.ai_assistant.recommendations,
            }
          : NOVARIDE_SUPER_APP_FALLBACK.super_app.ai_assistant,
      metrics:
        report.metrics && typeof report.metrics === "object"
          ? {
              ...NOVARIDE_SUPER_APP_FALLBACK.super_app.metrics,
              ...report.metrics,
            }
          : NOVARIDE_SUPER_APP_FALLBACK.super_app.metrics,
    },
  };
}

function normalizeNovaID(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.identity || payload.novaid || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVAID_IDENTITY_FALLBACK;
  }

  return {
    ...NOVAID_IDENTITY_FALLBACK,
    ...report,
    identity: {
      ...NOVAID_IDENTITY_FALLBACK.identity,
      ...report,
      capabilities: Array.isArray(report.capabilities)
        ? report.capabilities
        : NOVAID_IDENTITY_FALLBACK.identity.capabilities,
      use_cases: Array.isArray(report.use_cases)
        ? report.use_cases
        : NOVAID_IDENTITY_FALLBACK.identity.use_cases,
      verification:
        report.verification && typeof report.verification === "object"
          ? {
              ...NOVAID_IDENTITY_FALLBACK.identity.verification,
              ...report.verification,
            }
          : NOVAID_IDENTITY_FALLBACK.identity.verification,
      sample_profile:
        report.sample_profile && typeof report.sample_profile === "object"
          ? {
              ...NOVAID_IDENTITY_FALLBACK.identity.sample_profile,
              ...report.sample_profile,
              reputation: Array.isArray(report.sample_profile.reputation)
                ? report.sample_profile.reputation
                : NOVAID_IDENTITY_FALLBACK.identity.sample_profile.reputation,
            }
          : NOVAID_IDENTITY_FALLBACK.identity.sample_profile,
      login_button:
        report.login_button && typeof report.login_button === "object"
          ? {
              ...NOVAID_IDENTITY_FALLBACK.identity.login_button,
              ...report.login_button,
              policy_gates: Array.isArray(report.login_button.policy_gates)
                ? report.login_button.policy_gates
                : NOVAID_IDENTITY_FALLBACK.identity.login_button.policy_gates,
            }
          : NOVAID_IDENTITY_FALLBACK.identity.login_button,
      metrics:
        report.metrics && typeof report.metrics === "object"
          ? {
              ...NOVAID_IDENTITY_FALLBACK.identity.metrics,
              ...report.metrics,
            }
          : NOVAID_IDENTITY_FALLBACK.identity.metrics,
    },
  };
}

function normalizeGenSovereign(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.gen_sovereign || payload.genSovereign || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVAID_GEN_SOVEREIGN_FALLBACK;
  }

  return {
    ...NOVAID_GEN_SOVEREIGN_FALLBACK,
    ...report,
    gen_sovereign: {
      ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign,
      ...report,
      core_layers: Array.isArray(report.core_layers)
        ? report.core_layers
        : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.core_layers,
      capabilities: Array.isArray(report.capabilities)
        ? report.capabilities
        : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.capabilities,
      identity:
        report.identity && typeof report.identity === "object"
          ? {
              ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.identity,
              ...report.identity,
              auth_flow: Array.isArray(report.identity.auth_flow)
                ? report.identity.auth_flow
                : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.identity.auth_flow,
            }
          : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.identity,
      government_integration:
        report.government_integration && typeof report.government_integration === "object"
          ? {
              ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.government_integration,
              ...report.government_integration,
              credential_types: Array.isArray(report.government_integration.credential_types)
                ? report.government_integration.credential_types
                : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.government_integration.credential_types,
            }
          : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.government_integration,
      crypto_finance:
        report.crypto_finance && typeof report.crypto_finance === "object"
          ? {
              ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.crypto_finance,
              ...report.crypto_finance,
              components: Array.isArray(report.crypto_finance.components)
                ? report.crypto_finance.components
                : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.crypto_finance.components,
              payment_stack: Array.isArray(report.crypto_finance.payment_stack)
                ? report.crypto_finance.payment_stack
                : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.crypto_finance.payment_stack,
            }
          : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.crypto_finance,
      federation:
        report.federation && typeof report.federation === "object"
          ? {
              ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.federation,
              ...report.federation,
              apis: Array.isArray(report.federation.apis)
                ? report.federation.apis
                : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.federation.apis,
            }
          : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.federation,
      ai_governance:
        report.ai_governance && typeof report.ai_governance === "object"
          ? {
              ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.ai_governance,
              ...report.ai_governance,
            }
          : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.ai_governance,
      dashboard:
        report.dashboard && typeof report.dashboard === "object"
          ? {
              ...NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.dashboard,
              ...report.dashboard,
            }
          : NOVAID_GEN_SOVEREIGN_FALLBACK.gen_sovereign.dashboard,
    },
  };
}

function normalizeDigitalNation(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.digital_nation || payload.digitalNation || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVAID_DIGITAL_NATION_FALLBACK;
  }

  return {
    ...NOVAID_DIGITAL_NATION_FALLBACK,
    ...report,
    digital_nation: {
      ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation,
      ...report,
      what_this_is: Array.isArray(report.what_this_is)
        ? report.what_this_is
        : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.what_this_is,
      what_this_is_not: Array.isArray(report.what_this_is_not)
        ? report.what_this_is_not
        : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.what_this_is_not,
      core_layers: Array.isArray(report.core_layers)
        ? report.core_layers
        : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.core_layers,
      capabilities: Array.isArray(report.capabilities)
        ? report.capabilities
        : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.capabilities,
      citizenship:
        report.citizenship && typeof report.citizenship === "object"
          ? {
              ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.citizenship,
              ...report.citizenship,
              profile:
                report.citizenship.profile && typeof report.citizenship.profile === "object"
                  ? {
                      ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.citizenship.profile,
                      ...report.citizenship.profile,
                      roles: Array.isArray(report.citizenship.profile.roles)
                        ? report.citizenship.profile.roles
                        : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.citizenship.profile.roles,
                    }
                  : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.citizenship.profile,
              tiers: Array.isArray(report.citizenship.tiers)
                ? report.citizenship.tiers
                : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.citizenship.tiers,
            }
          : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.citizenship,
      passport:
        report.passport && typeof report.passport === "object"
          ? {
              ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.passport,
              ...report.passport,
              sample:
                report.passport.sample && typeof report.passport.sample === "object"
                  ? {
                      ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.passport.sample,
                      ...report.passport.sample,
                      credentials: Array.isArray(report.passport.sample.credentials)
                        ? report.passport.sample.credentials
                        : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.passport.sample.credentials,
                    }
                  : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.passport.sample,
              capabilities: Array.isArray(report.passport.capabilities)
                ? report.passport.capabilities
                : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.passport.capabilities,
            }
          : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.passport,
      ssi:
        report.ssi && typeof report.ssi === "object"
          ? {
              ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.ssi,
              ...report.ssi,
              auth_flow: Array.isArray(report.ssi.auth_flow)
                ? report.ssi.auth_flow
                : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.ssi.auth_flow,
            }
          : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.ssi,
      governance:
        report.governance && typeof report.governance === "object"
          ? {
              ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.governance,
              ...report.governance,
              proposal_types: Array.isArray(report.governance.proposal_types)
                ? report.governance.proposal_types
                : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.governance.proposal_types,
            }
          : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.governance,
      ai_governance:
        report.ai_governance && typeof report.ai_governance === "object"
          ? {
              ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.ai_governance,
              ...report.ai_governance,
            }
          : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.ai_governance,
      dashboard:
        report.dashboard && typeof report.dashboard === "object"
          ? {
              ...NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.dashboard,
              ...report.dashboard,
            }
          : NOVAID_DIGITAL_NATION_FALLBACK.digital_nation.dashboard,
    },
  };
}

function normalizeDigitalConstitution(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.constitution || payload.digitalConstitution || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK;
  }

  return {
    ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK,
    ...report,
    constitution: {
      ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution,
      ...report,
      articles: Array.isArray(report.articles)
        ? report.articles
        : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.articles,
      amendment_process: Array.isArray(report.amendment_process)
        ? report.amendment_process
        : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.amendment_process,
      authority_structure:
        report.authority_structure && typeof report.authority_structure === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.authority_structure,
              ...report.authority_structure,
              authorities: Array.isArray(report.authority_structure.authorities)
                ? report.authority_structure.authorities
                : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.authority_structure.authorities,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.authority_structure,
      governance:
        report.governance && typeof report.governance === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.governance,
              ...report.governance,
              powers: Array.isArray(report.governance.powers)
                ? report.governance.powers
                : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.governance.powers,
              voting_model: Array.isArray(report.governance.voting_model)
                ? report.governance.voting_model
                : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.governance.voting_model,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.governance,
      economic_constitution:
        report.economic_constitution && typeof report.economic_constitution === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.economic_constitution,
              ...report.economic_constitution,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.economic_constitution,
      trust_verification_law:
        report.trust_verification_law && typeof report.trust_verification_law === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.trust_verification_law,
              ...report.trust_verification_law,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.trust_verification_law,
      contract_law:
        report.contract_law && typeof report.contract_law === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.contract_law,
              ...report.contract_law,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.contract_law,
      ai_governance_law:
        report.ai_governance_law && typeof report.ai_governance_law === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.ai_governance_law,
              ...report.ai_governance_law,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.ai_governance_law,
      dispute_resolution:
        report.dispute_resolution && typeof report.dispute_resolution === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.dispute_resolution,
              ...report.dispute_resolution,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.dispute_resolution,
      compliance_enforcement:
        report.compliance_enforcement && typeof report.compliance_enforcement === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.compliance_enforcement,
              ...report.compliance_enforcement,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.compliance_enforcement,
      guarantees:
        report.guarantees && typeof report.guarantees === "object"
          ? {
              ...NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.guarantees,
              ...report.guarantees,
            }
          : NOVARIDE_DIGITAL_CONSTITUTION_FALLBACK.constitution.guarantees,
    },
  };
}

function normalizeRegulatoryAlignment(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.regulatory_alignment || payload.regulatoryAlignment || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK;
  }

  return {
    ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK,
    ...report,
    regulatory_alignment: {
      ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment,
      ...report,
      alignment_model: Array.isArray(report.alignment_model)
        ? report.alignment_model
        : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.alignment_model,
      identity_compliance:
        report.identity_compliance && typeof report.identity_compliance === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.identity_compliance,
              ...report.identity_compliance,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.identity_compliance,
      payments_regulation:
        report.payments_regulation && typeof report.payments_regulation === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.payments_regulation,
              ...report.payments_regulation,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.payments_regulation,
      token_regulation:
        report.token_regulation && typeof report.token_regulation === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.token_regulation,
              ...report.token_regulation,
              classification_model: Array.isArray(report.token_regulation.classification_model)
                ? report.token_regulation.classification_model
                : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.token_regulation.classification_model,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.token_regulation,
      privacy_law:
        report.privacy_law && typeof report.privacy_law === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.privacy_law,
              ...report.privacy_law,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.privacy_law,
      cross_border_framework:
        report.cross_border_framework && typeof report.cross_border_framework === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.cross_border_framework,
              ...report.cross_border_framework,
              regions: Array.isArray(report.cross_border_framework.regions)
                ? report.cross_border_framework.regions
                : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.cross_border_framework.regions,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.cross_border_framework,
      liability_model:
        report.liability_model && typeof report.liability_model === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.liability_model,
              ...report.liability_model,
              responsibilities: Array.isArray(report.liability_model.responsibilities)
                ? report.liability_model.responsibilities
                : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.liability_model.responsibilities,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.liability_model,
      ai_regulation_compliance:
        report.ai_regulation_compliance && typeof report.ai_regulation_compliance === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.ai_regulation_compliance,
              ...report.ai_regulation_compliance,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.ai_regulation_compliance,
      compliance_engine:
        report.compliance_engine && typeof report.compliance_engine === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.compliance_engine,
              ...report.compliance_engine,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.compliance_engine,
      dashboard:
        report.dashboard && typeof report.dashboard === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.dashboard,
              ...report.dashboard,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.dashboard,
      properties:
        report.properties && typeof report.properties === "object"
          ? {
              ...NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.properties,
              ...report.properties,
            }
          : NOVARIDE_REGULATORY_ALIGNMENT_FALLBACK.regulatory_alignment.properties,
    },
  };
}

function normalizeGlobalExpansion(payload) {
  const report =
    payload && typeof payload === "object"
      ? payload.expansion || payload.globalExpansion || payload
      : null;

  if (!report || typeof report !== "object") {
    return NOVARIDE_GLOBAL_EXPANSION_FALLBACK;
  }

  return {
    ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK,
    ...report,
    expansion: {
      ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion,
      ...report,
      expansion_model: Array.isArray(report.expansion_model)
        ? report.expansion_model
        : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.expansion_model,
      phases: Array.isArray(report.phases)
        ? report.phases
        : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.phases,
      country_entry_playbook:
        report.country_entry_playbook && typeof report.country_entry_playbook === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.country_entry_playbook,
              ...report.country_entry_playbook,
              regulatory_mapping: Array.isArray(report.country_entry_playbook.regulatory_mapping)
                ? report.country_entry_playbook.regulatory_mapping
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.country_entry_playbook.regulatory_mapping,
              legal_structure: Array.isArray(report.country_entry_playbook.legal_structure)
                ? report.country_entry_playbook.legal_structure
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.country_entry_playbook.legal_structure,
              partnership_model: Array.isArray(report.country_entry_playbook.partnership_model)
                ? report.country_entry_playbook.partnership_model
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.country_entry_playbook.partnership_model,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.country_entry_playbook,
      novaid_deployment:
        report.novaid_deployment && typeof report.novaid_deployment === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novaid_deployment,
              ...report.novaid_deployment,
              basic_id: Array.isArray(report.novaid_deployment.basic_id)
                ? report.novaid_deployment.basic_id
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novaid_deployment.basic_id,
              verified_id: Array.isArray(report.novaid_deployment.verified_id)
                ? report.novaid_deployment.verified_id
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novaid_deployment.verified_id,
              trusted_id: Array.isArray(report.novaid_deployment.trusted_id)
                ? report.novaid_deployment.trusted_id
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novaid_deployment.trusted_id,
              government_integration_path: Array.isArray(report.novaid_deployment.government_integration_path)
                ? report.novaid_deployment.government_integration_path
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novaid_deployment.government_integration_path,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novaid_deployment,
      novapay_deployment:
        report.novapay_deployment && typeof report.novapay_deployment === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novapay_deployment,
              ...report.novapay_deployment,
              partner_based: Array.isArray(report.novapay_deployment.partner_based)
                ? report.novapay_deployment.partner_based
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novapay_deployment.partner_based,
              licensed_later: Array.isArray(report.novapay_deployment.licensed_later)
                ? report.novapay_deployment.licensed_later
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novapay_deployment.licensed_later,
              multi_currency_rollout: Array.isArray(report.novapay_deployment.multi_currency_rollout)
                ? report.novapay_deployment.multi_currency_rollout
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novapay_deployment.multi_currency_rollout,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.novapay_deployment,
      token_strategy:
        report.token_strategy && typeof report.token_strategy === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.token_strategy,
              ...report.token_strategy,
              launch_model: Array.isArray(report.token_strategy.launch_model)
                ? report.token_strategy.launch_model
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.token_strategy.launch_model,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.token_strategy,
      dao_structure:
        report.dao_structure && typeof report.dao_structure === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.dao_structure,
              ...report.dao_structure,
              model: Array.isArray(report.dao_structure.model)
                ? report.dao_structure.model
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.dao_structure.model,
              why_it_matters: Array.isArray(report.dao_structure.why_it_matters)
                ? report.dao_structure.why_it_matters
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.dao_structure.why_it_matters,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.dao_structure,
      cross_border_architecture:
        report.cross_border_architecture && typeof report.cross_border_architecture === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.cross_border_architecture,
              ...report.cross_border_architecture,
              compliance_engine: Array.isArray(report.cross_border_architecture.compliance_engine)
                ? report.cross_border_architecture.compliance_engine
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.cross_border_architecture.compliance_engine,
              region_examples: Array.isArray(report.cross_border_architecture.region_examples)
                ? report.cross_border_architecture.region_examples
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.cross_border_architecture.region_examples,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.cross_border_architecture,
      ai_alignment:
        report.ai_alignment && typeof report.ai_alignment === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.ai_alignment,
              ...report.ai_alignment,
              requirements: Array.isArray(report.ai_alignment.requirements)
                ? report.ai_alignment.requirements
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.ai_alignment.requirements,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.ai_alignment,
      go_to_market:
        report.go_to_market && typeof report.go_to_market === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.go_to_market,
              ...report.go_to_market,
              entry_model: Array.isArray(report.go_to_market.entry_model)
                ? report.go_to_market.entry_model
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.go_to_market.entry_model,
              growth_strategy: Array.isArray(report.go_to_market.growth_strategy)
                ? report.go_to_market.growth_strategy
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.go_to_market.growth_strategy,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.go_to_market,
      risk_management:
        report.risk_management && typeof report.risk_management === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.risk_management,
              ...report.risk_management,
              top_risks: Array.isArray(report.risk_management.top_risks)
                ? report.risk_management.top_risks
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.risk_management.top_risks,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.risk_management,
      dashboard:
        report.dashboard && typeof report.dashboard === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.dashboard,
              ...report.dashboard,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.dashboard,
      execution_blueprint:
        report.execution_blueprint && typeof report.execution_blueprint === "object"
          ? {
              ...NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint,
              ...report.execution_blueprint,
              hub_model: Array.isArray(report.execution_blueprint.hub_model)
                ? report.execution_blueprint.hub_model
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint.hub_model,
              phase_sequence: Array.isArray(report.execution_blueprint.phase_sequence)
                ? report.execution_blueprint.phase_sequence
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint.phase_sequence,
              ninety_day_plan: Array.isArray(report.execution_blueprint.ninety_day_plan)
                ? report.execution_blueprint.ninety_day_plan
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint.ninety_day_plan,
              novaid_rollout: Array.isArray(report.execution_blueprint.novaid_rollout)
                ? report.execution_blueprint.novaid_rollout
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint.novaid_rollout,
              novapay_rollout: Array.isArray(report.execution_blueprint.novapay_rollout)
                ? report.execution_blueprint.novapay_rollout
                : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint.novapay_rollout,
            }
          : NOVARIDE_GLOBAL_EXPANSION_FALLBACK.expansion.execution_blueprint,
    },
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

function formatInteger(value, fallback = 0) {
  return new Intl.NumberFormat("en-AU").format(Math.max(0, Math.round(toNumber(value, fallback))));
}

function formatCurrency(value, fallback = 0) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: 0,
  }).format(Math.max(0, Math.round(toNumber(value, fallback))));
}

function percentValue(numerator, denominator, fallback = 0) {
  const top = toNumber(numerator, 0);
  const bottom = toNumber(denominator, 0);
  if (bottom <= 0) {
    return fallback;
  }
  return clampNumber((top / bottom) * 100, 0, 100);
}

function deriveNovaRideOperationsSurface({
  state,
  liveAnalyticsSnapshot,
  analyticsTrail,
  liveNotifications,
  operationAIDecisionState,
  operatorDemandForecast,
  operatorStrategyEngine,
  operatorBusinessPricing,
  operatorCityProfitOptimization,
  operatorAutonomy,
  liveConnection,
  liveEvents,
}) {
  const liveRides = Math.max(
    state.activeRides.length,
    toNumber(liveAnalyticsSnapshot.activeRidesCount, 0),
    toNumber(state.systemHealth?.active_rides, 0),
  );
  const activeDrivers = Math.max(
    state.drivers.filter((driver) => String(driver.status).toUpperCase() === "ONLINE").length,
    toNumber(liveAnalyticsSnapshot.onlineDrivers, 0),
    toNumber(liveAnalyticsSnapshot.activeDrivers, 0),
    toNumber(state.systemHealth?.drivers_online, 0),
    toNumber(state.trustMetrics?.active_drivers, 0),
  );
  const totalDrivers = Math.max(
    state.drivers.length,
    toNumber(liveAnalyticsSnapshot.driverCount, 0),
    toNumber(state.systemHealth?.total_drivers, activeDrivers),
    activeDrivers,
  );
  const completedRides = Math.max(
    toNumber(liveAnalyticsSnapshot.completedRides, 0),
    toNumber(state.pilotMetrics?.completed_rides, 0),
    toNumber(state.pilotMetrics?.verified_rides_today, 0),
    toNumber(state.systemHealth?.completed_rides, 0),
  );
  const bookingsToday = Math.max(
    toNumber(liveAnalyticsSnapshot.totalRides, 0),
    toNumber(state.pilotMetrics?.total_rides, 0),
    completedRides + liveRides,
  );
  const trustScore = clampNumber(
    toNumber(
      state.trustMetrics?.fleet_trust_score ??
        state.trustMetrics?.trust_score ??
        liveAnalyticsSnapshot.trustScore,
      100,
    ),
    0,
    100,
  );
  const completionRate = percentValue(completedRides || bookingsToday - liveRides, bookingsToday, trustScore);
  const evidenceCoverage = clampNumber(toNumber(liveAnalyticsSnapshot.evidenceCoverage, 100), 0, 100);
  const utilization = percentValue(activeDrivers, totalDrivers, activeDrivers > 0 ? 78 : 0);
  const estimatedRevenue = Math.max(
    toNumber(state.pilotMetrics?.revenue_today, 0),
    toNumber(state.pilotMetrics?.gross_booking_value, 0),
    bookingsToday * 23,
  );
  const payoutEstimate = Math.round(estimatedRevenue * 0.72);
  const pendingEstimate = Math.round(estimatedRevenue * 0.09);
  const verifiedDrivers = Math.round(totalDrivers * (trustScore / 100));
  const verifiedRides = Math.round(bookingsToday * (evidenceCoverage / 100));
  const openIncidents = Math.max(
    state.guards.length,
    toNumber(liveAnalyticsSnapshot.alertCount, 0),
    toNumber(liveAnalyticsSnapshot.exceptionCount, 0),
  );
  const requestsQueue = Math.max(
    liveRides,
    toNumber(state.observabilityDashboard?.queue_depth, 0),
    toNumber(operatorDemandForecast?.forecast?.request_queue, 0),
    Math.round(bookingsToday * 0.08),
  );
  const busyDrivers = Math.min(totalDrivers, Math.max(liveRides, Math.round(activeDrivers * 0.37)));
  const availableDrivers = Math.max(0, activeDrivers - busyDrivers);
  const offlineDrivers = Math.max(0, totalDrivers - activeDrivers);
  const atRiskDrivers = Math.min(
    totalDrivers,
    Math.max(
      openIncidents,
      toNumber(operatorAutonomy?.driver_risk?.at_risk_drivers, 0),
      operationAIDecisionState?.safetyGate === "hold" ? 1 : 0,
    ),
  );
  const trendSeed = analyticsTrail.length > 0 ? analyticsTrail : [liveAnalyticsSnapshot];
  const chartValues = trendSeed
    .slice(-12)
    .map((point, index) =>
      clampNumber(
        Math.round(
          toNumber(point.totalRides, bookingsToday) +
            toNumber(point.activeDrivers, activeDrivers) * 0.35 +
            index * 4,
        ),
        12,
        128,
      ),
    );
  const normalizedChartValues =
    chartValues.length >= 6
      ? chartValues
      : [...[42, 54, 49, 64, 72, 81].slice(0, 6 - chartValues.length), ...chartValues];

  const dynamicActivity = state.activeRides.slice(0, 3).map((ride, index) => ({
    time: liveAnalyticsSnapshot.timestamp || "live",
    event: index === 0 ? "New ride accepted" : "Ride picked up",
    actor: ride.rideId || ride.driverId || `RIDE-${index + 1}`,
    value: ride.driverId || ride.state || "assigned",
    tone: "success",
  }));

  return {
    kpis: [
      { label: "Live Rides", value: formatInteger(liveRides), trend: liveRides > 0 ? "live" : "standby", detail: "active trips now", chart: [32, 44, 38, 52, 61, 58, 72] },
      { label: "Active Drivers", value: formatInteger(activeDrivers), trend: `${Math.round(utilization)}%`, detail: "online supply", chart: [24, 31, 36, 42, 48, 55, activeDrivers || 58] },
      { label: "Requests Queue", value: formatInteger(requestsQueue), trend: operationAIDecisionState?.demandLabel || "Stable", detail: "dispatch intake", chart: [12, 18, 24, 20, 32, 38, requestsQueue || 34] },
      { label: "Bookings Today", value: formatInteger(bookingsToday), trend: `${Math.round(completionRate)}%`, detail: "completed + active", chart: [28, 46, 40, 68, 82, 76, bookingsToday || 88] },
      { label: "Revenue", value: formatCurrency(estimatedRevenue), trend: "gross", detail: "booking value", chart: [20, 34, 48, 54, 72, 86, 104] },
      { label: "Incident Count", value: formatInteger(openIncidents), trend: operationAIDecisionState?.safetyGate || "pass", detail: "open risk signals", chart: [2, 1, 3, 2, 4, 2, openIncidents] },
    ],
    clusters: NOVARIDE_MAP_CLUSTERS.map((cluster, index) => ({
      ...cluster,
      count: Math.max(8, Math.round((liveRides || bookingsToday || cluster.count) / (index + 2))),
    })),
    drivers: NOVARIDE_MAP_DRIVERS.map((driver, index) => ({
      ...driver,
      id: state.drivers[index]?.driverId || driver.id,
      status:
        index < atRiskDrivers
          ? "at-risk"
          : index < availableDrivers
          ? "available"
          : index < availableDrivers + busyDrivers
            ? "busy"
            : "offline",
    })),
    activity: [...dynamicActivity, ...NOVARIDE_ACTIVITY_FEED].slice(0, 5),
    alerts: [
      ...liveNotifications.slice(0, 2).map((notification) => ({
        title: notification.title,
        detail: notification.detail,
        severity: notification.severity === "critical" ? "critical" : "warning",
      })),
      ...NOVARIDE_OPERATION_ALERTS,
    ].slice(0, 3),
    chartValues: normalizedChartValues,
    fleet: [
      { label: "Available", value: formatInteger(availableDrivers), percent: `${Math.round(percentValue(availableDrivers, totalDrivers, 0))}%` },
      { label: "Busy", value: formatInteger(busyDrivers), percent: `${Math.round(percentValue(busyDrivers, totalDrivers, 0))}%` },
      { label: "Offline", value: formatInteger(offlineDrivers), percent: `${Math.round(percentValue(offlineDrivers, totalDrivers, 0))}%` },
      { label: "At Risk", value: formatInteger(atRiskDrivers), percent: `${Math.round(percentValue(atRiskDrivers, totalDrivers, 0))}%` },
      { label: "Utilization Rate", value: `${utilization.toFixed(1)}%`, percent: "citywide" },
    ],
    payments: [
      { label: "Revenue", value: formatCurrency(estimatedRevenue) },
      { label: "Payouts", value: formatCurrency(payoutEstimate) },
      { label: "Pending", value: formatCurrency(pendingEstimate) },
    ],
    trustSafety: [
      { label: "Trust Score", value: `${trustScore.toFixed(1)} / 100` },
      { label: "Verified Drivers", value: `${formatInteger(verifiedDrivers)} / ${formatInteger(totalDrivers)}` },
      { label: "Verified Rides", value: `${formatInteger(verifiedRides)} / ${formatInteger(bookingsToday)}` },
      { label: "Open Incidents", value: formatInteger(openIncidents) },
    ],
    rideControl: {
      rideId: state.activeRides[0]?.rideId || "ride-67231",
      passenger: state.activeRides[0]?.riderId || "rider-demo-001",
      driver: state.activeRides[0]?.driverId || "DRV-104",
      route: "Kampala Road -> Nakasero",
      eta: operationAIDecisionState?.demandPressure >= 70 ? "7 min" : "4 min",
      distance: "3.8 km",
      fare: formatCurrency(estimatedRevenue / Math.max(bookingsToday, 1), 23),
      status: state.activeRides[0]?.state || "in_progress",
    },
    aiLayer: [
      {
        title: "Demand Prediction",
        value: operatorDemandForecast?.forecast?.demand_label || operationAIDecisionState?.demandLabel || "Stable",
        detail: operatorDemandForecast?.forecast?.instruction || operationAIDecisionState?.dispatchPosture || "Maintain current dispatch band.",
      },
      {
        title: "Surge Recommendation",
        value: operatorBusinessPricing?.pricing?.pricing_posture || "balanced",
        detail: operatorBusinessPricing?.pricing?.explanation || "No manual surge is required in the current trust window.",
      },
      {
        title: "Driver Risk Scoring",
        value: `${formatInteger(atRiskDrivers)} at risk`,
        detail: operationAIDecisionState?.operatorMove || "Continue monitoring driver risk against replay and incident pressure.",
      },
      {
        title: "Fraud Detection",
        value: openIncidents > 0 ? "Review" : "Clear",
        detail: openIncidents > 0 ? "Open incidents require operator acknowledgement." : "No fraud or payment anomaly is active.",
      },
    ],
    quickActions: [
      { label: "Broadcast", detail: "Message online drivers" },
      { label: "Incentives", detail: "driver supply plan" },
      { label: "Heat Map", detail: "demand overlay" },
      { label: "Reports", detail: "export audit packet" },
      { label: "Trigger Surge", detail: operatorBusinessPricing?.pricing?.pricing_posture || "balanced" },
      { label: "Heatmap Boost", detail: operatorDemandForecast?.forecast?.target_zone || "highest demand zone" },
      { label: "Incident Mode", detail: operationAIDecisionState?.safetyGate || "pass" },
      { label: "Lock Zone", detail: "senior operator" },
      { label: "Unlock Zone", detail: "audit logged" },
    ],
    realtime: [
      { label: "WebSocket", value: liveConnection || "connecting", detail: "/ws/map/live/" },
      { label: "Map refresh", value: "<500ms", detail: "driver clusters + heatmap" },
      { label: "KPI refresh", value: "<2s", detail: "operator metrics window" },
      { label: "Events", value: formatInteger(liveEvents?.length || 0), detail: "ride_update / incident_reported" },
    ],
    trustReplay: [
      { label: "Ride playback", value: liveAnalyticsSnapshot.replayFailures > 0 ? "Review" : "Ready" },
      { label: "GPS replay", value: liveAnalyticsSnapshot.missingTraces > 0 ? "Partial" : "Synced" },
      { label: "Action audit trail", value: operationAIDecisionState?.executionTier || "advisory" },
      { label: "RBAC", value: "operator role enforced" },
    ],
    backendModules: NOVARIDE_OPERATOR_BACKEND_MODULES,
    rbac: NOVARIDE_OPERATOR_RBAC,
    analytics: {
      completionRate,
      utilization,
      evidenceCoverage,
      projectedProfit:
        operatorCityProfitOptimization?.profit_optimization?.projected_profit ||
        formatCurrency(Math.round(estimatedRevenue * 0.18)),
      strategy:
        operatorStrategyEngine?.strategy?.strategy_posture ||
        operatorStrategyEngine?.decision?.decision_lane ||
        operationAIDecisionState?.lane ||
        "observe",
    },
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
  const [trustJourneyActive, setTrustJourneyActive] = useState(false);
  const [trustJourneyStep, setTrustJourneyStep] = useState(0);
  const [trustScoreExpanded, setTrustScoreExpanded] = useState(false);
  const [engineeringJourneyActive, setEngineeringJourneyActive] = useState(false);
  const [engineeringJourneyStep, setEngineeringJourneyStep] = useState(0);

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

  useEffect(() => {
    if (!trustJourneyActive || trustJourneyStep >= RIDE_REPLAY_STEPS.length) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      setTrustJourneyStep((current) => Math.min(current + 1, RIDE_REPLAY_STEPS.length));
    }, 900);
    return () => window.clearTimeout(timer);
  }, [trustJourneyActive, trustJourneyStep]);

  useEffect(() => {
    if (!engineeringJourneyActive || engineeringJourneyStep >= NOVACODEPRO_ENGINEERING_JOURNEY.length) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      setEngineeringJourneyStep((current) =>
        Math.min(current + 1, NOVACODEPRO_ENGINEERING_JOURNEY.length),
      );
    }, 850);
    return () => window.clearTimeout(timer);
  }, [engineeringJourneyActive, engineeringJourneyStep]);

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
        partnerGovernanceResult,
        novapayLiveTestReadinessResult,
        treasuryIntelligenceResult,
        globalTreasuryIntelligenceResult,
        daoEconomyResult,
        appStoreResult,
        protocolMarketplaceResult,
        superAppResult,
        novaidIdentityResult,
        novaidGenSovereignResult,
        novaidDigitalNationResult,
        novarideDigitalConstitutionResult,
        novarideRegulatoryAlignmentResult,
        novarideGlobalExpansionResult,
        architectureProtocolMarketplaceResult,
        novarideEcosystemResult,
        novaridePlatformArchitectureContractResult,
        architectureComplianceResult,
        architectureRemediationResult,
        architectureLearningResult,
        architecturePredictiveResult,
        architectureAutonomousResult,
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
        readJson("/v1/trust/orgs"),
        readJson("/v1/core-platform/transfers/live-test/readiness"),
        readJson("/v1/treasury/intelligence"),
        readJson("/v1/treasury/global-intelligence"),
        readJson("/v1/economy/protocol"),
        readJson("/v1/novaride/appstore/apps"),
        readJson("/v1/novaride/developer/marketplace"),
        readJson("/v1/novaride/super-app"),
        readJson("/v1/novaride/novaid"),
        readJson("/v1/novaride/novaid/gen-sovereign"),
        readJson("/v1/novaride/novaid/digital-nation"),
        readJson("/v1/novaride/constitution"),
        readJson("/v1/novaride/regulatory-alignment"),
        readJson("/v1/novaride/global-expansion"),
        readJson("/v1/architecture/protocol-marketplace"),
        readJson("/v1/novaride/ecosystem"),
        readJson("/v1/novaride/platform/architecture-contract"),
        readJson("/v1/architecture/compliance"),
        readJson("/v1/architecture/remediation"),
        readJson("/v1/architecture/learning"),
        readJson("/v1/architecture/predictive-governance"),
        readJson("/v1/architecture/autonomous-governance"),
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
      const novatechPartnerGovernance =
        partnerGovernanceResult.status === "fulfilled"
          ? partnerGovernanceResult.value
          : state.novatechPartnerGovernance;
      const novapayLiveTestReadiness =
        novapayLiveTestReadinessResult.status === "fulfilled"
          ? novapayLiveTestReadinessResult.value
          : state.novapayLiveTestReadiness;
      const novapayTreasuryIntelligence =
        treasuryIntelligenceResult.status === "fulfilled"
          ? normalizeTreasuryIntelligence(treasuryIntelligenceResult.value)
          : normalizeTreasuryIntelligence(state.novapayTreasuryIntelligence);
      const novapayGlobalTreasuryIntelligence =
        globalTreasuryIntelligenceResult.status === "fulfilled"
          ? normalizeGlobalTreasuryIntelligence(globalTreasuryIntelligenceResult.value)
          : normalizeGlobalTreasuryIntelligence(state.novapayGlobalTreasuryIntelligence);
      const novarideDaoEconomy =
        daoEconomyResult.status === "fulfilled"
          ? normalizeDaoEconomy(daoEconomyResult.value)
          : normalizeDaoEconomy(state.novarideDaoEconomy);
      const novarideAppStore =
        appStoreResult.status === "fulfilled"
          ? normalizeAppStore(appStoreResult.value)
          : normalizeAppStore(state.novarideAppStore);
      const novarideProtocolMarketplace =
        protocolMarketplaceResult.status === "fulfilled"
          ? normalizeProtocolMarketplace(protocolMarketplaceResult.value)
          : architectureProtocolMarketplaceResult.status === "fulfilled"
            ? normalizeProtocolMarketplace(architectureProtocolMarketplaceResult.value)
          : normalizeProtocolMarketplace(state.novarideProtocolMarketplace);
      const novarideSuperApp =
        superAppResult.status === "fulfilled"
          ? normalizeSuperApp(superAppResult.value)
          : normalizeSuperApp(state.novarideSuperApp);
      const novaidIdentity =
        novaidIdentityResult.status === "fulfilled"
          ? normalizeNovaID(novaidIdentityResult.value)
          : normalizeNovaID(state.novaidIdentity);
      const novaidGenSovereign =
        novaidGenSovereignResult.status === "fulfilled"
          ? normalizeGenSovereign(novaidGenSovereignResult.value)
          : normalizeGenSovereign(state.novaidGenSovereign);
      const novaidDigitalNation =
        novaidDigitalNationResult.status === "fulfilled"
          ? normalizeDigitalNation(novaidDigitalNationResult.value)
          : normalizeDigitalNation(state.novaidDigitalNation);
      const novarideDigitalConstitution =
        novarideDigitalConstitutionResult.status === "fulfilled"
          ? normalizeDigitalConstitution(novarideDigitalConstitutionResult.value)
          : normalizeDigitalConstitution(state.novarideDigitalConstitution);
      const novarideRegulatoryAlignment =
        novarideRegulatoryAlignmentResult.status === "fulfilled"
          ? normalizeRegulatoryAlignment(novarideRegulatoryAlignmentResult.value)
          : normalizeRegulatoryAlignment(state.novarideRegulatoryAlignment);
      const novarideGlobalExpansion =
        novarideGlobalExpansionResult.status === "fulfilled"
          ? normalizeGlobalExpansion(novarideGlobalExpansionResult.value)
          : normalizeGlobalExpansion(state.novarideGlobalExpansion);
      const novarideEcosystem =
        novarideEcosystemResult.status === "fulfilled"
          ? novarideEcosystemResult.value
          : state.novarideEcosystem;
      const novaridePlatformArchitectureContract =
        novaridePlatformArchitectureContractResult.status === "fulfilled"
          ? novaridePlatformArchitectureContractResult.value
          : state.novaridePlatformArchitectureContract;
      const architectureCompliance =
        architectureComplianceResult.status === "fulfilled"
          ? normalizeComplianceReport(architectureComplianceResult.value)
          : normalizeComplianceReport(state.architectureCompliance);
      const architectureRemediation =
        architectureRemediationResult.status === "fulfilled"
          ? normalizeRemediationReport(architectureRemediationResult.value)
          : normalizeRemediationReport(state.architectureRemediation);
      const architectureLearning =
        architectureLearningResult.status === "fulfilled"
          ? normalizeLearningReport(architectureLearningResult.value)
          : normalizeLearningReport(state.architectureLearning);
      const architecturePredictive =
        architecturePredictiveResult.status === "fulfilled"
          ? normalizePredictiveReport(architecturePredictiveResult.value)
          : normalizePredictiveReport(state.architecturePredictive);
      const architectureAutonomous =
        architectureAutonomousResult.status === "fulfilled"
          ? normalizeAutonomousReport(architectureAutonomousResult.value)
          : normalizeAutonomousReport(state.architectureAutonomous);
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
        novatechPartnerGovernance,
        novapayLiveTestReadiness,
        novapayTreasuryIntelligence,
        novapayGlobalTreasuryIntelligence,
        novarideDaoEconomy,
        novarideAppStore,
        novarideProtocolMarketplace,
        novarideSuperApp,
        novaidIdentity,
        novaidGenSovereign,
        novaidDigitalNation,
        novarideDigitalConstitution,
        novarideRegulatoryAlignment,
        novarideGlobalExpansion,
        novarideEcosystem,
        novaridePlatformArchitectureContract,
        architectureCompliance,
        architectureRemediation,
        architectureLearning,
        architecturePredictive,
        architectureAutonomous,
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
  const novatechPartnerGovernance = state.novatechPartnerGovernance;
  const novapayLiveTestReadiness = state.novapayLiveTestReadiness;
  const novapayTreasuryIntelligence = normalizeTreasuryIntelligence(state.novapayTreasuryIntelligence);
  const novapayGlobalTreasuryIntelligence = normalizeGlobalTreasuryIntelligence(
    state.novapayGlobalTreasuryIntelligence,
  );
  const novarideDaoEconomy = normalizeDaoEconomy(state.novarideDaoEconomy);
  const novarideAppStore = normalizeAppStore(state.novarideAppStore);
  const novarideProtocolMarketplace = normalizeProtocolMarketplace(state.novarideProtocolMarketplace);
  const novarideSuperApp = normalizeSuperApp(state.novarideSuperApp);
  const novaidIdentity = normalizeNovaID(state.novaidIdentity);
  const novaidGenSovereign = normalizeGenSovereign(state.novaidGenSovereign);
  const novaidDigitalNation = normalizeDigitalNation(state.novaidDigitalNation);
  const novarideDigitalConstitution = normalizeDigitalConstitution(state.novarideDigitalConstitution);
  const novarideRegulatoryAlignment = normalizeRegulatoryAlignment(state.novarideRegulatoryAlignment);
  const novarideGlobalExpansion = normalizeGlobalExpansion(state.novarideGlobalExpansion);
  const novarideEcosystem = state.novarideEcosystem;
  const novarideArchitecture = novarideEcosystem?.architecture || {};
  const novarideLayeredArchitecture = Array.isArray(novarideArchitecture.layers)
    ? novarideArchitecture.layers
    : [];
  const novarideOperatorInterventionFlow = Array.isArray(novarideArchitecture.operator_intervention_flow)
    ? novarideArchitecture.operator_intervention_flow
    : [];
  const novarideMaturityDimensions = Array.isArray(novarideArchitecture.maturity_dimensions)
    ? novarideArchitecture.maturity_dimensions
    : [];
  const novarideEnterpriseOperationsLayer = Array.isArray(novarideArchitecture.enterprise_operations)
    ? novarideArchitecture.enterprise_operations
    : [];
  const novarideProductionInfrastructureReadiness = Array.isArray(novarideArchitecture.production_readiness)
    ? novarideArchitecture.production_readiness
    : [];
  const novarideEcosystemPlatform = novarideEcosystem?.ecosystem_platform || {};
  const novarideCompatibilityMatrix = Array.isArray(novarideEcosystemPlatform.compatibility_matrix)
    ? novarideEcosystemPlatform.compatibility_matrix
    : [];
  const novarideMigrationRegistry = Array.isArray(novarideEcosystemPlatform.migration_registry)
    ? novarideEcosystemPlatform.migration_registry
    : [];
  const novarideSdkRegistry = Array.isArray(novarideEcosystemPlatform.sdk_registry)
    ? novarideEcosystemPlatform.sdk_registry
    : [];
  const novarideOperationalMetrics =
    novarideEcosystemPlatform.operational_metrics &&
    typeof novarideEcosystemPlatform.operational_metrics === "object" &&
    !Array.isArray(novarideEcosystemPlatform.operational_metrics)
      ? Object.entries(novarideEcosystemPlatform.operational_metrics || {})
      : [];
  const novaridePlatformArchitectureContract = state.novaridePlatformArchitectureContract;
  const architectureCompliance = normalizeComplianceReport(state.architectureCompliance);
  const architectureRemediation = normalizeRemediationReport(state.architectureRemediation);
  const architectureLearning = normalizeLearningReport(state.architectureLearning);
  const architecturePredictive = normalizePredictiveReport(state.architecturePredictive);
  const architectureAutonomous = normalizeAutonomousReport(state.architectureAutonomous);
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
  const novaRideOperationsSurface = useMemo(
    () =>
      deriveNovaRideOperationsSurface({
        state,
        liveAnalyticsSnapshot,
        analyticsTrail,
        liveNotifications,
        operationAIDecisionState,
        operatorDemandForecast,
        operatorStrategyEngine,
        operatorBusinessPricing,
        operatorCityProfitOptimization,
        operatorAutonomy,
        liveConnection,
        liveEvents,
      }),
    [
      state,
      liveAnalyticsSnapshot,
      analyticsTrail,
      liveNotifications,
      operationAIDecisionState,
      operatorDemandForecast,
      operatorStrategyEngine,
      operatorBusinessPricing,
      operatorCityProfitOptimization,
      operatorAutonomy,
      liveConnection,
      liveEvents,
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
      <header className="os-topbar" aria-label="AfriTechnology navigation">
        <div>
          <strong>AFRITECHNOLOGY</strong>
          <span>NovaTech Platform</span>
        </div>
        <label className="os-search">
          <span>Search product, proof, route</span>
          <input defaultValue="NovaTrust" aria-label="Search product, proof, route" />
        </label>
        <div className="verified-lock">Trust OS online</div>
      </header>

      <section className="section-band novatech-home-band nextgen-hero-band" id="home">
        <div className="pilot-badge">PRR Complete · Public Pilot</div>
        <div className="novatech-home-grid">
          <div className="hero-copy">
            <p className="eyebrow">The Trust Operating System for Africa and Emerging Markets</p>
            <h1>Trusted Infrastructure for Mobility, Payments, Identity and AI Operations</h1>
            <p className="hero-summary">
              AfriTechnology builds trusted digital infrastructure for mobility,
              payments, identity, and AI-powered operations. Every ride, every
              payment, and every decision can be proven, replayed, and audited.
            </p>
            <div className="hero-actions" aria-label="NovaTech navigation">
              <a className="button primary" href="#platform">
                View Platform
              </a>
              <a className="button secondary" href="#contact">
                Start Pilot
              </a>
              <a className="button secondary" href="#trust-journey">
                View Replay Demo
              </a>
              <a className="button secondary" href="#trust-center">
                Trust Center
              </a>
            </div>
          </div>

          <div className="hero-trust-visual" aria-label="AfriTechnology trust operating system diagram">
            <div className="hero-node hero-node-core">AfriTechnology</div>
            <div className="hero-node hero-node-id">NovaID</div>
            <div className="hero-node hero-node-ride">NovaRide</div>
            <div className="hero-node hero-node-pay">NovaPay</div>
            <div className="hero-node hero-node-trust">NovaTrust</div>
            <div className="hero-node hero-node-ai">NovaAI</div>
            <div className="hero-trust-score">Trust Score 98.7%</div>
            <svg className="hero-flow-lines" viewBox="0 0 520 380" role="presentation" aria-hidden="true">
              <path d="M260 84 L140 154 L158 252 L260 305 L374 252 L390 154 Z" />
              <path d="M140 154 L260 84 L390 154 L374 252 L260 305 L158 252 Z" />
              <path d="M260 84 L260 305" />
              <path d="M140 154 L390 154" />
              <path d="M158 252 L374 252" />
            </svg>
            <div className="hero-flow-strip">
              {HERO_FLOW_STEPS.map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
          </div>
        </div>
        <div className="platform-status-strip">
          {PLATFORM_STATUS.map((item) => (
            <div key={item.system} className={`status-pill status-pill-${item.tone}`}>
              <span>{item.system}</span>
              <strong>{item.value}</strong>
              <em>{item.state}</em>
            </div>
          ))}
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

      <section className="section-band platform-band" id="platform">
        <SectionIntro
          eyebrow="Platform Architecture"
          title="One platform, six trust products"
          question="AfriTechnology is the company. NovaTech is the platform. NovaRide, NovaPay, NovaID, NovaTrust, NovaAI, and NovaCodePro are the product layers."
        />
        <div className="platform-map">
          <div className="platform-map-root">
            <span>Company</span>
            <strong>AfriTechnology</strong>
          </div>
          <div className="platform-map-line" aria-hidden="true" />
          <div className="platform-map-root platform-map-platform">
            <span>Platform</span>
            <strong>NovaTech Platform</strong>
          </div>
          <div className="interactive-ecosystem" id="products">
            {PLATFORM_PRODUCTS.map((product) => (
              <article key={product.name} className={`ecosystem-product ecosystem-product-${product.name.toLowerCase()}`}>
                <div className="record-card-header">
                  <strong>{product.name}</strong>
                  <span>{product.purpose}</span>
                </div>
                <p>{product.useCases.join(" • ")}</p>
                <div className="ecosystem-hover">
                  {(PLATFORM_HOVER_FEATURES[product.name] || product.features).map((feature) => (
                    <span key={feature} className="surface-chip">{feature}</span>
                  ))}
                </div>
                <div className="record-card-footer">
                  {product.industries.join(" / ")} · Docs {product.docs}
                </div>
              </article>
            ))}
            <div className="ecosystem-center">
              <span>Flow</span>
              <strong>Identity → Operations → Payments → Evidence → AI Insights</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="section-band audience-band" id="solutions">
        <SectionIntro
          eyebrow="Customer Journey"
          title="From problem to proof to pilot"
          question="The website now starts with customer outcomes before exposing the full operator dashboard and engineering depth."
        />
        <div className="journey-row">
          {["Problem", "Solution", "Products", "Proof", "Pilot", "Contact"].map((step) => (
            <span key={step}>{step}</span>
          ))}
        </div>
        <div className="audience-grid">
          {AUDIENCE_PORTALS.map((portal) => (
            <article key={portal.audience} className="operator-panel audience-card">
              <h3>{portal.audience}</h3>
              <p>{portal.promise}</p>
              <div className="chip-row">
                {portal.capabilities.map((capability) => (
                  <span key={capability} className="surface-chip">{capability}</span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band proof-band" id="trust-journey">
        <SectionIntro
          eyebrow="Live Trust Journey"
          title="Watch a ride become verified evidence"
          question="The signature demo shows identity, mobility, payment, evidence, and AI trust controls in one short journey."
        />
        <div className="journey-control-row">
          <button
            type="button"
            className="button primary"
            onClick={() => {
              setTrustJourneyActive(true);
              setTrustJourneyStep(0);
            }}
          >
            ▶ Start Trust Journey
          </button>
          <span>{trustJourneyActive && trustJourneyStep >= RIDE_REPLAY_STEPS.length ? "Trust Score: 98.7% · Evidence Complete · Replay Verified · Audit Ready" : "Ready to generate proof"}</span>
        </div>
        <div className="replay-demo">
          {RIDE_REPLAY_STEPS.map((step, index) => (
            <article
              key={step.step}
              className={`replay-step ${trustJourneyStep >= index + 1 ? "replay-step-active" : ""}`}
            >
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{step.step}</strong>
              <p>{step.proof}</p>
              <em>{step.product}</em>
            </article>
          ))}
        </div>
        <div className="trust-score-panel" id="trust-score">
          <div>
            <p className="eyebrow">Signature Feature</p>
            <h3>Transaction Trust Score</h3>
            <p>
              Calculated from live evidence: identity confidence, device binding,
              replay integrity, event completeness, and audit coverage.
            </p>
            <button
              type="button"
              className="button secondary"
              onClick={() => setTrustScoreExpanded((current) => !current)}
            >
              {trustScoreExpanded ? "Hide score evidence" : "Expand score evidence"}
            </button>
          </div>
          <div>
            <div className="trust-score-number">
              <span>Trust Score</span>
              <strong>98.7</strong>
            </div>
            {trustScoreExpanded && (
              <div className="trust-score-grid">
                {TRUST_SCORE_DETAILS.map((item) => (
                  <div key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="section-band global-band" id="global">
        <SectionIntro
          eyebrow="Global Expansion"
          title="From public pilot to regional trust infrastructure"
          question="The global presence map shows current footprint, next markets, and partnership strategy for investors and enterprise partners."
        />
        <div className="global-map-panel">
          <div className="global-map">
            {GLOBAL_PRESENCE.map((market) => (
              <div
                key={market.market}
                className={`map-pin map-pin-${market.tone}`}
                style={{ left: `${market.x}%`, top: `${market.y}%` }}
              >
                <span />
                <strong>{market.market}</strong>
                <em>{market.status}</em>
              </div>
            ))}
          </div>
          <div className="global-legend">
            <span><i className="legend-active" /> Active</span>
            <span><i className="legend-pilot" /> Pilot</span>
            <span><i className="legend-partner" /> Partnership</span>
            <span><i className="legend-future" /> Future market</span>
          </div>
        </div>
      </section>

      <section className="section-band pilot-band" id="pilots">
        <SectionIntro
          eyebrow="Pilot Evidence"
          title="Real pilot readiness, presented plainly"
          question="Enterprise and investor audiences need concrete proof before they need the full internal dashboard."
        />
        <div className="metric-grid pilot-metric-grid">
          {PILOT_METRICS.map((metric) => (
            <TrustMetric
              key={metric.label}
              label={metric.label}
              value={metric.value}
              helper="Controlled pilot registry evidence"
              tone="success"
            />
          ))}
        </div>
      </section>

      <section className="section-band case-study-band" id="case-studies">
        <SectionIntro
          eyebrow="Case Studies"
          title="Real trust problems, solved with evidence"
          question="Short proof stories make the platform understandable for enterprise buyers, operators, partners, and investors."
        />
        <div className="case-study-grid">
          {CASE_STUDIES.map((study) => (
            <article key={study.title} className="case-study-card">
              <strong>{study.title}</strong>
              <div><span>Problem</span><p>{study.problem}</p></div>
              <div><span>Solution</span><p>{study.solution}</p></div>
              <div><span>Result</span><p>{study.result}</p></div>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band trust-center-band" id="trust-center">
        <SectionIntro
          eyebrow="Trust Center"
          title="Security, governance, and compliance built into the platform"
          question="Deep governance language belongs here and in documentation, while the homepage keeps the customer story simple."
        />
        <div className="trust-center-grid">
          {TRUST_CENTER_PILLARS.map((pillar) => (
            <article key={pillar.title} className="operator-panel">
              <h3>{pillar.title}</h3>
              <div className="stack compact-stack">
                {pillar.items.map((item) => (
                  <div key={item} className="reason-chip reason-chip-success">{item}</div>
                ))}
              </div>
            </article>
          ))}
        </div>
        <div className="trust-page-grid">
          {TRUST_CENTER_PAGES.map((page) => (
            <a key={page.path} className="trust-page-card" href={page.path}>
              <span>{page.path}</span>
              <strong>{page.title}</strong>
              <p>{page.items.join(" · ")}</p>
            </a>
          ))}
        </div>
        <div className="operator-grid why-grid">
          {WHY_AFRITECHNOLOGY.map((pillar) => (
            <article key={pillar.title} className="record-card">
              <strong>{pillar.title}</strong>
              <p>{pillar.example}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band developers-band" id="developers">
        <SectionIntro
          eyebrow="Developers"
          title="APIs, SDKs, sandbox, and documentation"
          question="The developer portal is separated from marketing so builders can get started without reading investor or operator copy."
        />
        <div className="operator-grid">
          <OperatorPanel title="Documentation Portal">
            <p className="section-note">docs.afritechnology.com</p>
            <div className="docs-grid">
              {DOCS_PORTAL_SECTIONS.map((item) => (
                <div key={item} className="reason-chip reason-chip-success">{item}</div>
              ))}
            </div>
          </OperatorPanel>
          <OperatorPanel title="NovaAI Experience">
            <p className="section-note">AI recommends. Humans approve.</p>
            <div className="chip-row">
              {["Operational Assistant", "Payment Insights", "Fleet Insights", "Risk Insights", "Support Intelligence"].map((item) => (
                <span key={item} className="surface-chip">{item}</span>
              ))}
            </div>
          </OperatorPanel>
        </div>
      </section>

      <section className="section-band novacodepro-band" id="novacodepro">
        <div className="novacodepro-hero">
          <div>
            <p className="eyebrow">NovaCodePro X</p>
            <h2>Build. Govern. Deploy. Verify.</h2>
            <p>
              NovaCodePro X is the Engineering Operating System powering
              NovaRide, NovaPay, NovaID, NovaTrust, NovaAI, internal apps,
              partner applications, and third-party integrations.
            </p>
            <div className="chip-row">
              {NOVACODEPRO_TARGET_USERS.map((user) => (
                <span key={user} className="surface-chip">{user}</span>
              ))}
            </div>
          </div>
          <div className="novacodepro-command-panel">
            <div className="record-card-header">
              <strong>Engineering Control Plane</strong>
              <span>governed delivery</span>
            </div>
            <div className="codepro-flow">
              {["Build", "Govern", "Deploy", "Verify"].map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
            <pre>{`nova codepro run --workspace mobility-api
  checks: ai_review, sast, tests, replay
  deploy: controlled
  evidence: generated`}</pre>
          </div>
        </div>

        <SectionIntro
          eyebrow="Operating System Architecture"
          title="From developer product to full engineering OS"
          question="NovaCodePro X converges source control, cloud workspaces, AI engineering, CI/CD, deployments, monitoring, security, documentation, marketplace, and governance."
        />
        <div className="codepro-os-map">
          <div className="codepro-os-core">
            <span>Engineering OS</span>
            <strong>NovaCodePro</strong>
          </div>
          {NOVACODEPRO_X_MODULES.map((module) => (
            <article key={module.name} className="codepro-os-module">
              <div className="record-card-header">
                <strong>{module.name}</strong>
                <span>{module.role}</span>
              </div>
              <div className="chip-row">
                {module.features.map((feature) => (
                  <span key={feature} className="surface-chip">{feature}</span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <div className="codepro-workspace-grid">
          <OperatorPanel title="NovaCloud IDE Workspace">
            <pre className="workspace-tree">{`workspace/
├── source
├── tests
├── docs
├── pipelines
├── deployments
└── governance`}</pre>
          </OperatorPanel>
          <OperatorPanel title="Developer Workflow">
            <div className="codepro-flow vertical-flow">
              {["Create Workspace", "Code", "AI Review", "Commit", "Pipeline", "Deploy"].map((step) => (
                <span key={step}>{step}</span>
              ))}
            </div>
          </OperatorPanel>
          <OperatorPanel title="NovaGit Governance">
            <p className="section-note">Every merge includes reviewer, approval, evidence, and audit record.</p>
            <div className="docs-grid">
              {["Repositories", "Branch protection", "Pull requests", "Review workflows", "Signed commits", "Repository policies"].map((item) => (
                <div key={item} className="reason-chip reason-chip-success">{item}</div>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <SectionIntro
          eyebrow="NovaAI Engineering"
          title="Specialized AI roles for governed software delivery"
          question="NovaAI does not replace governance. It proposes, reviews, documents, and audits while NovaCodePro records the evidence trail."
        />
        <div className="codepro-role-grid">
          {NOVACODEPRO_AI_ROLES.map((role) => (
            <article key={role.role} className="codepro-role-card">
              <span>{role.action}</span>
              <strong>{role.role}</strong>
              <div className="chip-row">
                {role.outputs.map((output) => (
                  <span key={output} className="surface-chip">{output}</span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <section className="codepro-journey-panel">
          <SectionIntro
            eyebrow="Live Engineering Journey"
            title="Watch code become verified software"
            question="A repository moves through AI generation, pipeline validation, security, deployment, and NovaTrust evidence."
          />
          <div className="journey-control-row">
            <button
              type="button"
              className="button primary"
              onClick={() => {
                setEngineeringJourneyActive(true);
                setEngineeringJourneyStep(0);
              }}
            >
              ▶ Start Engineering Journey
            </button>
            <span>
              {engineeringJourneyActive && engineeringJourneyStep >= NOVACODEPRO_ENGINEERING_JOURNEY.length
                ? "Trust Score: 99.4% · Pipeline Verified · Security Passed · Deployment Approved · Audit Ready"
                : "Ready to verify engineering delivery"}
            </span>
          </div>
          <div className="replay-demo codepro-journey-grid">
            {NOVACODEPRO_ENGINEERING_JOURNEY.map((step, index) => (
              <article
                key={step.step}
                className={`replay-step ${engineeringJourneyStep >= index + 1 ? "replay-step-active" : ""}`}
              >
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{step.step}</strong>
                <p>{step.result}</p>
                <em>{step.product}</em>
              </article>
            ))}
          </div>
        </section>

        <div className="codepro-status-grid">
          {NOVACODEPRO_STATUS.map((status) => (
            <article key={status.system} className="status-pill status-pill-active codepro-status-pill">
              <span>{status.system}</span>
              <strong>{status.state}</strong>
              <em>service status</em>
            </article>
          ))}
        </div>

        <SectionIntro
          eyebrow="Core Applications"
          title="A full engineering suite, not just an IDE"
          question="Desktop, mobile, cloud IDE, AI assistant, automation, deployment, monitoring, security, docs, and marketplace operate as one governed engineering platform."
        />
        <div className="novacodepro-app-grid">
          {NOVACODEPRO_APPS.map((app) => (
            <article key={app.name} className="novacodepro-app-card">
              <div className="record-card-header">
                <strong>{app.name}</strong>
                <span>{app.type}</span>
              </div>
              <p>{app.summary}</p>
              <div className="chip-row">
                {app.features.map((feature) => (
                  <span key={feature} className="surface-chip">{feature}</span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <div className="novacodepro-system-grid">
          <OperatorPanel title="AI Engineering Agents">
            <div className="docs-grid">
              {NOVACODEPRO_AI_AGENTS.map((agent) => (
                <div key={agent} className="reason-chip reason-chip-success">{agent}</div>
              ))}
            </div>
          </OperatorPanel>
          <OperatorPanel title="Enterprise Controls">
            <div className="docs-grid">
              {NOVACODEPRO_ENTERPRISE_FEATURES.map((feature) => (
                <div key={feature} className="reason-chip">{feature}</div>
              ))}
            </div>
          </OperatorPanel>
          <OperatorPanel title="Developer Services">
            <div className="docs-grid">
              {NOVACODEPRO_DEVELOPER_SERVICES.map((service) => (
                <div key={service} className="reason-chip reason-chip-success">{service}</div>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <div className="novacodepro-language-panel">
          <div>
            <p className="eyebrow">Supported Languages</p>
            <h3>Multi-language engineering from day one.</h3>
          </div>
          <div className="language-grid">
            {NOVACODEPRO_LANGUAGES.map((language) => (
              <span key={language}>{language}</span>
            ))}
          </div>
        </div>

        <SectionIntro
          eyebrow="Ecosystem Integration"
          title="The engineering platform for every NovaTech product"
          question="NovaCodePro powers software delivery across mobility, payments, identity, trust, AI, cloud, and monitoring while remaining a standalone enterprise engineering platform."
        />
        <div className="novacodepro-ecosystem-grid">
          {NOVACODEPRO_ECOSYSTEM.map((integration) => (
            <article key={integration.product} className="record-card">
              <strong>{integration.product}</strong>
              <p>{integration.role}</p>
            </article>
          ))}
        </div>

        <SectionIntro
          eyebrow="Enterprise Operating Model"
          title="Control center, tenancy, docs, and marketplace economy"
          question="NovaCodePro X is designed as multi-tenant enterprise SaaS: teams, projects, evidence, billing, documentation, extensions, and revenue-share marketplace."
        />
        <div className="codepro-enterprise-grid">
          <OperatorPanel title="Enterprise Control Center">
            <div className="docs-grid">
              {NOVACODEPRO_ENTERPRISE_CONTROL_CENTER.map((item) => (
                <div key={item} className="reason-chip reason-chip-success">{item}</div>
              ))}
            </div>
          </OperatorPanel>
          <OperatorPanel title="Multi-Tenant SaaS Architecture">
            <div className="tenant-tree">
              <strong>Tenant</strong>
              {NOVACODEPRO_TENANT_MODEL.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </OperatorPanel>
          <OperatorPanel title="Developer Portal">
            <p className="section-note">docs.novacodepro.com</p>
            <div className="docs-grid">
              {NOVACODEPRO_DOCS_PORTAL.map((item) => (
                <div key={item} className="reason-chip">{item}</div>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <div className="marketplace-economy-grid">
          {NOVACODEPRO_MARKETPLACE_ECONOMY.map((entry) => (
            <article key={entry.category} className="download-card">
              <span>{entry.model}</span>
              <strong>{entry.category}</strong>
              <p>Marketplace-ready category for NovaCodePro extensions, templates, agents, and automation packs.</p>
            </article>
          ))}
        </div>

        <div className="trusted-positioning-grid">
          {TRUSTED_PRODUCT_POSITIONING.map(([product, positioning]) => (
            <article key={product} className="record-card">
              <strong>{product}</strong>
              <p>{positioning}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band downloads-band" id="downloads">
        <SectionIntro
          eyebrow="Enterprise Downloads"
          title="Boardroom-ready trust infrastructure material"
          question="Professional buyers need downloadable architecture, security, governance, and API material before procurement or partnership review."
        />
        <div className="download-grid">
          {ENTERPRISE_DOWNLOADS.map((download) => (
            <article key={download} className="download-card">
              <span>PDF</span>
              <strong>{download}</strong>
              <p>Prepared for enterprise, investor, partner, and compliance review.</p>
              <a href="#contact">Request download</a>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band investor-band" id="investors">
        <SectionIntro
          eyebrow="Investors & Partners"
          title="A trust platform growth story"
          question="AfriTechnology scales from controlled pilots into a regional trust infrastructure network for mobility, payments, identity, and AI operations."
        />
        <div className="expansion-path">
          {EXPANSION_PATH.map((market) => (
            <span key={market}>{market}</span>
          ))}
        </div>
        <div className="pitch-grid">
          {["Platform Metrics", "Pilot Metrics", "Roadmap", "Market Opportunity", "Revenue Streams", "Strategic Partnerships"].map((item) => (
            <article key={item} className="investor-claim">
              <span>Investor Readiness</span>
              <strong>{item}</strong>
              <p>Prepared as a dedicated partner and investor surface rather than buried in the operator dashboard.</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-band contact-band" id="contact">
        <div className="contact-panel">
          <div>
            <p className="eyebrow">Start Pilot</p>
            <h2>Build trusted operations with AfriTechnology.</h2>
            <p>
              Start with one controlled pilot flow, prove the evidence trail,
              then expand into payments, identity, audit exports, and governed AI.
            </p>
          </div>
          <div className="hero-actions">
            <a className="button primary" href="mailto:hello@afritechnology.com">Contact AfriTechnology</a>
            <a className="button secondary" href="/v1/operator/dashboard">Open Operator Demo</a>
          </div>
        </div>
      </section>

      <footer className="ecosystem-footer" aria-label="AfriTechnology ecosystem footer">
        <div>
          <strong>AFRITECHNOLOGY</strong>
          <span>Trust Infrastructure Experience Platform</span>
        </div>
        <nav>
          <section>
            <h3>Platform</h3>
            <a href="#platform">NovaTech</a>
          </section>
          <section>
            <h3>Products</h3>
            {PLATFORM_PRODUCTS.map((product) => (
              <a key={product.name} href={product.docs}>{product.name}</a>
            ))}
          </section>
          <section>
            <h3>Resources</h3>
            <a href="#developers">Documentation</a>
            <a href="#trust-center">Trust Center</a>
            <a href="#case-studies">Case Studies</a>
            <a href="#downloads">Downloads</a>
          </section>
          <section>
            <h3>Company</h3>
            <a href="#investors">Partners</a>
            <a href="#investors">Investors</a>
            <a href="#global">Roadmap</a>
            <a href="#contact">Contact</a>
          </section>
          <section>
            <h3>Status</h3>
            <a href="#home">system.afritechnology.com</a>
          </section>
        </nav>
      </footer>

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

      <section className="section-band novaride-ops-band" id="novaride-operations-layer">
        <SectionIntro
          eyebrow="NovaRide Operations Layer"
          title="Next-generation mobility command center"
          question="Operator, admin, support, inspector, rider, driver, payments, trust, and ecosystem apps are composed into one high-level operations surface."
        />

        <div className="ops-kpi-grid">
          {novaRideOperationsSurface.kpis.map((metric) => (
            <article key={metric.label} className="ops-kpi-card">
              <div className="ops-kpi-card-header">
                <span>{metric.label}</span>
                <em>{metric.trend}</em>
              </div>
              <strong>{metric.value}</strong>
              <MiniSparkline values={metric.chart} />
              <small>{metric.detail}</small>
            </article>
          ))}
        </div>

        <div className="ops-command-grid">
          <OperatorPanel title="Live Operations Map">
            <div className="ops-map" aria-label="Sydney operations map">
              <div className="ops-map-grid" />
              <div className="ops-map-river" />
              {novaRideOperationsSurface.clusters.map((cluster) => (
                <div
                  key={cluster.label}
                  className="ops-map-cluster"
                  style={{ left: `${cluster.x}%`, top: `${cluster.y}%` }}
                  title={`${cluster.label}: ${cluster.count}`}
                >
                  <strong>{cluster.count}</strong>
                  <span>{cluster.label}</span>
                </div>
              ))}
              {novaRideOperationsSurface.drivers.map((driver) => (
                <div
                  key={driver.id}
                  className={`ops-driver-dot ops-driver-${driver.status}`}
                  style={{ left: `${driver.x}%`, top: `${driver.y}%` }}
                  title={`${driver.id}: ${driver.status}`}
                />
              ))}
            </div>
            <div className="ops-map-legend">
              <span><i className="legend-available" />Available</span>
              <span><i className="legend-busy" />Busy</span>
              <span><i className="legend-offline" />Offline</span>
              <span><i className="legend-risk" />At Risk</span>
              <span><i className="legend-cluster" />Cluster</span>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Ride Control Panel">
            <div className="ops-ride-control">
              <div className="ops-ride-id">
                <span>Ride ID</span>
                <strong>#{novaRideOperationsSurface.rideControl.rideId}</strong>
              </div>
              <KeyValue label="Passenger" value={novaRideOperationsSurface.rideControl.passenger} />
              <KeyValue label="Driver" value={novaRideOperationsSurface.rideControl.driver} />
              <KeyValue label="Pickup -> Dropoff" value={novaRideOperationsSurface.rideControl.route} />
              <KeyValue label="ETA / Distance" value={`${novaRideOperationsSurface.rideControl.eta} / ${novaRideOperationsSurface.rideControl.distance}`} />
              <KeyValue label="Fare" value={novaRideOperationsSurface.rideControl.fare} />
              <div className="ops-control-actions">
                {["Reassign driver", "Cancel ride", "Contact driver", "Track route"].map((action) => (
                  <button key={action} type="button" className="ops-action-button ops-action-button-secondary">
                    {action}
                  </button>
                ))}
              </div>
            </div>
          </OperatorPanel>
        </div>

        <div className="ops-ai-grid">
          <OperatorPanel title="AI Decision Layer">
            <div className="ops-ai-card-grid">
              {novaRideOperationsSurface.aiLayer.map((item) => (
                <article key={item.title} className="ops-ai-card">
                  <span>{item.title}</span>
                  <strong>{item.value}</strong>
                  <p>{item.detail}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Live Activity Feed">
            <div className="ops-feed">
              {novaRideOperationsSurface.activity.map((item) => (
                <article key={`${item.time}-${item.actor}`} className={`ops-feed-item ops-feed-${item.tone}`}>
                  <time>{item.time}</time>
                  <div>
                    <strong>{item.event}</strong>
                    <span>{item.actor}</span>
                  </div>
                  <em>{item.value}</em>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <div className="ops-layout-grid">
          <OperatorPanel title="Alerts & Notifications">
            <div className="stack">
              {novaRideOperationsSurface.alerts.map((alert) => (
                <article key={alert.title} className={`ops-alert ops-alert-${alert.severity}`}>
                  <strong>{alert.title}</strong>
                  <span>{alert.detail}</span>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Fleet & Performance Analytics">
            <div className="ops-chart">
              {novaRideOperationsSurface.chartValues.map((height, index) => (
                <span key={index} style={{ height: `${height}px` }} />
              ))}
            </div>
            <div className="ops-fleet-list">
              {novaRideOperationsSurface.fleet.map((status) => (
                <div key={status.label}>
                  <span>{status.label}</span>
                  <strong>{status.value}</strong>
                  <em>{status.percent}</em>
                </div>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Payment Overview">
            <div className="ops-metric-stack">
              {novaRideOperationsSurface.payments.map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Trust & Safety Panel">
            <div className="ops-metric-stack">
              {novaRideOperationsSurface.trustSafety.map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <OperatorPanel title="Quick Actions">
          <div className="ops-action-row">
            {novaRideOperationsSurface.quickActions.map((action) => (
              <button key={action.label} type="button" className="ops-action-button">
                <span>{action.label}</span>
                <small>{action.detail}</small>
              </button>
            ))}
          </div>
        </OperatorPanel>

        <div className="ops-platform-grid">
          <OperatorPanel title="Realtime Architecture">
            <div className="ops-metric-stack">
              {novaRideOperationsSurface.realtime.map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                  <em>{item.detail}</em>
                </div>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Trust, Replay & Audit">
            <div className="ops-metric-stack">
              {novaRideOperationsSurface.trustReplay.map((item) => (
                <div key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="RBAC & Security">
            <div className="stack">
              {novaRideOperationsSurface.rbac.map((role) => (
                <article key={role.role} className="ops-rbac-row">
                  <strong>{role.role}</strong>
                  <span>{role.scope}</span>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <div className="ops-platform-grid">
          <OperatorPanel title="Operational Intelligence">
            <div className="ops-metric-stack">
              <div>
                <span>Ride Volume</span>
                <strong>{novaRideOperationsSurface.analytics.strategy}</strong>
              </div>
              <div>
                <span>Fleet Status</span>
                <strong>{novaRideOperationsSurface.analytics.utilization.toFixed(1)}%</strong>
              </div>
              <div>
                <span>Evidence Coverage</span>
                <strong>{novaRideOperationsSurface.analytics.evidenceCoverage}%</strong>
              </div>
              <div>
                <span>Profit Projection</span>
                <strong>{novaRideOperationsSurface.analytics.projectedProfit}</strong>
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Backend Modules">
            <div className="chip-row">
              {novaRideOperationsSurface.backendModules.map((module) => (
                <span key={module} className="surface-chip">{module}</span>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <div className="operator-grid">
          {NOVARIDE_OPERATION_MODULES.map((module) => (
            <OperatorPanel key={module.name} title={module.name}>
              <article className="record-card">
                <div className="record-card-header">
                  <strong>{module.focus}</strong>
                  <span>operations</span>
                </div>
                <div className="chip-row">
                  {module.capabilities.map((capability) => (
                    <span key={capability} className="surface-chip">{capability}</span>
                  ))}
                </div>
              </article>
            </OperatorPanel>
          ))}
        </div>

        <div className="operator-grid">
          <OperatorPanel title="Driver + Rider Apps Integration">
            <div className="stack">
              {NOVARIDE_APP_INTEGRATIONS.map((app) => (
                <article key={app.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{app.name}</strong>
                    <span>connected</span>
                  </div>
                  <p>{app.detail}</p>
                </article>
              ))}
            </div>
          </OperatorPanel>

          <OperatorPanel title="Platform Ecosystem">
            <div className="stack">
              {NOVARIDE_ECOSYSTEM_APPS.map((app) => (
                <article key={app.name} className="record-card">
                  <div className="record-card-header">
                    <strong>{app.name}</strong>
                    <span>{app.detail}</span>
                  </div>
                </article>
              ))}
            </div>
          </OperatorPanel>
        </div>

        <OperatorPanel title="High-Level Next Generation Enhancements">
          <div className="chip-row">
            {NOVARIDE_AI_ENHANCEMENTS.map((enhancement) => (
              <span key={enhancement} className="surface-chip">{enhancement}</span>
            ))}
          </div>
        </OperatorPanel>
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
        <OperatorPanel title="DAO Token Economy">
          <div className="compliance-panel">
            <article className="compliance-score-card">
              <div>
                <strong>{novarideDaoEconomy.token_economy.symbol}</strong>
                <span>{novarideDaoEconomy.token_economy.name}</span>
              </div>
              <span className="compliance-status pass">
                Governance score {novarideDaoEconomy.governance.governance_score}%
              </span>
            </article>
            <div className="compliance-summary-grid">
              <article>
                <strong>{novarideDaoEconomy.token_economy.total_supply}</strong>
                <span>Total supply</span>
              </article>
              <article>
                <strong>{novarideDaoEconomy.token_economy.circulating_supply}</strong>
                <span>Circulating</span>
              </article>
              <article>
                <strong>{novarideDaoEconomy.governance.active_proposals}</strong>
                <span>Active proposals</span>
              </article>
              <article>
                <strong>{novarideDaoEconomy.governance.participation_rate}%</strong>
                <span>Participation</span>
              </article>
            </div>
            <div className="chip-row">
              {(novarideDaoEconomy.token_economy.utility || []).map((utility) => (
                <span key={utility} className="surface-chip">
                  {utility}
                </span>
              ))}
            </div>
            <div className="chip-row">
              {(novarideDaoEconomy.token_economy.reward_actions || []).map((action) => (
                <span key={action} className="reason-chip">
                  {action}
                </span>
              ))}
            </div>
            <div className="compliance-rule-list">
              {(novarideDaoEconomy.governance.proposal_queue || []).slice(0, 4).map((proposal) => (
                <article key={proposal.proposal_id} className="compliance-rule-row">
                  <div>
                    <strong>{proposal.title}</strong>
                    <span>
                      {proposal.category} · {proposal.status} · {proposal.treasury_request}
                    </span>
                  </div>
                  <span className="compliance-status pass">{proposal.votes_for}</span>
                </article>
              ))}
            </div>
          </div>
        </OperatorPanel>
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
              operatorCityProfitOptimization={operatorCityProfitOptimization}
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
              operatorCityProfitOptimization={operatorCityProfitOptimization}
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

          <OperatorPanel title="Architecture Compliance">
            <div className="compliance-panel">
              <article className="compliance-score-card">
                <div>
                  <strong>{architectureCompliance.score}%</strong>
                  <span>Compliance score</span>
                </div>
                <span className={`compliance-status ${architectureCompliance.status === "pass" ? "pass" : "fail"}`}>
                  {architectureCompliance.status || "pending"}
                </span>
              </article>
              <div className="compliance-summary-grid">
                <article>
                  <strong>{architectureCompliance.rules_passed}</strong>
                  <span>Rules passed</span>
                </article>
                <article>
                  <strong>{architectureCompliance.rules_failed}</strong>
                  <span>Rules failed</span>
                </article>
                <article>
                  <strong>{architectureCompliance.mode}</strong>
                  <span>Report source</span>
                </article>
                <article>
                  <strong>/metrics/architecture/compliance</strong>
                  <span>Prometheus Metrics</span>
                </article>
              </div>
              <div className="chip-row">
                {(architectureCompliance.capabilities || []).map((capability) => (
                  <span key={capability} className="surface-chip">
                    {capability}
                  </span>
                ))}
                <span className="surface-chip">Grafana Panels</span>
                <span className="surface-chip">Failed rules trend</span>
                <span className="surface-chip">API breaking changes</span>
                <span className="surface-chip">Security violations</span>
              </div>
              <div className="compliance-rule-list">
                {(architectureCompliance.report || []).map((rule) => (
                  <article key={rule.name} className="compliance-rule-row">
                    <div>
                      <strong>{rule.name}</strong>
                      <span>
                        {Array.isArray(rule.issues) && rule.issues.length > 0
                          ? rule.issues.slice(0, 2).join(" | ")
                          : "No violations detected"}
                      </span>
                    </div>
                    <span className={`compliance-status ${rule.passed ? "pass" : "fail"}`}>
                      {rule.passed ? "PASS" : "FAIL"}
                    </span>
                  </article>
                ))}
                {(architectureCompliance.report || []).length === 0 ? (
                  <EmptyState label="Compliance report will appear after the architecture validator publishes a result." />
                ) : null}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Auto-Fix Actions">
            <div className="compliance-panel">
              <article className="compliance-score-card">
                <div>
                  <strong>{architectureRemediation.fixes_total}</strong>
                  <span>Proposed fixes</span>
                </div>
                <span className={`compliance-status ${architectureRemediation.final_passed ? "pass" : "fail"}`}>
                  {architectureRemediation.final_passed ? "COMPLIANT" : "REVIEW"}
                </span>
              </article>
              <div className="compliance-summary-grid">
                <article>
                  <strong>{architectureRemediation.manual_review_required}</strong>
                  <span>Human approval required</span>
                </article>
                <article>
                  <strong>{architectureRemediation.mode}</strong>
                  <span>Self-healing status</span>
                </article>
                <article>
                  <strong>{architectureRemediation.source || "validator"}</strong>
                  <span>Plan source</span>
                </article>
              </div>
              <div className="compliance-rule-list">
                {(architectureRemediation.fixes || []).slice(0, 8).map((fix, index) => (
                  <article key={`${fix.rule}-${fix.action}-${index}`} className="compliance-rule-row">
                    <div>
                      <strong>{fix.action || "request_human_architecture_review"}</strong>
                      <span>{fix.detail || fix.issue || "Remediation pending review"}</span>
                    </div>
                    <span className={`compliance-status ${fix.safe_to_apply ? "pass" : "fail"}`}>
                      {fix.safe_to_apply ? "SAFE" : "APPROVAL"}
                    </span>
                  </article>
                ))}
                {(architectureRemediation.fixes || []).length === 0 ? (
                  <article className="compliance-rule-row">
                    <div>
                      <strong>No remediation required</strong>
                      <span>Validator report is compliant; auto-fix engine is standing by.</span>
                    </div>
                    <span className="compliance-status pass">PASS</span>
                  </article>
                ) : null}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="AI Learning Insights">
            <div className="compliance-panel">
              <article className="compliance-score-card">
                <div>
                  <strong>{architectureLearning.risk_profile.score}%</strong>
                  <span>Auto-fix success</span>
                </div>
                <span
                  className={`compliance-status ${architectureLearning.risk_profile.risk === "low" ? "pass" : "fail"}`}
                >
                  {architectureLearning.risk_profile.risk}
                </span>
              </article>
              <div className="compliance-summary-grid">
                <article>
                  <strong>
                    {Object.entries(architectureLearning.patterns).sort(
                      (left, right) =>
                        ((right[1]?.success || 0) + (right[1]?.fail || 0)) -
                        ((left[1]?.success || 0) + (left[1]?.fail || 0)),
                    )[0]?.[0] || "No learning data"}
                  </strong>
                  <span>Top issue</span>
                </article>
                <article>
                  <strong>{architectureLearning.risk_profile.total}</strong>
                  <span>Learning events</span>
                </article>
                <article>
                  <strong>{architectureLearning.learning_memory_path}</strong>
                  <span>Memory store</span>
                </article>
                <article>
                  <strong>{architectureLearning.risk_profile.risk}</strong>
                  <span>System risk</span>
                </article>
                <article>
                  <strong>{architectureLearning.optimizer_suggestions.length}</strong>
                  <span>Optimization suggestions</span>
                </article>
              </div>
              <div className="chip-row">
                {architectureLearning.optimizer_suggestions.length > 0 ? (
                  architectureLearning.optimizer_suggestions.slice(0, 4).map((suggestion) => (
                    <span key={suggestion} className="surface-chip">
                      {suggestion}
                    </span>
                  ))
                ) : (
                  <span className="surface-chip">No optimization suggestions</span>
                )}
              </div>
              <div className="compliance-rule-list">
                {Object.entries(architectureLearning.knowledge_graph)
                  .slice(0, 4)
                  .map(([issue, summary]) => (
                    <article key={issue} className="compliance-rule-row">
                      <div>
                        <strong>{issue}</strong>
                        <span>
                          {summary.best_fix?.action || "No learned fix"} · {summary.success || 0} success ·{" "}
                          {summary.fail || 0} fail
                        </span>
                      </div>
                      <span
                        className={`compliance-status ${
                          (summary.success || 0) >= (summary.fail || 0) ? "pass" : "fail"
                        }`}
                      >
                        {summary.total || 0}
                      </span>
                    </article>
                  ))}
                {Object.keys(architectureLearning.knowledge_graph).length === 0 ? (
                  <article className="compliance-rule-row">
                    <div>
                      <strong>No learning history</strong>
                      <span>Learning memory is empty until a governed remediation is recorded.</span>
                    </div>
                    <span className="compliance-status pass">PASS</span>
                  </article>
                ) : null}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Predictive Governance">
            <div className="compliance-panel">
              <article className="compliance-score-card">
                <div>
                  <strong>{architecturePredictive.risk_score}</strong>
                  <span>Predictive risk score</span>
                </div>
                <span className={`compliance-status ${architecturePredictive.risk_score >= 60 ? "fail" : "pass"}`}>
                  {architecturePredictive.digital_twin.twin_health_score}% twin
                </span>
              </article>
              <div className="compliance-summary-grid">
                <article>
                  <strong>{architecturePredictive.metrics.predicted_risks}</strong>
                  <span>Predicted risks</span>
                </article>
                <article>
                  <strong>{architecturePredictive.metrics.prevented_violations}</strong>
                  <span>Preventive actions</span>
                </article>
                <article>
                  <strong>{architecturePredictive.digital_twin.scenario_count}</strong>
                  <span>Simulation scenarios</span>
                </article>
                <article>
                  <strong>{architecturePredictive.authority_boundary}</strong>
                  <span>Authority boundary</span>
                </article>
              </div>
              <div className="chip-row">
                {(architecturePredictive.digital_twin.mirrored_components || []).slice(0, 5).map((component) => (
                  <span key={component} className="surface-chip">
                    {component}
                  </span>
                ))}
              </div>
              <div className="compliance-rule-list">
                {(architecturePredictive.scenarios || []).slice(0, 4).map((scenario) => (
                  <article key={scenario.scenario_id} className="compliance-rule-row">
                    <div>
                      <strong>{scenario.description}</strong>
                      <span>
                        {scenario.predictions?.[0]?.risk || "No risk"} · {scenario.predictions?.[0]?.preventive_action || "WATCH"}
                      </span>
                    </div>
                    <span
                      className={`compliance-status ${
                        (scenario.risk_score || 0) >= 60 ? "fail" : "pass"
                      }`}
                    >
                      {scenario.risk_score || 0}
                    </span>
                  </article>
                ))}
                {(architecturePredictive.scenarios || []).length === 0 ? (
                  <article className="compliance-rule-row">
                    <div>
                      <strong>No predictive scenarios</strong>
                      <span>Digital twin projections will appear after the predictive governance endpoint is reachable.</span>
                    </div>
                    <span className="compliance-status pass">PASS</span>
                  </article>
                ) : null}
              </div>
            </div>
          </OperatorPanel>

          <OperatorPanel title="Autonomous Multi-Agent Governance">
            <div className="compliance-panel">
              <article className="compliance-score-card">
                <div>
                  <strong>{architectureAutonomous.metrics.multi_agent_findings}</strong>
                  <span>Multi-agent findings</span>
                </div>
                <span className={`compliance-status ${architectureAutonomous.metrics.critical_crisis_scenarios > 0 ? "fail" : "pass"}`}>
                  {architectureAutonomous.metrics.economic_efficiency}% efficiency
                </span>
              </article>
              <div className="compliance-summary-grid">
                <article>
                  <strong>{architectureAutonomous.multi_agent.agent_count}</strong>
                  <span>Active agents</span>
                </article>
                <article>
                  <strong>{architectureAutonomous.crisis_summary.scenario_count}</strong>
                  <span>Crisis scenarios</span>
                </article>
                <article>
                  <strong>{architectureAutonomous.crisis_summary.max_risk_score}</strong>
                  <span>Max crisis risk</span>
                </article>
                <article>
                  <strong>{architectureAutonomous.economic_optimization.action}</strong>
                  <span>Economic decision</span>
                </article>
                <article>
                  <strong>{architectureAutonomous.crisis_summary.black_swan.event}</strong>
                  <span>Black swan</span>
                </article>
              </div>
              <div className="chip-row">
                {(architectureAutonomous.refactor_suggestions || []).length > 0 ? (
                  architectureAutonomous.refactor_suggestions.slice(0, 4).map((suggestion) => (
                    <span key={suggestion} className="surface-chip">
                      {suggestion}
                    </span>
                  ))
                ) : (
                  <span className="surface-chip">No refactor suggestions</span>
                )}
              </div>
              <div className="compliance-rule-list">
                {(architectureAutonomous.multi_agent.findings || []).slice(0, 4).map((finding) => (
                  <article key={`${finding.agent}-${finding.risk}`} className="compliance-rule-row">
                    <div>
                      <strong>{finding.agent}</strong>
                      <span>
                        {finding.risk} · {finding.detail}
                      </span>
                    </div>
                    <span className={`compliance-status ${finding.severity === "critical" ? "fail" : "pass"}`}>
                      {finding.severity}
                    </span>
                  </article>
                ))}
                {(architectureAutonomous.crisis || []).slice(0, 2).map((scenario) => (
                  <article key={scenario.scenario} className="compliance-rule-row">
                    <div>
                      <strong>{scenario.scenario}</strong>
                      <span>
                        {scenario.impact} · {scenario.requires}
                      </span>
                    </div>
                    <span className={`compliance-status ${scenario.impact === "CRITICAL" ? "fail" : "pass"}`}>
                      {scenario.risk_score}
                    </span>
                  </article>
                ))}
              </div>
            </div>
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
                  <span>{novarideEcosystem?.enterprise_operations_classification || "contract_loading"}</span>
                </div>
                <p>
                  App and portal surfaces now sit on an enterprise operations layer for command,
                  zones, digital twin simulation, incident workflow, fleet intelligence, public
                  trust, developer ecosystem, SRE observability, and multi-tenant governance.
                </p>
                <div className="chip-row">
                  <span className="surface-chip">Enterprise Operations: 10/10</span>
                  <span className="surface-chip">Architecture version {novarideArchitecture.version || "pending"}</span>
                  <span className="surface-chip">AI-assisted decisions</span>
                  <span className="surface-chip">Evidence-backed operations</span>
                  <span className="surface-chip">Multi-tenant governance</span>
                </div>
              </article>

              <article className="record-card">
                <strong>Layered architecture</strong>
                <div className="flow-line" aria-label="NovaRide layered architecture">
                  {novarideLayeredArchitecture.map((layer) => (
                    <span key={layer}>{layer}</span>
                  ))}
                </div>
              </article>

              <article className="record-card">
                <strong>Governed intervention flow</strong>
                <div className="flow-line" aria-label="NovaRide governed intervention flow">
                  {novarideOperatorInterventionFlow.map((step) => (
                    <span key={step}>{step}</span>
                  ))}
                </div>
              </article>

              <article className="record-card">
                <strong>Maturity dimensions</strong>
                <div className="novapay-build-grid">
                  {novarideMaturityDimensions.map((dimension) => (
                    <div key={dimension.dimension} className="record-card novapay-build-card">
                      <strong>{dimension.dimension}</strong>
                      <div className="chip-row">
                        {(dimension.capabilities || []).map((capability) => (
                          <span key={capability} className="reason-chip">{capability}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <div className="novapay-build-grid">
                {novarideEnterpriseOperationsLayer.map((capability) => (
                  <article key={capability.name} className="record-card novapay-build-card">
                    <div className="record-card-header">
                      <strong>{capability.name}</strong>
                      <span>{capability.purpose}</span>
                    </div>
                    <div className="chip-row">
                      {(capability.capabilities || []).map((item) => (
                        <span key={item} className="reason-chip reason-chip-success">{displayArchitectureToken(item)}</span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
              {novarideEnterpriseOperationsLayer.length === 0 ? (
                <EmptyState label="NovaRide enterprise operations contract will appear after the ecosystem API is reachable." />
              ) : null}

              <article className="record-card">
                <div className="record-card-header">
                  <strong>Production infrastructure readiness</strong>
                  <span>resilience_regulatory_external_verification</span>
                </div>
                <p>
                  Architecture is separated from deployment readiness: infrastructure hardening
                  covers distributed consistency, key management, operational resilience,
                  regulatory readiness, and independent verification.
                </p>
              </article>

              <div className="novapay-build-grid">
                {novarideProductionInfrastructureReadiness.map((capability) => (
                  <article key={capability.name} className="record-card novapay-build-card">
                    <div className="record-card-header">
                      <strong>{capability.name}</strong>
                      <span>{capability.purpose}</span>
                    </div>
                    <div className="chip-row">
                      {(capability.capabilities || []).map((item) => (
                        <span key={item} className="reason-chip">{displayArchitectureToken(item)}</span>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
              {novarideProductionInfrastructureReadiness.length === 0 ? (
                <EmptyState label="NovaRide production readiness contract will appear after the ecosystem API is reachable." />
              ) : null}

              <article className="record-card">
                <div className="record-card-header">
                  <strong>NovaRide Ecosystem Platform</strong>
                  <span>{novarideEcosystemPlatform.classification || "contract_platform_loading"}</span>
                </div>
                <p>
                  Partner-facing architecture contracts now publish unsigned controlled-contract
                  metadata, compatibility rows, migration guidance, SDK targets, and operational
                  metrics from the same canonical registry.
                </p>
                <div className="chip-row">
                  <span className="surface-chip">
                    {novarideEcosystemPlatform.signed_publication?.signature_status || "unsigned_controlled_contract"}
                  </span>
                  <span className="surface-chip">
                    schema hash {novarideEcosystemPlatform.signed_publication?.schema_hash || "pending"}
                  </span>
                  <span className="surface-chip">canonical.v1</span>
                  <span className="surface-chip">sha256</span>
                </div>
              </article>

              <div className="novapay-build-grid">
                <article className="record-card novapay-build-card">
                  <strong>Compatibility Matrix</strong>
                  <div className="chip-row">
                    {novarideCompatibilityMatrix.map((row) => (
                      <span key={`${row.requested_version}-${row.served_version}`} className="reason-chip reason-chip-success">
                        {row.requested_version} to {row.served_version}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card novapay-build-card">
                  <strong>Migration Registry</strong>
                  <div className="chip-row">
                    {novarideMigrationRegistry.map((migration) => (
                      <span key={`${migration.from_version}-${migration.to_version}`} className="reason-chip">
                        {migration.from_version} to {migration.to_version}: {migration.required_action}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card novapay-build-card">
                  <strong>SDK Registry</strong>
                  <div className="chip-row">
                    {novarideSdkRegistry.map((sdk) => (
                      <span key={sdk.language} className="reason-chip reason-chip-success">
                        {sdk.language}: {sdk.status}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card novapay-build-card">
                  <strong>Operational Metrics</strong>
                  <div className="chip-row">
                    {novarideOperationalMetrics.map(([metric, details]) => (
                      <span key={metric} className="reason-chip">
                        {metric}: {details.value} {details.unit}
                      </span>
                    ))}
                  </div>
                </article>
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
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideEcosystem.unified_ui_framework?.name || "NovaRide Unified UI Framework"}</strong>
                    <span>{novarideEcosystem.unified_ui_framework?.status || "contract_ready"}</span>
                  </div>
                  <div className="chip-row">
                    {(novarideEcosystem.unified_ui_framework?.shared_components || [
                      "TrustBadge",
                      "ReplayTimeline",
                      "NovaPayReceiptPanel",
                      "AgentRecommendationPanel",
                    ]).slice(0, 6).map((component) => (
                      <span key={component} className="surface-chip">
                        {component}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Native app activation</strong>
                  <div className="stack compact-stack">
                    {(novarideEcosystem.native_app_activation || []).map((activation) => (
                      <div key={activation.surface} className="reason-chip">
                        {activation.surface}: {activation.status}
                      </div>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Agentic AI modules</strong>
                  <div className="stack compact-stack">
                    {(novarideEcosystem.agentic_ai_modules || []).map((module) => (
                      <div key={module.key} className="reason-chip">
                        {module.name}: {module.authority}
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

          <OperatorPanel title="NovaRide Super App">
            {novarideSuperApp ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Global Super App Shell</strong>
                    <span>{novarideSuperApp.status || "contract_ready"}</span>
                  </div>
                  <p>{novarideSuperApp.super_app?.purpose}</p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Users {novarideSuperApp.super_app?.metrics?.users || "2.5M"}
                    </span>
                    <span className="surface-chip">
                      Apps {novarideSuperApp.super_app?.metrics?.apps || 0}
                    </span>
                    <span className="surface-chip">
                      Transactions {novarideSuperApp.super_app?.metrics?.transactions_per_day || "$5M"}
                    </span>
                    <span className="surface-chip">
                      {novarideSuperApp.super_app?.authority_boundary || "interface_only"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Super App dashboard</strong>
                  <div className="compliance-summary-grid">
                    <article>
                      <strong>{novarideSuperApp.super_app?.profile?.novaid}</strong>
                      <span>NovaID</span>
                    </article>
                    <article>
                      <strong>${novarideSuperApp.super_app?.profile?.wallet_balance_usd}</strong>
                      <span>Wallet</span>
                    </article>
                    <article>
                      <strong>{novarideSuperApp.super_app?.profile?.token_balance}</strong>
                      <span>Tokens</span>
                    </article>
                    <article>
                      <strong>{novarideSuperApp.super_app?.profile?.trust_score}</strong>
                      <span>Trust score</span>
                    </article>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Modules</strong>
                  <div className="stack compact-stack">
                    {(novarideSuperApp.super_app?.modules || []).map((module) => (
                      <article key={module.key} className="record-card">
                        <div className="record-card-header">
                          <strong>{module.name}</strong>
                          <span>{module.authority}</span>
                        </div>
                        <div className="chip-row">
                          {(module.capabilities || []).map((capability) => (
                            <span key={capability} className="surface-chip">
                              {capability.replaceAll("_", " ")}
                            </span>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Wallet + AI</strong>
                  <div className="chip-row">
                    {Object.entries(novarideSuperApp.super_app?.wallet?.balances || {}).map(([currency, amount]) => (
                      <span key={currency} className="surface-chip">
                        {currency} {amount}
                      </span>
                    ))}
                  </div>
                  <div className="stack compact-stack">
                    {(novarideSuperApp.super_app?.ai_assistant?.recommendations || []).map((recommendation) => (
                      <div key={recommendation} className="reason-chip">
                        {recommendation}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide Super App will appear after the contract surface is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaID Global Identity">
            {novaidIdentity ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novaidIdentity.identity?.positioning || "Login with NovaID"}</strong>
                    <span>{novaidIdentity.status || "standard_ready"}</span>
                  </div>
                  <p>{novaidIdentity.identity?.authority_boundary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Profiles {novaidIdentity.identity?.metrics?.identity_profiles || 0}
                    </span>
                    <span className="surface-chip">
                      Wallet link {novaidIdentity.identity?.metrics?.wallet_link_rate || "0%"}
                    </span>
                    <span className="surface-chip">
                      Devices {novaidIdentity.identity?.metrics?.verified_devices || 0}
                    </span>
                    <span className="surface-chip">
                      {novaidIdentity.identity?.login_button?.contract}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Digital economic identity</strong>
                  <div className="compliance-summary-grid">
                    <article>
                      <strong>{novaidIdentity.identity?.sample_profile?.id}</strong>
                      <span>NovaID</span>
                    </article>
                    <article>
                      <strong>{novaidIdentity.identity?.sample_profile?.did}</strong>
                      <span>DID</span>
                    </article>
                    <article>
                      <strong>{novaidIdentity.identity?.sample_profile?.trust_score}%</strong>
                      <span>Trust score</span>
                    </article>
                    <article>
                      <strong>{novaidIdentity.identity?.sample_profile?.wallet}</strong>
                      <span>Wallet</span>
                    </article>
                  </div>
                  <div className="chip-row">
                    {(novaidIdentity.identity?.sample_profile?.reputation || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Capabilities</strong>
                  <div className="stack compact-stack">
                    {(novaidIdentity.identity?.capabilities || []).map((capability) => (
                      <div key={capability.key} className="reason-chip">
                        {capability.name}: {capability.capability}
                      </div>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Policy gates</strong>
                  <div className="chip-row">
                    {(novaidIdentity.identity?.login_button?.policy_gates || []).map((gate) => (
                      <span key={gate} className="surface-chip">
                        {gate.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaID global identity will appear after the identity contract is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaID Gen-Sovereign">
            {novaidGenSovereign ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novaidGenSovereign.gen_sovereign?.positioning}</strong>
                    <span>{novaidGenSovereign.status || "architecture_contract_ready"}</span>
                  </div>
                  <p>{novaidGenSovereign.gen_sovereign?.authority_boundary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      NovaIDs {novaidGenSovereign.gen_sovereign?.dashboard?.identity?.novaids}
                    </span>
                    <span className="surface-chip">
                      Verified {novaidGenSovereign.gen_sovereign?.dashboard?.identity?.verified}
                    </span>
                    <span className="surface-chip">
                      Daily {novaidGenSovereign.gen_sovereign?.dashboard?.economy?.daily_transactions}
                    </span>
                    <span className="surface-chip">
                      Governance {novaidGenSovereign.gen_sovereign?.dashboard?.governance?.participation}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Sovereign infrastructure layers</strong>
                  <div className="stack compact-stack">
                    {(novaidGenSovereign.gen_sovereign?.core_layers || []).map((layer) => (
                      <article key={layer.key} className="record-card">
                        <div className="record-card-header">
                          <strong>{layer.name}</strong>
                          <span>{layer.authority}</span>
                        </div>
                        <p>{layer.role}</p>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>SSI credential model</strong>
                  <div className="compliance-summary-grid">
                    <article>
                      <strong>{novaidGenSovereign.gen_sovereign?.identity?.sample_did_document?.id}</strong>
                      <span>DID</span>
                    </article>
                    <article>
                      <strong>{novaidGenSovereign.gen_sovereign?.identity?.did_method}</strong>
                      <span>Method</span>
                    </article>
                    <article>
                      <strong>{novaidGenSovereign.gen_sovereign?.identity?.credential_standard}</strong>
                      <span>Credentials</span>
                    </article>
                    <article>
                      <strong>{novaidGenSovereign.gen_sovereign?.crypto_finance?.metrics?.token_circulation}</strong>
                      <span>Token circulation</span>
                    </article>
                  </div>
                  <div className="chip-row">
                    {(novaidGenSovereign.gen_sovereign?.identity?.sample_did_document?.credentials || []).map((credential) => (
                      <span key={credential} className="surface-chip">
                        {credential.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Government + federation adapters</strong>
                  <div className="chip-row">
                    {(novaidGenSovereign.gen_sovereign?.government_integration?.credential_types || []).map((credential) => (
                      <span key={credential} className="surface-chip">
                        {credential.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="stack compact-stack">
                    {(novaidGenSovereign.gen_sovereign?.federation?.apis || []).map((api) => (
                      <div key={api.path} className="reason-chip">
                        {api.path}: {api.purpose}
                      </div>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>AI governance voting</strong>
                  <div className="chip-row">
                    {Object.entries(novaidGenSovereign.gen_sovereign?.ai_governance?.formula || {}).map(([key, value]) => (
                      <span key={key} className="surface-chip">
                        {key} {value}
                      </span>
                    ))}
                  </div>
                  <p>
                    {novaidGenSovereign.gen_sovereign?.ai_governance?.sample_analysis?.proposal}:{" "}
                    ROI {novaidGenSovereign.gen_sovereign?.ai_governance?.sample_analysis?.roi},{" "}
                    risk {novaidGenSovereign.gen_sovereign?.ai_governance?.sample_analysis?.risk},{" "}
                    recommendation {novaidGenSovereign.gen_sovereign?.ai_governance?.sample_analysis?.recommendation}.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      {novaidGenSovereign.gen_sovereign?.ai_governance?.authority_boundary}
                    </span>
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaID Gen-Sovereign will appear after the sovereign contract is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaID Digital Nation">
            {novaidDigitalNation ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novaidDigitalNation.digital_nation?.positioning}</strong>
                    <span>{novaidDigitalNation.status || "architecture_contract_ready"}</span>
                  </div>
                  <p>{novaidDigitalNation.digital_nation?.authority_boundary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      NovaCitizens {novaidDigitalNation.digital_nation?.dashboard?.identity?.novacitizens}
                    </span>
                    <span className="surface-chip">
                      Verified {novaidDigitalNation.digital_nation?.dashboard?.identity?.verified}
                    </span>
                    <span className="surface-chip">
                      Trusted {novaidDigitalNation.digital_nation?.dashboard?.identity?.trusted}
                    </span>
                    <span className="surface-chip">
                      Daily {novaidDigitalNation.digital_nation?.dashboard?.economy?.daily_transactions}
                    </span>
                    <span className="surface-chip">
                      AI-assisted decisions{" "}
                      {novaidDigitalNation.digital_nation?.dashboard?.governance?.ai_assisted_decisions
                        ? "ENABLED"
                        : "DISABLED"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Digital nation boundary</strong>
                  <div className="chip-row">
                    {(novaidDigitalNation.digital_nation?.what_this_is || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novaidDigitalNation.digital_nation?.what_this_is_not || []).map((item) => (
                      <span key={item} className="reason-chip">
                        Not {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>NovaCitizen profile</strong>
                  <div className="compliance-summary-grid">
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.citizenship?.profile?.nova_id}</strong>
                      <span>NovaID</span>
                    </article>
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.citizenship?.profile?.wallet}</strong>
                      <span>Wallet</span>
                    </article>
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.citizenship?.profile?.trust_score}</strong>
                      <span>Trust score</span>
                    </article>
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.citizenship?.profile?.governance_power}</strong>
                      <span>Governance power</span>
                    </article>
                  </div>
                  <div className="chip-row">
                    {(novaidDigitalNation.digital_nation?.citizenship?.profile?.roles || []).map((role) => (
                      <span key={role} className="surface-chip">
                        {role}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>NovaPassport</strong>
                  <div className="compliance-summary-grid">
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.passport?.sample?.passport_id}</strong>
                      <span>Passport ID</span>
                    </article>
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.passport?.sample?.holder}</strong>
                      <span>Holder</span>
                    </article>
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.passport?.sample?.validity}</strong>
                      <span>Validity</span>
                    </article>
                    <article>
                      <strong>{novaidDigitalNation.digital_nation?.passport?.sample?.signature}</strong>
                      <span>Signature</span>
                    </article>
                  </div>
                  <p>{novaidDigitalNation.digital_nation?.passport?.authority_boundary}</p>
                  <div className="chip-row">
                    {(novaidDigitalNation.digital_nation?.passport?.sample?.credentials || []).map((credential) => (
                      <span key={credential} className="surface-chip">
                        {credential.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Citizenship tiers</strong>
                  <div className="stack compact-stack">
                    {(novaidDigitalNation.digital_nation?.citizenship?.tiers || []).map((tier) => (
                      <article key={tier.tier} className="record-card">
                        <div className="record-card-header">
                          <strong>{tier.tier}</strong>
                          <span>{tier.access}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Digital governance</strong>
                  <div className="chip-row">
                    {Object.entries(novaidDigitalNation.digital_nation?.governance?.formula || {}).map(([key, value]) => (
                      <span key={key} className="surface-chip">
                        {key} {value}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novaidDigitalNation.digital_nation?.governance?.proposal_types || []).map((proposalType) => (
                      <span key={proposalType} className="surface-chip">
                        {proposalType.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <p>
                    {novaidDigitalNation.digital_nation?.ai_governance?.sample_analysis?.proposal}:{" "}
                    impact {novaidDigitalNation.digital_nation?.ai_governance?.sample_analysis?.impact},{" "}
                    cost {novaidDigitalNation.digital_nation?.ai_governance?.sample_analysis?.cost},{" "}
                    recommendation {novaidDigitalNation.digital_nation?.ai_governance?.sample_analysis?.recommendation}.
                  </p>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaID Digital Nation will appear after the citizenship contract is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Digital Constitution">
            {novarideDigitalConstitution ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideDigitalConstitution.constitution?.positioning}</strong>
                    <span>{novarideDigitalConstitution.status || "architecture_contract_ready"}</span>
                  </div>
                  <p>{novarideDigitalConstitution.constitution?.authority_boundary}</p>
                  <div className="chip-row">
                    {Object.entries(novarideDigitalConstitution.constitution?.guarantees || {}).map(([key, value]) => (
                      <span key={key} className="surface-chip">
                        {key.replaceAll("_", " ")} {value ? "guaranteed" : "pending"}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Constitutional principle</strong>
                  <p>{novarideDigitalConstitution.constitution?.core_statement}</p>
                </article>
                <article className="record-card">
                  <strong>Foundational articles</strong>
                  <div className="stack compact-stack">
                    {(novarideDigitalConstitution.constitution?.articles || []).map((article) => (
                      <article key={article.article} className="record-card">
                        <div className="record-card-header">
                          <strong>Article {article.article}: {article.title}</strong>
                          <span>constitutional</span>
                        </div>
                        <p>{article.principle}</p>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Authority structure</strong>
                  <p>{novarideDigitalConstitution.constitution?.authority_structure?.fundamental_rule}</p>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.authority_structure?.authorities || []).map((authority) => (
                      <span key={authority.authority} className="surface-chip">
                        {authority.authority}: {authority.role}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Governance + AI limits</strong>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.governance?.powers || []).map((power) => (
                      <span key={power} className="surface-chip">
                        {power.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.governance?.ai_role?.shall_not || []).map((restriction) => (
                      <span key={restriction} className="reason-chip">
                        AI shall not {restriction.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Programmable law</strong>
                  <p>{novarideDigitalConstitution.constitution?.contract_law?.rule}</p>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.contract_law?.types || []).map((type) => (
                      <span key={type} className="surface-chip">
                        {type.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.contract_law?.enforcement || []).map((rule) => (
                      <span key={rule} className="surface-chip">
                        {rule.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Trust + dispute law</strong>
                  <p>{novarideDigitalConstitution.constitution?.trust_verification_law?.legal_equivalent}</p>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.dispute_resolution?.example_flow || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Enforcement + amendment</strong>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.compliance_enforcement?.layers || []).map((layer) => (
                      <span key={layer} className="surface-chip">
                        {layer.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideDigitalConstitution.constitution?.amendment_process || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide Digital Constitution will appear after the governance contract is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Regulatory Alignment">
            {novarideRegulatoryAlignment ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideRegulatoryAlignment.regulatory_alignment?.positioning}</strong>
                    <span>{novarideRegulatoryAlignment.status || "architecture_contract_ready"}</span>
                  </div>
                  <p>{novarideRegulatoryAlignment.regulatory_alignment?.authority_boundary}</p>
                  <div className="chip-row">
                    {Object.entries(novarideRegulatoryAlignment.regulatory_alignment?.dashboard?.regulatory_status || {}).map(([key, value]) => (
                      <span key={key} className="surface-chip">
                        {key} {value}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Legal alignment principle</strong>
                  <p>{novarideRegulatoryAlignment.regulatory_alignment?.core_principle}</p>
                </article>
                <article className="record-card">
                  <strong>Regulatory domains</strong>
                  <div className="stack compact-stack">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.alignment_model || []).map((domain) => (
                      <article key={domain.domain} className="record-card">
                        <div className="record-card-header">
                          <strong>{domain.domain}: {domain.novaride_layer}</strong>
                          <span>{domain.real_world_equivalent}</span>
                        </div>
                        <p>{domain.control}</p>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Identity + payments controls</strong>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.identity_compliance?.aligns_with || []).map((standard) => (
                      <span key={standard} className="surface-chip">
                        {standard.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <p>{novarideRegulatoryAlignment.regulatory_alignment?.identity_compliance?.rule}</p>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.payments_regulation?.requirements || []).map((requirement) => (
                      <span key={requirement} className="surface-chip">
                        {requirement.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Token + privacy classification</strong>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.token_regulation?.classification_model || []).map((token) => (
                      <span key={token.type} className="surface-chip">
                        {token.type.replaceAll("_", " ")}: {token.treatment.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.privacy_law?.principles || []).map((principle) => (
                      <span key={principle} className="surface-chip">
                        {principle.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Jurisdiction map</strong>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.cross_border_framework?.regions || []).map((region) => (
                      <span key={region.region} className="surface-chip">
                        {region.region}: {region.active_rule}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.cross_border_framework?.flow || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Liability + AI compliance</strong>
                  <p>{novarideRegulatoryAlignment.regulatory_alignment?.liability_model?.rule}</p>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.liability_model?.responsibilities || []).map((item) => (
                      <span key={item.component} className="surface-chip">
                        {item.component}: {item.responsibility}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.ai_regulation_compliance?.rules || []).map((rule) => (
                      <span key={rule} className="reason-chip">
                        {rule.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Compliance engine + risk monitor</strong>
                  <div className="chip-row">
                    {(novarideRegulatoryAlignment.regulatory_alignment?.compliance_engine?.flow || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {Object.entries(novarideRegulatoryAlignment.regulatory_alignment?.dashboard?.risk_monitor || {}).map(([key, value]) => (
                      <span key={key} className="surface-chip">
                        {key.replaceAll("_", " ")} {value}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide Regulatory Alignment will appear after the compliance contract is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="NovaRide Global Expansion">
            {novarideGlobalExpansion ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>{novarideGlobalExpansion.expansion?.positioning}</strong>
                    <span>{novarideGlobalExpansion.status || "strategy_contract_ready"}</span>
                  </div>
                  <p>{novarideGlobalExpansion.expansion?.authority_boundary}</p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Objective {novarideGlobalExpansion.expansion?.objective}
                    </span>
                    <span className="surface-chip">
                      Core principle {novarideGlobalExpansion.expansion?.core_principle}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Global Regulatory Expansion Strategy</strong>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.expansion_model || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Regulatory ready markets</strong>
                  <div className="stack compact-stack">
                    {(novarideGlobalExpansion.expansion?.phases || [])
                      .filter((phase) => phase.phase === "1")
                      .map((phase) => (
                        <article key={phase.name} className="record-card">
                          <div className="record-card-header">
                            <strong>{phase.name}</strong>
                            <span>{phase.status}</span>
                          </div>
                          <p>{phase.note}</p>
                          <div className="chip-row">
                            {(phase.markets || []).map((market) => (
                              <span key={market} className="surface-chip">
                                {market}
                              </span>
                            ))}
                          </div>
                        </article>
                      ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>High growth markets</strong>
                  <div className="stack compact-stack">
                    {(novarideGlobalExpansion.expansion?.phases || [])
                      .filter((phase) => phase.phase === "2")
                      .map((phase) => (
                        <article key={phase.name} className="record-card">
                          <div className="record-card-header">
                            <strong>{phase.name}</strong>
                            <span>{phase.status}</span>
                          </div>
                          <p>{phase.note}</p>
                          <div className="chip-row">
                            {(phase.markets || []).map((market) => (
                              <span key={market} className="surface-chip">
                                {market}
                              </span>
                            ))}
                          </div>
                        </article>
                      ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Complex regulations</strong>
                  <div className="stack compact-stack">
                    {(novarideGlobalExpansion.expansion?.phases || [])
                      .filter((phase) => phase.phase === "3")
                      .map((phase) => (
                        <article key={phase.name} className="record-card">
                          <div className="record-card-header">
                            <strong>{phase.name}</strong>
                            <span>{phase.status}</span>
                          </div>
                          <p>{phase.note}</p>
                          <div className="chip-row">
                            {(phase.markets || []).map((market) => (
                              <span key={market} className="surface-chip">
                                {market}
                              </span>
                            ))}
                          </div>
                        </article>
                      ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Country entry playbook</strong>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.country_entry_playbook?.regulatory_mapping || []).map(
                      (item) => (
                        <span key={item} className="surface-chip">
                          {item.replaceAll("_", " ")}
                        </span>
                      ),
                    )}
                  </div>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.country_entry_playbook?.legal_structure || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.country_entry_playbook?.partnership_model || []).map(
                      (item) => (
                        <span key={item} className="surface-chip">
                          {item.replaceAll("_", " ")}
                        </span>
                      ),
                    )}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Jurisdiction-aware compliance</strong>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.cross_border_architecture?.region_examples || []).map(
                      (region) => (
                        <span key={region.region} className="surface-chip">
                          {region.region}: {region.feature}
                        </span>
                      ),
                    )}
                  </div>
                  <p>
                    {(novarideGlobalExpansion.expansion?.cross_border_architecture?.compliance_engine || []).join(
                      " -> ",
                    )}
                  </p>
                </article>
                <article className="record-card">
                  <strong>Partner model</strong>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.novapay_deployment?.partner_based || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <p>{novarideGlobalExpansion.expansion?.go_to_market?.entry_model?.join(" -> ")}</p>
                </article>
                <article className="record-card">
                  <strong>Risk management</strong>
                  <div className="stack compact-stack">
                    {(novarideGlobalExpansion.expansion?.risk_management?.top_risks || []).map((item) => (
                      <article key={item.risk} className="record-card">
                        <div className="record-card-header">
                          <strong>{item.risk}</strong>
                          <span>{item.mitigation}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Dashboard snapshot</strong>
                  <div className="compliance-summary-grid">
                    <article>
                      <strong>{novarideGlobalExpansion.expansion?.dashboard?.expansion_status?.Australia}</strong>
                      <span>Australia</span>
                    </article>
                    <article>
                      <strong>{novarideGlobalExpansion.expansion?.dashboard?.expansion_status?.Kenya}</strong>
                      <span>Kenya</span>
                    </article>
                    <article>
                      <strong>{novarideGlobalExpansion.expansion?.dashboard?.expansion_status?.EU}</strong>
                      <span>EU</span>
                    </article>
                    <article>
                      <strong>{novarideGlobalExpansion.expansion?.dashboard?.financial?.transactions_per_day}</strong>
                      <span>Transactions / day</span>
                    </article>
                  </div>
                  <div className="chip-row">
                    {Object.entries(novarideGlobalExpansion.expansion?.dashboard?.compliance_status || {}).map(
                      ([key, value]) => (
                        <span key={key} className="surface-chip">
                          {key} {value}
                        </span>
                      ),
                    )}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Execution blueprint</strong>
                  <p>3-Hub deployment model: Melbourne, Burundi, DRC, East Africa.</p>
                  <div className="stack compact-stack">
                    {(novarideGlobalExpansion.expansion?.execution_blueprint?.hub_model || []).map((hub) => (
                      <article key={hub.hub} className="record-card">
                        <div className="record-card-header">
                          <strong>{hub.hub}</strong>
                          <span>{hub.role}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                  <article className="record-card">
                    <strong>Melbourne pilot</strong>
                    <p>Airport transfers and courier logistics with a 1000+ rides/month target.</p>
                  </article>
                  <article className="record-card">
                    <strong>Burundi launch</strong>
                    <p>Mobile money payments and a small local driver cohort.</p>
                  </article>
                  <article className="record-card">
                    <strong>DRC launch</strong>
                    <p>Motorbike taxis, delivery, and business transport expansion.</p>
                  </article>
                  <article className="record-card">
                    <strong>East Africa expansion</strong>
                    <p>M-Pesa integration for Kenya, with Rwanda and Uganda next.</p>
                  </article>
                  <div className="stack compact-stack">
                    {(novarideGlobalExpansion.expansion?.execution_blueprint?.phase_sequence || []).map((phase) => (
                      <article key={`${phase.phase}-${phase.market}`} className="record-card">
                        <div className="record-card-header">
                          <strong>Phase {phase.phase}: {phase.market}</strong>
                          <span>{phase.objective}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.execution_blueprint?.novaid_rollout || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.execution_blueprint?.novapay_rollout || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                  <div className="chip-row">
                    {(novarideGlobalExpansion.expansion?.execution_blueprint?.ninety_day_plan || []).map((item) => (
                      <span key={item} className="surface-chip">
                        {item.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide Global Expansion will appear after the rollout strategy contract is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="App Store">
            {novarideAppStore ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>NovaRide App Store</strong>
                    <span>{novarideAppStore.status || "governed_beta"}</span>
                  </div>
                  <p>
                    Apps are discovered, validated, installed, and published through a governed
                    distribution surface with policy gates and trust review.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Apps {novarideAppStore.app_store?.metrics?.app_count || 0}
                    </span>
                    <span className="surface-chip">
                      Developers {novarideAppStore.app_store?.metrics?.developer_count || 0}
                    </span>
                    <span className="surface-chip">
                      Cities {novarideAppStore.app_store?.metrics?.city_count || 0}
                    </span>
                    <span className="surface-chip">
                      Revenue split {novarideAppStore.app_store?.monetization?.revenue_split?.developer || "70%"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Categories</strong>
                  <div className="chip-row">
                    {(novarideAppStore.app_store?.categories || []).map((category) => (
                      <span key={category.key} className="surface-chip">
                        {category.name}
                      </span>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Published apps</strong>
                  <div className="stack compact-stack">
                    {(novarideAppStore.app_store?.apps || []).map((app) => (
                      <article key={app.app_id} className="record-card">
                        <div className="record-card-header">
                          <strong>{app.name}</strong>
                          <span>{app.status}</span>
                        </div>
                        <p>{app.summary}</p>
                        <div className="chip-row">
                          <span className="surface-chip">{app.category}</span>
                          <span className="surface-chip">{app.pricing}</span>
                          {app.token_integration ? (
                            <span className="surface-chip">NVT enabled</span>
                          ) : (
                            <span className="surface-chip">fiat only</span>
                          )}
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Developer flow</strong>
                  <div className="chip-row">
                    {(novarideAppStore.app_store?.developer_flow || []).map((step) => (
                      <span key={step} className="surface-chip">
                        {step.replaceAll("_", " ")}
                      </span>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="NovaRide App Store will appear after the app store surface is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Protocol Marketplace">
            {novarideProtocolMarketplace ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>NovaRide App Store</strong>
                    <span>{novarideProtocolMarketplace.status || "governed_beta"}</span>
                  </div>
                  <p>
                    Open protocol listings, SDK publishing, and partner integrations are routed
                    through the governed marketplace surface.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">
                      Storefronts {novarideProtocolMarketplace.marketplace?.metrics?.storefront_count || 0}
                    </span>
                    <span className="surface-chip">
                      Catalog {novarideProtocolMarketplace.marketplace?.metrics?.catalog_count || 0}
                    </span>
                    <span className="surface-chip">
                      Publishing steps{" "}
                      {novarideProtocolMarketplace.marketplace?.metrics?.publishing_step_count || 0}
                    </span>
                    <span className="surface-chip">
                      Trust review{" "}
                      {novarideProtocolMarketplace.marketplace?.developer_program?.trust_review || "required"}
                    </span>
                  </div>
                </article>
                <article className="record-card">
                  <strong>Storefronts</strong>
                  <div className="stack compact-stack">
                    {(novarideProtocolMarketplace.marketplace?.storefronts || []).map((storefront) => (
                      <article key={storefront.key} className="record-card">
                        <div className="record-card-header">
                          <strong>{storefront.name}</strong>
                          <span>{storefront.status}</span>
                        </div>
                        <p>{storefront.purpose}</p>
                        <div className="chip-row">
                          <span className="surface-chip">{storefront.audience}</span>
                          {(storefront.listing_types || []).map((listingType) => (
                            <span key={listingType} className="surface-chip">
                              {listingType.replaceAll("_", " ")}
                            </span>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Developer catalog</strong>
                  <div className="stack compact-stack">
                    {(novarideProtocolMarketplace.marketplace?.catalog || []).map((listing) => (
                      <article key={listing.listing_id} className="record-card">
                        <div className="record-card-header">
                          <strong>{listing.name}</strong>
                          <span>{listing.publish_channel}</span>
                        </div>
                        <p>{listing.purpose}</p>
                        <div className="chip-row">
                          <span className="surface-chip">{listing.role}</span>
                          <span className="surface-chip">{listing.surface_type}</span>
                          {(listing.platforms || []).map((platform) => (
                            <span key={platform} className="surface-chip">
                              {platform}
                            </span>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </article>
                <article className="record-card">
                  <strong>Publishing pipeline</strong>
                  <div className="stack compact-stack">
                    {(novarideProtocolMarketplace.marketplace?.publishing_pipeline || []).map((step) => (
                      <div key={step.step} className="reason-chip">
                        {step.title} - {step.goal}
                      </div>
                    ))}
                  </div>
                </article>
              </div>
            ) : (
              <EmptyState label="Protocol marketplace will appear after the developer marketplace surface is loaded." />
            )}
          </OperatorPanel>

          <OperatorPanel title="Partner Trust Governance">
            {novatechPartnerGovernance ? (
              <div className="stack">
                <article className="record-card">
                  <div className="record-card-header">
                    <strong>Partner trust registry</strong>
                    <span>{novatechPartnerGovernance.organizations?.length || 0} organizations</span>
                  </div>
                  <p>
                    Approval state, trust level, active keys, usage, and SLA enforcement are exposed
                    from the same registry-backed control plane.
                  </p>
                  <div className="chip-row">
                    <span className="surface-chip">Approval governance</span>
                    <span className="surface-chip">SLA enforcement</span>
                    <span className="surface-chip">Usage metering</span>
                    <span className="surface-chip">Monetization</span>
                  </div>
                </article>
                <div className="stack compact-stack">
                  {(novatechPartnerGovernance.organizations || []).slice(0, 4).map((org) => (
                    <article key={org.org_id} className="record-card">
                      <div className="record-card-header">
                        <strong>{org.organization}</strong>
                        <span>{org.status}</span>
                      </div>
                      <p>
                        {org.business_type} | {org.country} | {org.sla_plan} plan |{" "}
                        {org.trust_level} trust
                      </p>
                      <div className="chip-row">
                        <span className="surface-chip">Approval {org.approval_state}</span>
                        <span className="surface-chip">Activation {org.activation_state}</span>
                        <span className="surface-chip">
                          SLA {org.sla?.state || "healthy"}
                        </span>
                        <span className="surface-chip">
                          Billing AUD {Number(org.billing?.estimated_cost_aud || 0).toFixed(2)}
                        </span>
                        <span className="surface-chip">
                          Keys {Array.isArray(org.keys) ? org.keys.length : 0}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState label="Partner trust governance will appear after the trust registry is loaded." />
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

        <OperatorPanel title="Treasury AI">
          <div className="compliance-panel">
            <article className="compliance-score-card">
              <div>
                <strong>{novapayTreasuryIntelligence.risk_level}</strong>
                <span>Risk level</span>
              </div>
              <span
                className={`compliance-status ${
                  novapayTreasuryIntelligence.risk_level === "CRITICAL" ||
                  novapayTreasuryIntelligence.risk_level === "HIGH"
                    ? "fail"
                    : "pass"
                }`}
              >
                Liquidity ratio {novapayTreasuryIntelligence.coverage_ratio}
              </span>
            </article>
            <div className="compliance-summary-grid">
              <article>
                <strong>{novapayTreasuryIntelligence.cash_balance}</strong>
                <span>Cash balance</span>
              </article>
              <article>
                <strong>{novapayTreasuryIntelligence.settlement_obligations}</strong>
                <span>Settlement obligations</span>
              </article>
              <article>
                <strong>{novapayTreasuryIntelligence.prefunding_gap}</strong>
                <span>Prefunding gap</span>
              </article>
              <article>
                <strong>{novapayTreasuryIntelligence.reserve_headroom}</strong>
                <span>Reserve headroom</span>
              </article>
            </div>
            <div className="chip-row">
              {(novapayTreasuryIntelligence.recommendations || []).length > 0 ? (
                novapayTreasuryIntelligence.recommendations.slice(0, 4).map((recommendation) => (
                  <span
                    key={recommendation.recommendation_id || recommendation.title}
                    className="surface-chip"
                  >
                    {recommendation.title || recommendation.action}
                  </span>
                ))
              ) : (
                <span className="surface-chip">No treasury recommendations</span>
              )}
            </div>
            <div className="compliance-rule-list">
              {(novapayTreasuryIntelligence.provider_snapshot || []).slice(0, 4).map((provider) => (
                <article
                  key={`${provider.provider}-${provider.currency}`}
                  className="compliance-rule-row"
                >
                  <div>
                    <strong>{provider.provider}</strong>
                    <span>
                      {provider.current_balance} / {provider.required_balance} · {provider.status}
                    </span>
                  </div>
                  <span className="compliance-status pass">{provider.prefunding_gap}</span>
                </article>
              ))}
              {(novapayTreasuryIntelligence.stress_tests || []).slice(0, 3).map((scenario) => (
                <article key={scenario.scenario} className="compliance-rule-row">
                  <div>
                    <strong>{scenario.scenario}</strong>
                    <span>
                      {scenario.projected_coverage_ratio} coverage · {scenario.mitigation}
                    </span>
                  </div>
                  <span className={`compliance-status ${scenario.impact === "CRITICAL" ? "fail" : "pass"}`}>
                    {scenario.impact}
                  </span>
                </article>
              ))}
            </div>
          </div>
        </OperatorPanel>

        <OperatorPanel title="Global Treasury Intelligence">
          <div className="compliance-panel">
            <article className="compliance-score-card">
              <div>
                <strong>{novapayGlobalTreasuryIntelligence.multi_currency.action}</strong>
                <span>Multi-currency action</span>
              </div>
              <span className="compliance-status pass">
                On-chain coverage {novapayGlobalTreasuryIntelligence.metrics.onchain_coverage}
              </span>
            </article>
            <div className="compliance-summary-grid">
              <article>
                <strong>{novapayGlobalTreasuryIntelligence.multi_currency.fx_exposure}%</strong>
                <span>FX exposure</span>
              </article>
              <article>
                <strong>{novapayGlobalTreasuryIntelligence.multi_currency.stablecoin_ratio}%</strong>
                <span>Stablecoin ratio</span>
              </article>
              <article>
                <strong>{novapayGlobalTreasuryIntelligence.onchain.batch_size}</strong>
                <span>Anchor batch size</span>
              </article>
              <article>
                <strong>{novapayGlobalTreasuryIntelligence.metrics.currency_count}</strong>
                <span>Active currencies</span>
              </article>
            </div>
            <div className="chip-row">
              {(novapayGlobalTreasuryIntelligence.multi_currency.currency_distribution || []).map((entry) => (
                <span key={entry.currency} className="surface-chip">
                  {entry.currency} {entry.share}%
                </span>
              ))}
            </div>
            <div className="chip-row">
              {(novapayGlobalTreasuryIntelligence.multi_currency.hedge_actions || []).map((action) => (
                <span key={action} className="reason-chip">
                  {action}
                </span>
              ))}
            </div>
            <div className="compliance-rule-list">
              {(novapayGlobalTreasuryIntelligence.onchain.anchor_batch_plan || []).slice(0, 4).map((anchor) => (
                <article key={anchor.anchor_id} className="compliance-rule-row">
                  <div>
                    <strong>{anchor.anchor_id}</strong>
                    <span>
                      {anchor.currency} · {anchor.context} · {anchor.amount}
                    </span>
                  </div>
                  <span className="compliance-status pass">{anchor.proof_hash.slice(0, 12)}</span>
                </article>
              ))}
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

function MiniSparkline({ values }) {
  const points = Array.isArray(values) && values.length > 0 ? values : [0, 0];
  const path = buildPolylinePath(points, 120, 34, 3);
  const area = buildAreaPath(points, 120, 34, 3);

  return (
    <svg className="ops-kpi-sparkline" viewBox="0 0 120 34" role="img" aria-label="KPI trend">
      <path className="ops-kpi-sparkline-area" d={area} />
      <path className="ops-kpi-sparkline-line" d={path} />
    </svg>
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
  operatorCityProfitOptimization,
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
