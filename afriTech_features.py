"""Canonical AfriTech feature summary.

This module is intentionally static and side-effect free. It can be imported by
docs, dashboards, or CLI tools without activating runtime or pilot behavior.
"""

from __future__ import annotations


SYSTEM_STATUS = {
    "classification": "CONTROLLED_PILOT_READY_SYSTEM",
    "live_pilot_authorized": False,
    "production_proven": False,
    "economic_activation_allowed": False,
}


FEATURES = [
    {
        "name": "Trust Kernel",
        "use": "Anchors events, evidence bundles, replay verification, and state truth.",
    },
    {
        "name": "AfriTPPS Execution",
        "use": "Executes domain operations through governed contracts.",
    },
    {
        "name": "Cross-Domain Orchestration",
        "use": "Coordinates verified operations across multiple AfriTech domains.",
    },
    {
        "name": "Federation",
        "use": "Supports signed node communication and independent verification.",
    },
    {
        "name": "Resilience Hardening",
        "use": "Handles consensus failure, malicious nodes, replay divergence, and isolation.",
    },
    {
        "name": "AfriPower Intelligence",
        "use": "Provides advisory-only prediction, risk scoring, and anomaly suggestions.",
    },
    {
        "name": "Governance Chain",
        "use": "Enforces ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI integrity.",
    },
    {
        "name": "Classification CI",
        "use": "Blocks false production, live deployment, and economic maturity claims.",
    },
    {
        "name": "Pilot Gates",
        "use": "Keeps AfriRide pilot execution evidence-gated and controlled.",
    },
    {
        "name": "Domain Surfaces",
        "use": "Defines bounded surfaces for AfriRide, AfriConnectTL, AfriEats, and AfriPay.",
    },
    {
        "name": "Legal Evidence Export",
        "use": "Packages replayable evidence for jurisdiction-aware review.",
    },
    {
        "name": "Operational Tooling",
        "use": "Provides CLI, inspectors, validators, and pilot readiness checks.",
    },
]


def feature_names() -> list[str]:
    return [feature["name"] for feature in FEATURES]


def status_summary() -> str:
    return (
        f"{SYSTEM_STATUS['classification']} "
        f"(live_pilot_authorized={SYSTEM_STATUS['live_pilot_authorized']}, "
        f"production_proven={SYSTEM_STATUS['production_proven']})"
    )


if __name__ == "__main__":
    print(status_summary())
    for feature in FEATURES:
        print(f"- {feature['name']}: {feature['use']}")
