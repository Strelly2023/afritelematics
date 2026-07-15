"""Replay side-effect firewall."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.common.errors import AuthorityDenied


BLOCKED_REPLAY_EFFECTS = {
    "novapay_execution",
    "novaid_mutation",
    "novatrust_duplicate_evidence",
    "push_notification_delivery",
    "sms_delivery",
    "email_delivery",
    "emergency_service_contact",
    "driver_dispatch",
    "rider_booking_confirmation_delivery",
    "external_webhook",
    "analytics_duplication",
    "ai_recommendation_execution",
}


@dataclass(frozen=True, slots=True)
class ReplayExecutionContext:
    replay_mode: bool = True
    external_effects_allowed: bool = False
    notification_delivery: bool = False
    payment_execution: bool = False
    dispatch_execution: bool = False
    evidence_duplication: bool = False

    def assert_allowed(self, effect: str) -> None:
        if self.replay_mode and effect in BLOCKED_REPLAY_EFFECTS:
            raise AuthorityDenied(f"replay_side_effect_blocked:{effect}")
        if not self.external_effects_allowed and effect in BLOCKED_REPLAY_EFFECTS:
            raise AuthorityDenied(f"external_effect_blocked:{effect}")
