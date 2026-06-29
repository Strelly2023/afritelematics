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
    assert 'readJson("/v1/core-platform/transfers/live-test/readiness")' in source
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
    ):
        assert required in source

    assert "novapay-apps-band" in styles
    assert "novapay-app-grid" in styles
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
