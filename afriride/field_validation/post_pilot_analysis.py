"""Post-pilot evidence analysis protocol for AfriRide.

This protocol evaluates collected pilot evidence after execution. It does not
create replay truth or claim that a pilot has been completed.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from afriride.field_validation.day_one_runbook import (
    EVIDENCE_CHECKPOINTS,
    RUNBOOK_BOUNDARY,
    build_day_one_runbook,
)
from afriride.field_validation.live_pilot_protocol import REQUIRED_SCENARIOS


ANALYSIS_BOUNDARY = (
    "Post-pilot analysis evaluates submitted evidence only. It does not define "
    "truth, certify production readiness, or convert pilot completion into "
    "public launch authority."
)

CORE_QUESTION = (
    "Did the collected pilot evidence remain replay-compatible, complete, "
    "admissibility-bound, and claim-bounded?"
)

ALLOWED_PASS_CLAIM = (
    "AfriRide pilot evidence is accepted as bounded evidence that the sealed "
    "proof stack remained reproducible during the analyzed pilot window."
)

NON_CLAIMS = (
    "production_ready",
    "public_launch_ready",
    "regulatory_approved",
    "market_validated",
    "fleet_scale_validated",
    "long_duration_validated",
)

REQUIRED_ANALYSIS_GATES = (
    "trace_manifest_complete",
    "replay_equivalence_verified",
    "identity_consistency_verified",
    "pricing_consistency_verified",
    "admissibility_consistency_verified",
    "dispute_reproducibility_verified",
    "proof_dashboard_healthy",
    "non_claims_preserved",
)

REQUIRED_DECISIONS = ("accepted", "deferred", "rejected")


class PostPilotAnalysisError(ValueError):
    """Raised when post-pilot analysis violates its proof boundary."""


@dataclass(frozen=True)
class AnalysisGate:
    name: str
    pass_condition: str
    failure_action: str

    def __post_init__(self) -> None:
        if self.name not in REQUIRED_ANALYSIS_GATES:
            raise PostPilotAnalysisError(f"unknown analysis gate: {self.name}")
        if not self.pass_condition:
            raise PostPilotAnalysisError("analysis gate pass condition is required")
        if not self.failure_action.startswith(("reject", "defer")):
            raise PostPilotAnalysisError("analysis gate failure must reject or defer")

    def canonical_dict(self) -> dict[str, str]:
        return {
            "failure_action": self.failure_action,
            "name": self.name,
            "pass_condition": self.pass_condition,
        }


@dataclass(frozen=True)
class PostPilotAnalysisProtocol:
    runbook_hash: str
    gates: tuple[AnalysisGate, ...]
    authority_boundary: str = ANALYSIS_BOUNDARY
    core_question: str = CORE_QUESTION
    non_claims: tuple[str, ...] = NON_CLAIMS
    decisions: tuple[str, ...] = REQUIRED_DECISIONS

    def __post_init__(self) -> None:
        if self.authority_boundary != ANALYSIS_BOUNDARY:
            raise PostPilotAnalysisError("post-pilot analysis boundary mismatch")
        if self.core_question != CORE_QUESTION:
            raise PostPilotAnalysisError("post-pilot core question mismatch")
        if set(NON_CLAIMS).difference(self.non_claims):
            raise PostPilotAnalysisError("post-pilot non-claims incomplete")
        if self.decisions != REQUIRED_DECISIONS:
            raise PostPilotAnalysisError("post-pilot decision set mismatch")
        if len(self.runbook_hash) != 64:
            raise PostPilotAnalysisError("post-pilot analysis requires runbook hash")
        gate_names = tuple(gate.name for gate in self.gates)
        if gate_names != REQUIRED_ANALYSIS_GATES:
            raise PostPilotAnalysisError("post-pilot analysis gates incomplete")

    @property
    def analysis_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "allowed_pass_claim": ALLOWED_PASS_CLAIM,
            "authority_boundary": self.authority_boundary,
            "core_question": self.core_question,
            "decisions": list(self.decisions),
            "evidence_inputs": list(EVIDENCE_CHECKPOINTS),
            "gates": [gate.canonical_dict() for gate in self.gates],
            "non_claims": list(self.non_claims),
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "runbook_boundary": RUNBOOK_BOUNDARY,
            "runbook_hash": self.runbook_hash,
            "schema": "afriride.post_pilot_analysis_protocol.v1",
        }
        if include_hash:
            payload["analysis_hash"] = self.analysis_hash
        return payload


def build_post_pilot_analysis_protocol() -> PostPilotAnalysisProtocol:
    runbook = build_day_one_runbook()
    return PostPilotAnalysisProtocol(
        runbook_hash=runbook.runbook_hash,
        gates=(
            AnalysisGate(
                name="trace_manifest_complete",
                pass_condition="all required evidence checkpoints are present and hash-bound",
                failure_action="defer claim until missing evidence is supplied",
            ),
            AnalysisGate(
                name="replay_equivalence_verified",
                pass_condition="field replay equals simulated baseline replay for every scenario",
                failure_action="reject evidence package for replay mismatch",
            ),
            AnalysisGate(
                name="identity_consistency_verified",
                pass_condition="identity resolves identically across all submitted traces",
                failure_action="reject evidence package for identity inconsistency",
            ),
            AnalysisGate(
                name="pricing_consistency_verified",
                pass_condition="pricing outputs match replay-derived authority",
                failure_action="reject evidence package for pricing deviation",
            ),
            AnalysisGate(
                name="admissibility_consistency_verified",
                pass_condition="admissibility decisions match admitted and rejected events",
                failure_action="reject evidence package for admissibility divergence",
            ),
            AnalysisGate(
                name="dispute_reproducibility_verified",
                pass_condition="dispute support decisions reproduce from replay authority only",
                failure_action="reject evidence package for dispute mismatch",
            ),
            AnalysisGate(
                name="proof_dashboard_healthy",
                pass_condition="dashboard reports proof health without influencing replay truth",
                failure_action="defer claim until dashboard artifact is regenerated and validated",
            ),
            AnalysisGate(
                name="non_claims_preserved",
                pass_condition="analysis output contains no production, launch, regulatory, or market claims",
                failure_action="reject evidence package for claim boundary violation",
            ),
        ),
    )


def write_post_pilot_analysis_protocol(
    output_path: str | Path = "reports/afriride_live_pilot_protocol_v1/post_pilot_analysis.json",
) -> PostPilotAnalysisProtocol:
    protocol = build_post_pilot_analysis_protocol()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(protocol.canonical_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return protocol


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
