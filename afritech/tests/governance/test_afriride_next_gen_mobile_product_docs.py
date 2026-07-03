from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "docs/api/AFRIRIDE_NEXT_GEN_MOBILE_API_CONTRACT.md"
WIREFRAMES = ROOT / "docs/mobile/AFRIRIDE_NEXT_GEN_UI_WIREFRAMES.md"
BUILD = ROOT / "docs/mobile/AFRIRIDE_REACT_NATIVE_APP_STORE_BUILD_PLAN.md"
NOVARIDE_ECOSYSTEM = ROOT / "docs/architecture/NOVARIDE_NEXT_GENERATION_ECOSYSTEM.md"


def test_next_gen_mobile_api_contract_covers_trust_native_rider_and_driver_endpoints() -> None:
    text = API.read_text(encoding="utf-8")

    for required in (
        "NEXT-GEN RIDER AND DRIVER API CONTRACT",
        "Mobile apps must never finalize receipts",
        "POST /v1/rider/rides",
        "GET /v1/rider/rides/{ride_id}/receipt",
        "GET /v1/rider/rides/{ride_id}/replay",
        "GET /v1/driver/{driver_id}/ride-queue",
        "POST /v1/driver/rides/{ride_id}/complete",
        "GET /v1/operator/dashboard",
        "Replay Exceptions",
        "Public Verification Status",
        "GET /public/trust/{receipt_id}",
        "GET /public/trust/{receipt_id}/package",
        "state_transition_rejected",
    ):
        assert required in text


def test_next_gen_wireframes_define_figma_level_rider_driver_surfaces() -> None:
    text = WIREFRAMES.read_text(encoding="utf-8")

    for required in (
        "FIGMA-LEVEL MOBILE WIREFRAME SPEC",
        "Rider / 01 Booking",
        "Rider / 04 Receipt",
        "Driver / 01 Availability",
        "Driver / 03 Trip Lifecycle",
        "Operator / 01 Dashboard",
        "TrustBadge",
        "LifecycleRail",
        "MetricCard",
        "Verify this ride",
        "Download Verification Package",
        "The app displays proof results; it does not create proof authority.",
    ):
        assert required in text


def test_react_native_app_store_build_plan_is_pilot_gated() -> None:
    text = BUILD.read_text(encoding="utf-8")

    for required in (
        "APP STORE READY BUILD PLAN",
        "rider_app  -> AfriRide Rider",
        "driver_app -> AfriRide Driver",
        "npm run typecheck",
        "pytest -q rider_app/tests driver_app/tests",
        "EXPO_PUBLIC_AFRIRIDE_API_URL",
        "TestFlight",
        "Google Play internal testing",
        "App Store Submission Assets",
        "pilot reviewer notes with test rider and driver credentials",
        "demo receipt ID for public verification review",
        "Do not submit if any condition exists",
        "AfriRide is already approved for public production release.",
    ):
        assert required in text


def test_novaride_next_generation_ecosystem_is_architecture_reference_not_transcript() -> None:
    text = NOVARIDE_ECOSYSTEM.read_text(encoding="utf-8")

    for required in (
        "Version: 2026.07",
        "## Executive Summary",
        "## Architecture Invariants",
        "User interfaces SHALL NOT execute business authority.",
        "Every public contract SHALL be versioned.",
        "## Runtime Guarantees",
        "deterministic request handling",
        "## Application Ecosystem",
        "NovaRide Passenger / Rider App",
        "## Shared Platform Services",
        "NovaPower",
        "NovaRide Core",
        "NovaTrust",
        "NovaAI",
        "NovaData",
        "NovaCloud",
        "## Architecture Layers",
        "## Authority Model",
        "### Authority Matrix",
        "| Payments | NovaPay | Read-only consumers |",
        "## System Truth Model",
        "NovaRide Core owns operational truth for rides.",
        "Only authoritative systems may mutate their domain.",
        "## Unified UI Framework",
        "## Agentic AI",
        "### AI Operational Rules",
        "AI modules SHALL NOT:",
        "Execution authority SHALL remain with NovaPower and the designated",
        "## Security",
        "### Security Principles",
        "All access MUST be authenticated.",
        "All sensitive actions MUST be replay-verifiable.",
        "All security controls SHALL be centrally enforced through NovaPower policies.",
        "### Trust Enforcement",
        "All receipts MUST be verifiable through NovaTrust.",
        "Blockchain anchoring MAY be used for proof immutability where required by trust or compliance policies.",
        "Applications MUST NOT:",
        "## Public APIs",
        "NovaRide exposes a contract-driven API system.",
        "### API Guarantees",
        "All public APIs SHALL:",
        "Breaking changes MUST follow the Version Policy.",
        "### Contract Enforcement",
        "Clients MUST NOT rely on undocumented behavior.",
        "considered non-authoritative.",
        "## Contract Integrity",
        "Contracts MUST be versioned.",
        "API tests enforce contract shape.",
        "## Version Policy",
        "Minor versions are additive only.",
        "## Production Readiness",
        "Production systems SHALL preserve invariant guarantees under load, failure, and",
        "| Payments (NovaPay) | Production | Auditable, reconciled, settlement-safe |",
        "### Production Definition",
        "A component is considered Production only if:",
        "## Verification",
        "### Verification Categories",
        "API contract validation",
        "### Verification Scope",
        "security compliance",
        "backward compatibility",
        "### Verification Requirements",
        "Each release MUST:",
        "maintain trust verification integrity",
        "### Verification Principle",
        "Architecture invariants remain intact.",
        "## Architecture Compliance Checklist",
        "- [ ] Authority boundaries preserved",
        "- [ ] Contracts versioned and validated",
        "- [ ] Security policies enforced through NovaPower",
        "## Related Architecture Decisions",
        "ADR-005 - AI Governance",
        "## Documentation Governance",
        "This document is the canonical NovaRide architecture specification.",
        "It SHALL NOT contain:",
        "Violations of these rules SHALL be treated as architecture defects.",
        "## Maintenance Rules",
        "Keep `NovaRide Passenger` and `Rider App` aligned as one customer app surface.",
    ):
        assert required in text

    for forbidden in (
        "docker compose",
        "git status",
        "pytest ",
        "Traceback",
        "implementation transcript",
    ):
        assert forbidden not in text
