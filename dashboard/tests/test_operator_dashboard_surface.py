from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_operator_dashboard_reads_required_ga_test_endpoints() -> None:
    source = read("src/App.jsx")

    assert 'readJson("/system/health")' in source
    assert 'readJson("/rides/active")' in source
    assert 'readJson("/system/drivers")' in source
    assert 'readJson("/system/replay/health")' in source
    assert 'readJson("/system/evidence")' in source
    assert 'readJson("/system/guards")' in source
    assert 'readJson("/system/trust-metrics")' in source
    assert 'readJson("/system/pilot-metrics")' in source
    assert 'readJson("/v1/ops/observability/dashboard")' in source
    assert 'readJson("/v1/ops/audit/dashboard")' in source
    assert 'readJson("/v1/trust/orgs")' in source
    assert 'readJson("/v1/core-platform/transfers/live-test/readiness")' in source
    assert 'readJson("/v1/treasury/intelligence")' in source
    assert 'readJson("/v1/treasury/global-intelligence")' in source
    assert 'readJson("/v1/economy/protocol")' in source
    assert 'readJson("/v1/novaride/appstore/apps")' in source
    assert 'readJson("/v1/novaride/developer/marketplace")' in source
    assert 'readJson("/v1/novaride/super-app")' in source
    assert 'readJson("/v1/novaride/novaid")' in source
    assert 'readJson("/v1/novaride/novaid/gen-sovereign")' in source
    assert 'readJson("/v1/novaride/novaid/digital-nation")' in source
    assert 'readJson("/v1/novaride/constitution")' in source
    assert 'readJson("/v1/novaride/regulatory-alignment")' in source
    assert 'readJson("/v1/novaride/global-expansion")' in source
    assert 'readJson("/v1/architecture/protocol-marketplace")' in source
    assert 'readJson("/v1/architecture/compliance")' in source
    assert 'readJson("/v1/architecture/remediation")' in source
    assert 'readJson("/v1/architecture/learning")' in source
    assert 'readJson("/v1/architecture/predictive-governance")' in source
    assert 'readJson("/v1/architecture/autonomous-governance")' in source
    assert 'readJson("/v1/novaride/phase11/status")' in source
    assert 'readJson("/v1/novaride/phase12/status")' in source
    assert 'readJson("/v1/novaride/phase13/status")' in source
    assert 'readJson("/v1/operator/autonomy")' in source
    assert 'readJson("/v1/operator/city-automation")' in source
    assert 'readJson("/v1/operator/multi-city-orchestration")' in source
    assert 'readJson("/v1/operator/digital-twin")' in source
    assert 'readJson("/v1/operator/meta-learning-redesign")' in source
    assert 'readJson("/v1/operator/demand-forecast")' in source
    assert 'readJson("/v1/operator/strategy-engine")' in source
    assert 'readJson("/v1/operator/business-pricing")' in source
    assert 'readJson("/v1/operator/city-profit-optimization")' in source
    assert 'readPublicJson("/public/trust/dashboard")' in source
    assert 'readJson("/api/feature-registry")' in source
    assert 'readPublicJson("/public/trust-badge")' in source
    assert 'writeJson("/trust/conversation"' in source


def test_operation_ai_panel_binds_city_profit_optimization_data() -> None:
    source = read("src/App.jsx")
    panel_signature = source.split("function OperationAIDecisionPanel({", 1)[1].split("}) {", 1)[0]

    assert "operatorCityProfitOptimization," in panel_signature
    assert source.count(
        "operatorCityProfitOptimization={operatorCityProfitOptimization}"
    ) == 2


def test_operator_dashboard_sends_test_instrumentation_headers() -> None:
    source = read("src/App.jsx")

    assert "TEST_MODE" in source
    assert "DEVICE_ID" in source
    assert "OPERATOR_ID" in source
    assert "/auth/token" in source
    assert '"Authorization"' in source or "Authorization" in source
    assert '"X-AfriRide-Device-Id"' in source
    assert '"X-AfriRide-App-Version"' in source
    assert '"X-AfriRide-Event-Id"' in source
    assert '"X-AfriRide-Client-Timestamp"' in source


def test_operator_dashboard_is_read_only_surface() -> None:
    source = read("src/App.jsx")

    assert source.count('method: "POST"') == 2
    assert 'writeJson("/trust/conversation"' in source
    assert "override" not in source.lower()
    assert "certify" not in source.lower()
    assert "Replay & Evidence Control" in source


