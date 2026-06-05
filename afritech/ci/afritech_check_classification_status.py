from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any


# ============================================================
# ✅ SYSTEM SIGNALS MODEL
# ============================================================

@dataclass(frozen=True)
class SystemSignals:
    """
    Canonical system signals.

    These MUST reflect real system state.
    No assumptions allowed.
    """

    constitutional_pass: bool
    replay_valid: bool
    proof_surface_valid: bool
    consensus_valid: bool

    hardening_implemented: bool
    adversarial_implemented: bool
    multi_domain_validation: bool

    observability_ready: bool
    deployment_control_ready: bool
    app_surface_ready: bool

    controlled_pilot_prepared: bool
    live_pilot_authorized: bool
    production_proven: bool


# ============================================================
# ✅ CLASSIFICATION ENGINE (CORE)
# ============================================================

class ClassificationEngine:
    """
    GA-Elite Classification Engine

    Guarantees:
    - Truth-bound classification
    - No overclaiming
    - Governance enforcement
    """

    def __init__(self, signals: SystemSignals):
        self.signals = signals

    # ---------------------------------------------------------
    # Primary Classification
    # ---------------------------------------------------------

    def classify(self) -> Dict[str, Any]:
        """
        Returns full classification state.
        """

        self._validate_signals()

        return {
            "tier": self._determine_tier(),
            "architecture": "Replay-Governed Constitutional Platform",
            "state": self._determine_state(),
            "layers": self._layer_status(),
            "truth_boundary": self._truth_boundary(),
            "allowed_claims": self._allowed_claims(),
            "forbidden_claims": self._forbidden_claims(),
            "missing_evidence": self._missing_evidence(),
        }

    # ---------------------------------------------------------
    # Tier Determination
    # ---------------------------------------------------------

    def _determine_tier(self) -> str:
        if self.signals.constitutional_pass:
            return "GA++++ Elite"
        return "INVALID"

    # ---------------------------------------------------------
    # State Determination
    # ---------------------------------------------------------

    def _determine_state(self) -> str:
        if self.signals.production_proven:
            return "PRODUCTION_PROVEN_SYSTEM"

        if self.signals.live_pilot_authorized:
            return "LIVE_PILOT_SYSTEM"

        if self.signals.controlled_pilot_prepared:
            return "CONTROLLED_PILOT_READY_SYSTEM"

        return "PRE_PILOT_SYSTEM"

    # ---------------------------------------------------------
    # Layer Status
    # ---------------------------------------------------------

    def _layer_status(self) -> Dict[str, str]:
        return {
            "constitutional": self._status(self.signals.constitutional_pass),
            "replay": self._status(self.signals.replay_valid),
            "proof": self._status(self.signals.proof_surface_valid),
            "consensus": self._status(self.signals.consensus_valid),

            "hardening": self._status(self.signals.hardening_implemented),
            "adversarial": self._status(self.signals.adversarial_implemented),
            "multi_domain": self._status(self.signals.multi_domain_validation),

            "observability": self._status(self.signals.observability_ready),
            "deployment_control": self._status(self.signals.deployment_control_ready),
            "app_surface": self._status(self.signals.app_surface_ready),
        }

    # ---------------------------------------------------------
    # Truth Boundary (CRITICAL)
    # ---------------------------------------------------------

    def _truth_boundary(self) -> Dict[str, bool]:
        return {
            "live_pilot_authorized": self.signals.live_pilot_authorized,
            "production_proven": self.signals.production_proven,
        }

    # ---------------------------------------------------------
    # Allowed Claims
    # ---------------------------------------------------------

    def _allowed_claims(self) -> List[str]:
        claims = []

        if self.signals.constitutional_pass:
            claims.append("Constitutionally valid system")

        if self.signals.replay_valid:
            claims.append("Replay-verifiable execution")

        if self.signals.adversarial_implemented:
            claims.append("Adversarially tested")

        if self.signals.multi_domain_validation:
            claims.append("Multi-domain validated")

        if self.signals.controlled_pilot_prepared:
            claims.append("Pilot-ready system")

        return claims

    # ---------------------------------------------------------
    # Forbidden Claims
    # ---------------------------------------------------------

    def _forbidden_claims(self) -> List[str]:
        forbidden = []

        if not self.signals.production_proven:
            forbidden.append("Production-proven system")
            forbidden.append("Economically validated platform")
            forbidden.append("Guaranteed real-world reliability")

        if not self.signals.live_pilot_authorized:
            forbidden.append("Live public deployment")
            forbidden.append("Open-scale operations")

        return forbidden

    # ---------------------------------------------------------
    # Missing Evidence
    # ---------------------------------------------------------

    def _missing_evidence(self) -> List[str]:
        missing = []

        if not self.signals.production_proven:
            missing.extend([
                "real-device behavior validation",
                "economic interaction validation",
                "long-duration operational continuity",
            ])

        return missing

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def _status(self, flag: bool) -> str:
        return "COMPLETE" if flag else "INCOMPLETE"

    # ---------------------------------------------------------
    # Signal Validation (SAFEGUARD)
    # ---------------------------------------------------------

    def _validate_signals(self) -> None:
        """
        Prevent impossible or illegal states.
        """

        if self.signals.production_proven and not self.signals.live_pilot_authorized:
            raise RuntimeError(
                "Invalid state: production_proven without live_pilot_authorized"
            )

        if self.signals.live_pilot_authorized and not self.signals.controlled_pilot_prepared:
            raise RuntimeError(
                "Invalid state: live pilot authorized without pilot preparation"
            )

        if not self.signals.constitutional_pass:
            raise RuntimeError(
                "Invalid system: constitutional validation failed"
            )


# ============================================================
# ✅ CLI ENTRY POINT
# ============================================================

def run_classification(signals: Dict[str, bool]) -> None:
    """
    Run classification from dict input.
    """

    model = SystemSignals(**signals)
    engine = ClassificationEngine(model)

    result = engine.classify()

    print("\n🔍 AFRITECH SYSTEM CLASSIFICATION")
    print("=" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 60)


# ============================================================
# ✅ DEFAULT TEST RUN (SAFE BASELINE)
# ============================================================

if __name__ == "__main__":

    signals = {
        "constitutional_pass": True,
        "replay_valid": True,
        "proof_surface_valid": True,
        "consensus_valid": True,

        "hardening_implemented": True,
        "adversarial_implemented": True,
        "multi_domain_validation": True,

        "observability_ready": True,
        "deployment_control_ready": True,
        "app_surface_ready": True,

        "controlled_pilot_prepared": True,
        "live_pilot_authorized": False,
        "production_proven": False,
    }

    run_classification(signals)