"""Admissibility checks for entropy-bound execution."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent


@dataclass(frozen=True)
class AdmissibilityDecision:
    admitted: bool
    reason: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
        }


def check_admissibility(event: NormalizedEntropyEvent) -> AdmissibilityDecision:
    if event.corrupted:
        return AdmissibilityDecision(False, event.corruption_reason or "corrupted")
    if not event.identity_id.startswith(("driver.", "rider.", "system.")):
        return AdmissibilityDecision(False, "identity_resolution_violation")
    return AdmissibilityDecision(True, "admissible")