def test_operator_dashboard_uses_api_architecture_contract_not_copied_constants() -> None:
    source = read("src/App.jsx")

    assert "const NOVARIDE_LAYERED_ARCHITECTURE" not in source
    assert "const NOVARIDE_OPERATOR_INTERVENTION_FLOW" not in source
    assert "const NOVARIDE_ENTERPRISE_OPERATIONS_LAYER" not in source
    assert "const NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS" not in source
    assert "novarideEcosystem?.architecture" in source
    assert "novarideArchitecture.layers" in source
    assert "novarideArchitecture.enterprise_operations" in source
    assert "novarideArchitecture.production_readiness" in source
    assert "Array.isArray(novarideArchitecture.layers)" in source
    assert "Array.isArray(novarideArchitecture.operator_intervention_flow)" in source
    assert "Array.isArray(novarideArchitecture.maturity_dimensions)" in source
    assert "Array.isArray(novarideArchitecture.enterprise_operations)" in source
    assert "Array.isArray(novarideArchitecture.production_readiness)" in source
    assert "novarideEcosystem?.ecosystem_platform" in source
    assert "Array.isArray(novarideEcosystemPlatform.compatibility_matrix)" in source
    assert "Array.isArray(novarideEcosystemPlatform.migration_registry)" in source
    assert "Array.isArray(novarideEcosystemPlatform.sdk_registry)" in source
    assert "Object.entries(novarideEcosystemPlatform.operational_metrics || {})" in source
    assert "!Array.isArray(novarideEcosystemPlatform.operational_metrics)" in source
    assert "NovaRide Ecosystem Platform" in source
    assert "unsigned_controlled_contract" in source
    assert "Compatibility Matrix" in source
    assert "Migration Registry" in source
    assert "SDK Registry" in source
    assert "Operational Metrics" in source
    assert "Partner Trust Governance" in source
    assert "Approval governance" in source
    assert "SLA enforcement" in source
    assert "Usage metering" in source
    assert "Monetization" in source
    assert "architecture_contract_pending" not in source


