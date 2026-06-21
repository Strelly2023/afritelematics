from __future__ import annotations

from hashlib import sha256
from typing import Any


class GlobalTrustNetwork:
    def __init__(self) -> None:
        self._members: dict[str, dict[str, Any]] = {}

    def join(self, *, organization_id: str, trust_domain: str, trust_score: int) -> dict[str, Any]:
        member = {
            "organization_id": organization_id,
            "trust_domain": trust_domain,
            "trust_score": max(0, min(100, int(trust_score))),
            "member_hash": sha256(f"{organization_id}:{trust_domain}:{trust_score}".encode()).hexdigest(),
        }
        self._members[organization_id] = member
        return member

    def status(self) -> dict[str, Any]:
        return {
            "mode": "global_trust_network",
            "member_count": len(self._members),
            "members": sorted(self._members.values(), key=lambda item: item["organization_id"]),
        }


class TokenizedTrustEconomy:
    def mint(self, *, organization_id: str, receipt_hash: str, trust_score: int) -> dict[str, Any]:
        units = max(0, int(trust_score))
        token_hash = sha256(f"{organization_id}:{receipt_hash}:{units}".encode()).hexdigest()
        return {
            "mode": "tokenized_trust_economy",
            "token_id": "trusttok-" + token_hash[:12],
            "organization_id": organization_id,
            "receipt_hash": receipt_hash,
            "trust_units": units,
            "transfer_policy": "non_transferable_attestation",
            "token_hash": token_hash,
        }


class AutonomousSelfUpgradeEngine:
    def plan(self, *, project_id: str, assurance: dict[str, Any], risk: dict[str, Any]) -> dict[str, Any]:
        needs_upgrade = assurance.get("assurance_status") != "assured" or int(risk.get("risk_score", 0)) >= 60
        plan_hash = sha256(f"{project_id}:{assurance.get('assurance_status')}:{risk.get('risk_score')}".encode()).hexdigest()
        return {
            "mode": "autonomous_self_upgrading_system",
            "upgrade_plan_id": "upgrade-" + plan_hash[:12],
            "project_id": project_id,
            "upgrade_required": needs_upgrade,
            "governance_gate": "policy_and_receipt_required",
            "steps": ["detect_drift", "propose_patch", "verify_receipt", "request_governance_approval"],
        }


_DEFAULT_GLOBAL_TRUST_NETWORK = GlobalTrustNetwork()
_DEFAULT_TRUST_ECONOMY = TokenizedTrustEconomy()
_DEFAULT_SELF_UPGRADE = AutonomousSelfUpgradeEngine()


def get_global_trust_network() -> GlobalTrustNetwork:
    return _DEFAULT_GLOBAL_TRUST_NETWORK


def get_tokenized_trust_economy() -> TokenizedTrustEconomy:
    return _DEFAULT_TRUST_ECONOMY


def get_autonomous_self_upgrade_engine() -> AutonomousSelfUpgradeEngine:
    return _DEFAULT_SELF_UPGRADE
