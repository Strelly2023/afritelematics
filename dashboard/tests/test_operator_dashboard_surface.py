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
    assert 'readPublicJson("/public/trust/dashboard")' in source
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
        "Operator Alert Rules",
        "Enterprise Readiness Review",
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
        "AfriProg Workspace",
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
        "Django Backend for AfriPro Chat + Dashboard",
        "AfriProg Prompt Studio",
        "AfriProg Controls",
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