def test_novaride_next_generation_operations_layer_is_implemented() -> None:
    source = read("src/App.jsx")
    styles = read("src/styles.css")

    for required in (
        "NovaRide Operations Layer",
        "Next-generation mobility command center",
        "Live Rides",
        "Active Drivers",
        "Bookings Today",
        "Revenue",
        "Completion Rate",
        "Live Operations Map",
        "Parramatta",
        "North Sydney",
        "Central",
        "South West",
        "Available",
        "Busy",
        "Offline",
        "Live Activity Feed",
        "New ride accepted",
        "Ride picked up",
        "Ride completed",
        "Incident reported",
        "Alerts & Notifications",
        "High Demand Zone",
        "Driver Shortage",
        "System Maintenance",
        "Fleet & Performance Analytics",
        "Utilization Rate",
        "Payment Overview",
        "Treasury AI",
        "Global Treasury Intelligence",
        "DAO Token Economy",
        "NovaToken",
        "Active proposals",
        "Participation",
        "Liquidity ratio",
        "Reserve headroom",
        "On-chain coverage",
        "FX exposure",
        "Stablecoin ratio",
        "Anchor batch size",
        "Payouts",
        "Pending",
        "App Store",
        "NovaRide App Store",
        "NovaRide Super App",
        "Global Super App Shell",
        "Super App dashboard",
        "NovaID Global Identity",
        "Login with NovaID",
        "Digital economic identity",
        "NovaID Gen-Sovereign",
        "Sovereign digital identity and global crypto-financial infrastructure",
        "Sovereign infrastructure layers",
        "SSI credential model",
        "Government + federation adapters",
        "/v1/federation/identity",
        "/v1/federation/payments",
        "/v1/federation/trust",
        "gen_sovereign_is_architecture_and_policy_gated_infrastructure_not_live_state_authority",
        "NovaAI_recommends_only_DAO_and_policy_execute",
        "NovaID Digital Nation",
        "Digital Citizenship + NovaID Passport System",
        "Digital nation boundary",
        "NovaCitizen profile",
        "NovaPassport",
        "NVP-992384",
        "did:nova:00087423",
        "NovaCitizens",
        "AI-assisted decisions",
        "digital_nation_is_platform_citizenship_not_legal_nationality_or_immigration_authority",
        "novapassport_is_platform_access_not_a_legal_travel_document",
        "NovaAI_recommends_only_citizens_and_DAO_execute",
        "NovaRide Digital Constitution",
        "Digital Constitution + Legal Governance Framework",
        "Constitutional principle",
        "Foundational articles",
        "Authority structure",
        "Governance + AI limits",
        "Programmable law",
        "Trust + dispute law",
        "Enforcement + amendment",
        "digital_constitution_is_platform_governance_not_statutory_law_or_regulator_substitute",
        "execution_authority_shall_remain_with_NovaPower_and_authorized_subsystems_only",
        "replay_is_digital_audit_record",
        "NovaRide Regulatory Alignment",
        "Regulatory-Aligned Digital Infrastructure Layer",
        "Legal alignment principle",
        "Regulatory domains",
        "Identity + payments controls",
        "Token + privacy classification",
        "Jurisdiction map",
        "Liability + AI compliance",
        "Compliance engine + risk monitor",
        "regulatory_alignment_is_control_mapping_not_legal_advice_certification_or_regulatory_approval",
        "jurisdiction_aware_policy_enforcement",
        "NovaRide Global Expansion",
        "Global Regulatory Expansion Strategy",
        "Global Core Platform",
        "Regional Compliance Layer",
        "Country-Specific Adaptation",
        "Local Market Deployment",
        "Regulatory ready markets",
        "High growth markets",
        "Complex regulations",
        "Melbourne",
        "Burundi",
        "DRC",
        "East Africa",
        "3-Hub deployment model",
        "Melbourne pilot",
        "Burundi launch",
        "DRC launch",
        "East Africa expansion",
        "Airport transfers and courier logistics with a 1000+ rides/month target.",
        "M-Pesa integration for Kenya, with Rwanda and Uganda next.",
        "airport_transfers",
        "courier_logistics",
        "M_Pesa_integration",
        "mobile_money_payments",
        "1000_plus_rides_per_month",
        "Partner model",
        "Mobile-first economies",
        "Jurisdiction-aware compliance",
        "did:nova:84729",
        "did:nova:847392",
        "NovaAI_recommendations_are_advisory_only",
        "super_app_is_interface_only_backend_services_keep_authority",
        "NovaID_owns_identity_authentication_reputation_device_and_governance_identity",
        "Published apps",
        "Developer flow",
        "Protocol Marketplace",
        "NovaRide Developer Marketplace",
        "Publishing pipeline",
        "Trust review",
        "Trust & Safety Panel",
        "Verified Drivers",
        "Verified Rides",
        "Open Incidents",
        "Quick Actions",
        "Broadcast",
        "Incentives",
        "Heat Map",
        "Reports",
        "Operator Module",
        "Admin Module",
        "Support Module",
        "Inspector Module",
        "Driver + Rider Apps Integration",
        "Platform Ecosystem",
        "NovaID",
        "NovaPay",
        "NovaConnect",
        "NovaHealth",
        "NovaLearn",
        "AI Dispatch Insights Panel",
        "Incident Heatmap Layer",
        "Driver Incentive Automation",
        "Voice Command for Operators",
        "Real-Time Profit Dashboard",
        "Architecture Compliance",
        "Compliance score",
        "/metrics/architecture/compliance",
        "Prometheus Metrics",
        "Grafana Panels",
        "Failed rules trend",
        "API breaking changes",
        "Security violations",
        "Auto-Fix Actions",
        "AI Learning Insights",
        "Predictive Governance",
        "Autonomous Multi-Agent Governance",
        "Proposed fixes",
        "Auto-fix success",
        "Top issue",
        "System risk",
        "Predicted risks",
        "Simulation scenarios",
        "Optimization suggestions",
        "Multi-agent findings",
        "Crisis scenarios",
        "Economic decision",
        "Max crisis risk",
        "Black swan",
        "No refactor suggestions",
        "Human approval required",
        "Self-healing status",
        "No remediation required",
        "Multi-Language AST Validation",
        "semantic_openapi_diff",
        "architecture_anchor_v2_verification",
    ):
        assert required in source

    for required_class in (
        ".novaride-ops-band",
        ".ops-kpi-grid",
        ".ops-command-grid",
        ".ops-map",
        ".ops-map-cluster",
        ".ops-driver-dot",
        ".ops-feed-item",
        ".ops-alert-critical",
        ".ops-chart",
        ".ops-action-button",
        ".compliance-panel",
        ".compliance-score-card",
        ".compliance-rule-row",
    ):
        assert required_class in styles


def test_novaride_modern_ai_operator_dashboard_is_integrated() -> None:
    source = read("src/App.jsx")
    styles = read("src/styles.css")

    for required in (
        "Requests Queue",
        "Incident Count",
        "At Risk",
        "Ride Control Panel",
        "Reassign driver",
        "Cancel ride",
        "Contact driver",
        "Track route",
        "AI Decision Layer",
        "Demand Prediction",
        "Surge Recommendation",
        "Driver Risk Scoring",
        "Fraud Detection",
        "Trigger Surge",
        "Heatmap Boost",
        "Incident Mode",
        "Lock Zone",
        "Unlock Zone",
        "Realtime Architecture",
        "/ws/map/live/",
        "Trust, Replay & Audit",
        "Ride playback",
        "GPS replay",
        "Action audit trail",
        "RBAC & Security",
        "Operator",
        "Senior Operator",
        "Compliance Officer",
        "Operational Intelligence",
        "Backend Modules",
        "OperatorMetricsService",
        "DispatchService",
        "RealtimeGateway",
        "AnalyticsAggregator",
    ):
        assert required in source

    for required_class in (
        ".ops-ai-grid",
        ".ops-platform-grid",
        ".ops-ai-card",
        ".ops-ride-control",
        ".ops-rbac-row",
        ".ops-driver-at-risk",
        ".legend-risk",
    ):
        assert required_class in styles


def test_novatech_core_console_exposes_2026_core_layers_only() -> None:
    source = read("src/App.jsx")

    assert "Unified Trust Operating Console" in source
    assert "Console Wireframes" in source
    assert "NovaTechSol Core Flow" in source
    assert "Identity to authority to execution to payment to proof to intelligence to evolution" in source
    assert "/console/identity" in source
    assert "/console/authority" in source
    assert "/console/payments" in source
    assert "/console/trust" in source
    assert "/console/intelligence" in source
    assert "/console/programming" in source
    assert "NovaID / AfriID" in source
    assert "NovaPower" in source
    assert "NovaPay / AfriPay" in source
    assert "NovaTrust" in source
    assert "NovaScript" in source
    assert "NovaProgramming" in source
    assert "NovaID Command Surface" in source
    assert "NovaPower Policy Surface" in source
    assert "NovaPay Transaction Surface" in source
    assert "NovaTrust Explorer" in source
    assert "NovaScript Intelligence Surface" in source
    assert "NovaProgramming Studio" in source
    assert "NovaTrust Public Explorer UI" in source
    assert "/trust/explorer/:receipt_id" in source
    assert "/v1/core-platform/trust/explorer/:receipt_id" in source
    assert "/v1/core-platform/pilot/flow" in source
    assert "TrustExplorerFrontend" in source
    assert "PDF audit export" in read("src/TrustExplorer.jsx")
    assert "Ed25519 signature" in read("src/TrustExplorer.jsx")
    assert "fetch(`${apiBaseUrl}/v1/core-platform/trust/explorer/${receiptId}`)" in read("src/TrustExplorer.jsx")
    assert "Real-time Auditor Dashboard" in read("src/AuditorDashboard.jsx")
    assert "/trust/auditor/dashboard?ids=" in read("src/AuditorDashboard.jsx")


def test_novapay_role_based_apps_surface_is_declared() -> None:
    source = read("src/App.jsx")
    styles = read("src/styles.css")

    for required in (
        "NovaPay UI/UX Platform",
        "Role-based apps over one governed financial runtime",
        "NovaPay Ecosystem Control Plane",
        "NovaPay Core Control Plane",
        "Transfer Engine, Ledger, Event Platform, Audit & Proof remain central",
        "NovaPay Role-Based Applications",
        "NovaPay Consumer App",
        "NovaPay Agent App",
        "NovaPay Merchant App",
        "NovaPay Business App",
        "NovaPay Operations App",
        "NovaPay Compliance App",
        "NovaPay Support App",
        "NovaPay Administration App",
        "NovaPay Developer Portal",
        "Multi-currency wallet",
        "International remittance",
        "Cash In",
        "Cash Out",
        "QR payments",
        "Bulk payments",
        "Liquidity Dashboard",
        "AML",
        "Sanctions",
        "Receipt verification",
        "License management",
        "Webhook management",
        "Event Explorer",
        "Shared Platform Services",
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
        "Unified Domain Model",
        "Customer",
        "Wallet",
        "Funding Source",
        "Jurisdiction",
        "License",
        "No duplicated business logic in role apps",
        "NovaPay Implementation Roadmap",
        "NovaPay Priority App Build Specifications",
        "NovaPay Merchant and Agent Web Portals",
        "NovaPay Merchant App / Web / Portal",
        "NovaPay Agent App / Web / Portal",
        "merchant_web_portal",
        "agent_web_portal",
        "NovaPay Business App / Portal / Web",
        "NovaPay Operations App / Website",
        "Home balance",
        "Send Money",
        "Beneficiaries",
        "Agent Dashboard",
        "Customer Lookup",
        "KYC Capture",
        "Merchant Dashboard",
        "Receive Payment",
        "QR Display",
        "Merchant Overview",
        "Payment Requests",
        "QR Checkout",
        "Refund Console",
        "Settlement Batches",
        "Merchant Settings",
        "Create QR payment request",
        "Generate invoice",
        "Approve refund",
        "Daily sales root",
        "Agent Overview",
        "Cash In Console",
        "Cash Out Console",
        "Float Ledger",
        "Shift Reconciliation",
        "Field Audit",
        "Open agent shift",
        "Request float top-up",
        "Submit shift proof",
        "Shift reconciliation root",
        "Business Overview",
        "Bulk Payments",
        "Payroll",
        "Operations Overview",
        "Live Transfers",
        "Settlement Queue",
        "Provider Health",
        "POST /v1/transfers/quote",
        "POST /v1/transfers",
        "GET /v1/transfers/{id}/receipt",
        "GET /v1/transfers/{id}/replay",
        "GET /v1/transfers/{id}/audit-package",
        "GET /v1/treasury/snapshot",
        "GET /v1/transfers/{id}/timeline",
        "Quote hash",
        "Replay valid badge",
        "Receipt verifier",
        "Settlement batch hash",
        "KYC evidence hash",
        "Float delta proof",
        "Closing balance proof",
        "Settlement batch",
        "Approval chain",
        "Snapshot root",
        "External verifier result",
    ):
        assert required in source

    assert "novapay-apps-band" in styles
    assert "novapay-app-grid" in styles
    assert "novapay-build-grid" in styles
    assert "novapay-portal-grid" in styles
    assert "roadmap-lane" in styles


def test_operator_dashboard_exposes_required_operator_panels() -> None:
    source = read("src/App.jsx")

    for required in (
        "AfriTech Dashboard",
        "Main Navigation Links",
        "Gateway Responsibilities",
        "Live Data Wiring",
        "Role-Based Surfaces",
        "Deep Linking into Replay / Proof",
        "Cross-System Context Panel",
        "View same ride across AfriRide + AfriProgramming",
        "AfriRide Dashboard",
        "AfroProg Dashboard",
        "AfriProgramming Dashboard",
        "System Health",
        "Replay Health",
        "Evidence Health",
        "Active Rides",
        "Drivers Online",
        "Guard Violations",
        "Trust Metrics",
        "Pilot Metrics",
        "Observability + Audit Dashboards",
        "Observability Dashboard",
        "Audit Dashboard",
        "Shared NovaRide Platform Architecture",
        "/v1/novaride/platform/architecture-contract",
        "Apps = Interface; Platform = Authority",
        "NovaRide Next-Generation Mobility Platform",
        "apps_request_control_plane_decides_events_prove",
        "Rider and Driver apps request and display",
        "Control Plane decides",
        "Execution Plane performs",
        "Event Platform proves",
        "NovaRide Rider App",
        "NovaRide Driver App",
        "NovaRide Operator App / Portal",
        "NovaRide Inspector App / Portal",
        "NovaRide Fleet Portal",
        "NovaRide Merchant Portal",
        "NovaRide Corporate Portal",
        "NovaRide Trust & Safety Portal",
        "NovaRide Customer Support Portal",
        "NovaRide Developer Portal",
        "Live Operations Dashboard",
        "Live Map: rides + drivers",
        "Manual Dispatch Intervention",
        "Demand Heatmap",
        "SOS Escalation",
        "Payment / Receipt Status",
        "Provider Health",
        "Vehicle Inspection",
        "License / Permit Check",
        "Insurance Check",
        "Roadworthiness Checklist",
        "Regulatory Export",
        "Violation / Suspension Workflow",
        "Inspection Registry",
        "Incident Registry",
        "Ride Lifecycle",
        "Demand Forecasting",
        "Driver Position Prediction",
        "ETA Prediction",
        "Dynamic Pricing",
        "Dispatch Optimization",
        "Verification Package",
        "NovaRide Enterprise Operations Layer",
        "10/10 enterprise operations depth",
        "novarideEcosystem?.enterprise_operations_classification",
        "Enterprise Operations: 10/10",
        "Evidence-backed operations",
        "novarideArchitecture.version",
        "novarideEnterpriseOperationsLayer",
        "novarideProductionInfrastructureReadiness",
        "novarideMaturityDimensions",
        "Layered architecture",
        "novarideLayeredArchitecture",
        "Governed intervention flow",
        "novarideOperatorInterventionFlow",
        "displayArchitectureToken",
        "Production infrastructure readiness",
        "resilience_regulatory_external_verification",
        "Shared services",
        "Authority boundary",
        "Ride request flow",
        "dispatch_decisions",
        "NovaRide Operator Command Center",
        "/v1/novaride/operator/dashboard-contract",
        "Operations decision layer",
            "Operation AI Decision Dashboard",
            "Dispatch posture",
            "Operator move",
            "Mobility signals",
            "Predictive AI and autonomous execution thresholds",
            "Autonomous budget allocation + profit optimization",
            "Autonomy thresholds",
            "Driver auto-allocation",
            "Predictive positioning",
            "City AI Automation",
            "Multi-City Orchestration",
            "Real-time Digital Twin",
            "Meta-learning redesign",
            "Predictive Demand ML",
            "Real-time analytics dashboard",
            "Phase 5",
            "Autonomous Strategy Engine",
            "Strategy Guardrails",
            "Business layer pricing + incentives",
            "Global Learning",
            "Self-improving AI loop",
            "zero_operator_mode",
            "global_zero_operator",
            "safe_to_autorun",
        "Safety & Emergency",
        "Support & Escalation",
        "direct_payment_execution",
        "NovaRide Fleet Manager",
        "/v1/novaride/fleet/manager-contract",
        "Fleet Management",
        "Maintenance & Compliance",
        "Financial Management",
        "direct_payment_provider_access",
        "NovaRide Business Portal",
        "/v1/novaride/business/portal-contract",
        "Corporate Travel Management",
        "Approval Workflow",
        "Business Wallet & Billing",
        "Department Budgets",
        "pricing_rule_bypass",
        "NovaRide Admin",
        "/v1/novaride/admin/contract",
        "User & Role Management",
        "Driver & Vehicle Approval",
        "Pricing & Service Configuration",
        "Geography & Service Zones",
        "Compliance & Audit",
        "manual_payment_processing",
        "NovaRide Inspector App",
        "/v1/novaride/inspector/app-contract",
        "Inspection Workflow",
        "Driver Verification",
        "Vehicle Inspection",
        "Photo & Evidence Capture",
        "Trust_Engine_final_authority",
        "NovaRide Support",
        "/v1/novaride/support/contract",
        "Customer Ticket Management",
        "Ride Lookup & Investigation",
        "Refund & Dispute Handling",
        "Escalation Management",
        "NovaPay_backend_only",
        "Phase 11 Compliance & Inspection",
        "Support Dashboard UI",
        "Auto Ticket Classification",
        "Auto Refund System",
        "Analytics Backend",
        "Driver Scoring Algorithm",
        "Document Verification",
        "Inspection Reports",
        "Regulatory Readiness",
        "Phase 12 Multi-City & Global Scaling",
        "Phase 13 Global Execution & AWS",
        "Global Deployment Plan",
        "Controlled AI Decision Engine",
        "AWS Production Infra",
        "Real Execution Layer",
        "AI Optimization",
        "Controlled actions",
        "Auto Pricing Adjustments",
        "Live Incentives Tuning",
        "NovaConnect Expansion",
        "NovaPay Expansion",
        "Global Deployment",
        "Multi-City Management",
        "Geo-Fencing",
        "Currency Support",
        "Localization",
        "Region-Based Pricing",
        "Distributed Infrastructure",
        "Auto Decision Engine",
        "Fraud Prediction Models",
        "Driver Incentives Optimization",
        "Global Learning",
        "NovaRide Partner Portal",
        "/v1/novaride/partner/portal-contract",
        "Ride Booking & Widget Integration",
        "Guest Transport Management",
        "Bulk Ride Requests",
        "Billing & Payments",
        "direct_payment_processing",
        "NovaRide App Ecosystem",
        "/v1/novaride/ecosystem",
        "NovaRide Passenger",
        "NovaRide Inspector",
        "NovaRide Partner",
        "NovaRide Finance Portal",
        "NovaRide Executive Dashboard",
        "NovaRide Unified UI Framework",
        "Native app activation",
        "Agentic AI modules",
        "AgentRecommendationPanel",
        "ReplayTimeline",
        "NovaPay_backend_only",
        "Operator Alert Rules",
        "Enterprise Readiness Review",
        "Governed Feature Registry Dashboard",
        "Feature Registry Status",
        "Feature Claims",
        "Registry Enforcement",
        "Trust Badge System",
        "Verified by AfriTech Trust Layer",
        "Public Badge",
        "Verify System Integrity",
        "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY",
        "FEATURE_REGISTRY_LEVEL_12",
        "REPLAY_DERIVED_EVIDENCE_PROJECTION",
        "driver-identity-proof",
        "trip-integrity-proof",
        "payment-proof-anchor",
        "EVIDENCE_VALIDATED",
        "BOUNDARY_GUARDED",
        "/api/feature-registry",
        "/public/trust-badge",
        "/public/ecosystem-evolution/verify",
        "Production-ready verification features remain read-only",
        "NovaPay MFS Live Test",
        "MFS Africa / Onafriq",
        "Money movement",
    ):
        assert required in source


def test_operator_dashboard_externalization_surfaces_are_replay_backed() -> None:
    source = read("src/App.jsx")

    for required in (
        "Replay-Backed Externalization Layer",
        "Multi-Region Topology",
        "Multi-Tenant Isolation",
        "External Anchor Commitments",
        "Partner Proof Surface",
        "projection(replay(trace_events))",
    ):
        assert required in source


def test_operator_dashboard_exposes_trust_explorer_and_commercial_surfaces() -> None:
    source = read("src/App.jsx")

    for required in (
        "Public Registry + Verification Visualization",
        "Public Trust Dashboard",
        "Sepolia → Mainnet Promotion",
        "Package Verifier CLI for External Users",
        "Deploy Public Trust Dashboard UI",
        "Run First External Partner Verification Session",
        "Trust Explorer Registry",
        "Verification Visualization",
        "First 5 Partners",
        "Monetization Surface",
        "registry publication is evidence indexing",
        "Protocol components",
    ):
        assert required in source


def test_operator_dashboard_exposes_architecture_compliance_surfaces() -> None:
    source = read("src/App.jsx")

    for required in (
        "Architecture Compliance Dashboard",
        "System adherence to architecture",
        "Architecture Test Status",
        "System Adherence to Architecture",
        "Declared Architecture Components",
        "Drift Detection Report",
        "New modules not in architecture",
        "Orphan components",
        "Undocumented flows",
        "AfriCPPT protocol extraction",
    ):
        assert required in source


def test_operator_dashboard_exposes_afriprog_workspace_surfaces() -> None:
    source = read("src/App.jsx")

    for required in (
        "AfriPro / NovaCodePro Workspace",
        "NovaCodePro Phase Roadmap",
        "Phase 0",
        "SaaS foundation",
        "Phase 12",
        "NovaCodePro OS",
        "Project Explorer",
        "Chat / AI Assistant Panel",
        "Code Editor (Live Editing + Execution)",
        "Prompt-Based Coding",
        "Context Awareness",
        "Multi-Mode Chat",
        "Code mode",
        "Debug mode",
        "Analysis mode",
        "Monaco Editor",
        "Django Backend for AfriPro / NovaCodePro Chat + Dashboard",
        "NovaCodePro Prompt Studio",
        "NovaCodePro Controls",
        "Natural Language to Code",
        "Code Autocomplete",
        "Multi-language Support",
        "Context Awareness",
        "Code Explanation",
        "Testing & Debugging",
        "API Integration",
        "Prompt / Instruction Panel",
        "Output / Code Window",
        "Model Settings",
        "Project Context / Files",
        "Version / History",
        "Integration Panel",
        "proposal-only",
        "AfriProgramming, replay, and governance still decide what becomes real execution",
        "Send to Governance",
        "Rejected by Governance",
        "Replay-Backed Reasoning Panel",
        "Demo Walkthrough Mode",
        "This failed because replay invariant",
        "Explicit proposal submission",
        "Next boundary step",
    ):
        assert required in source


def test_operator_dashboard_exposes_novacodepro_developer_platform_phase() -> None:
    source = read("src/App.jsx")
    styles = read("src/styles.css")

    for required in (
        "NovaCodePro Developer Platform Phase",
        "Build. Govern. Deploy. Verify.",
        "Trusted Engineering",
        "Developer Platform phase for IDEs, repos, docs, and AI coding",
        "claiming full Engineering OS production readiness",
        "NovaCloud IDE",
        "NovaCodePro Desktop",
        "NovaCodePro Mobile",
        "NovaGit",
        "NovaAI Coding",
        "NovaDocs",
        "Developer Templates",
        "Developer Command Center",
        "Create Workspace",
        "Generate Code",
        "Pull Request",
        "Evidence Ready",
        "React",
        "Django",
        "FastAPI",
        "Flutter",
        "Node.js",
        "Python",
        "macOS",
        "Windows",
        "Linux",
        "NovaRide App",
        "NovaPay App",
        "NovaID Service",
        "NovaTrust Verifier",
    ):
        assert required in source

    for required in (
        "selectedWorkspaceTemplate",
        "selectedRepositoryId",
        "activeAiCodingTab",
        "activeDocsCategory",
        "workspaceFlowStep",
        "NOVACODEPRO_TRUST_WORKFLOW",
    ):
        assert required in source

    for required in (
        ".codepro-developer-platform",
        ".novacloud-ide-grid",
        ".novagit-grid",
        ".ai-assistant-panel",
        ".docs-selector-row",
        ".trust-aware-workflow",
    ):
        assert required in styles


def test_operator_dashboard_exposes_novacodepro_engineering_platform_phase() -> None:
    source = read("src/App.jsx")
    styles = read("src/styles.css")

    for required in (
        "NovaCodePro Engineering Platform Phase",
        "Engineering Platform phase",
        "Controlled deployment",
        "Evidence-ready release",
        "not full GA",
        "NovaFlow CI/CD",
        "NovaSecurity",
        "NovaDeploy",
        "NovaMonitor",
        "NovaTelemetry",
        "Pipeline dashboard",
        "Security dashboard",
        "Deployment control center",
        "Observability dashboard",
        "Engineering Command Center",
        "Start Release Journey",
        "Release Verified",
        "Security Passed",
        "Deployment Approved",
        "Monitoring Healthy",
        "Evidence Ready",
        "Pipeline evidence",
        "Security evidence",
        "Deployment evidence",
        "Monitoring evidence",
        "Approval evidence",
        "Audit trail",
        "Commit",
        "Pipeline",
        "Security",
        "Approval",
        "Deploy",
        "Monitor",
        "SAST results",
        "DAST results",
        "Secret scanning",
        "Dependency scanning",
        "Container scanning",
        "SBOM status",
        "License compliance",
        "Docker",
        "Kubernetes",
        "AWS",
        "Azure",
        "Google Cloud",
        "on-premise",
        "edge",
    ):
        assert required in source

    for required in (
        "selectedPipelineId",
        "selectedDeploymentEnvironment",
        "selectedMonitoringService",
        "releaseJourneyActive",
        "releaseJourneyStep",
        "NOVACODEPRO_RELEASE_JOURNEY",
        "NOVACODEPRO_RELEASE_EVIDENCE",
    ):
        assert required in source

    for required in (
        ".codepro-engineering-platform",
        ".engineering-command-shell",
        ".engineering-pipeline-grid",
        ".security-scan-grid",
        ".deployment-control-grid",
        ".monitor-grid",
        ".release-journey-grid",
        ".release-evidence-grid",
        ".engineering-status-grid",
    ):
        assert required in styles


def test_operator_dashboard_exposes_novacodepro_enterprise_platform_phase() -> None:
    source = read("src/App.jsx")
    styles = read("src/styles.css")

    for required in (
        "NovaCodePro Enterprise Platform Phase",
        "Enterprise Command Center",
        "Multi-Tenant SaaS",
        "Organization Management",
        "Identity & Access",
        "Governance Center",
        "Compliance Center",
        "Enterprise Billing",
        "Marketplace Administration",
        "Enterprise Procurement & License Management",
        "Audit Center",
        "Executive Reporting",
        "Enterprise AI Assistant",
        "Enterprise Trust Dashboard",
        "Overall Enterprise Trust Score",
        "Marketplace Revenue Share",
        "Partner Programs",
        "Verified Publisher",
        "Trusted Extensions",
        "Organizations",
        "Enterprise Users",
        "Monthly Builds",
        "Compliance Score",
        "Trust Score",
        "Marketplace Revenue",
        "Recent activity",
        "Approval queue",
        "Risk indicators",
        "Governance notifications",
        "Tenant",
        "Business Units",
        "Workspaces",
        "Repositories",
        "Pipelines",
        "Deployments",
        "Marketplace",
        "Billing",
        "Evidence",
        "SSO",
        "OIDC",
        "SAML",
        "SCIM",
        "MFA",
        "API Keys",
        "Personal Access Tokens",
        "Service Accounts",
        "Robot Accounts",
        "Session Management",
        "RBAC",
        "Owner",
        "Administrator",
        "Platform Admin",
        "Engineering Manager",
        "Developer",
        "Reviewer",
        "Auditor",
        "Security",
        "Read Only",
        "ISO 27001",
        "SOC 2",
        "GDPR",
        "PCI DSS",
        "HIPAA",
        "NIST",
        "CIS Controls",
        "OWASP",
        "Free",
        "Professional",
        "Business",
        "Enterprise",
        "Government",
        "PDF",
        "DOCX",
        "XLSX",
        "CSV",
        "NovaCloud IDE",
        "NovaGit",
        "NovaAI",
        "NovaFlow",
        "NovaDeploy",
        "NovaSecurity",
        "NovaMonitor",
        "NovaTelemetry",
        "NovaDocs",
        "NovaMarketplace",
        "NovaTrust",
        "NovaID",
        "does not claim full GA readiness",
    ):
        assert required in source

    for required in (
        "activeEnterpriseTab",
        "selectedEnterpriseOrg",
        "selectedEnterpriseDepartment",
        "selectedEnterpriseProject",
        "selectedMarketplaceCategory",
        "selectedComplianceFramework",
        "selectedBillingPlan",
        "selectedGovernanceApproval",
        "selectedAuditFilter",
        "selectedExecutiveReport",
    ):
        assert required in source

    for required in (
        ".codepro-enterprise-platform",
        ".enterprise-command-shell",
        ".enterprise-metric-grid",
        ".tenant-hierarchy-grid",
        ".enterprise-admin-grid",
        ".enterprise-iam-grid",
        ".enterprise-governance-flow",
        ".enterprise-billing-grid",
        ".marketplace-admin-grid",
        ".audit-event-grid",
        ".enterprise-trust-grid",
    ):
        assert required in styles
