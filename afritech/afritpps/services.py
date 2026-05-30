"""AfriTPPS GA Elite execution services."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from afritech.afritpps.constants import (
    AFRITPPS_COMPONENT,
    AFRITPPS_PILLAR,
    AFRITPPS_STATUS,
    OUTPUTS,
    QUESTION_ANSWERED,
    constitutional_afritpps_metadata,
)
from afritech.afritpps.metrics import build_program_metric_bundle
from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
)


def build_program_from_mappings(
    program_id: str,
    name: str,
    capabilities: Iterable[Mapping[str, object]],
    workflows: Iterable[Mapping[str, object]],
) -> AfriTPPSProgram:
    return AfriTPPSProgram(
        program_id=program_id,
        name=name,
        capabilities=tuple(
            AfriTPPSCapability.from_mapping(payload) for payload in capabilities
        ),
        workflows=tuple(AfriTPPSWorkflow.from_mapping(payload) for payload in workflows),
    )


def build_operational_model(program: AfriTPPSProgram) -> dict[str, object]:
    metrics = build_program_metric_bundle(program)

    return {
        "component": AFRITPPS_COMPONENT,
        "pillar": AFRITPPS_PILLAR,
        "status": AFRITPPS_STATUS,
        "question_answered": QUESTION_ANSWERED,
        "outputs": OUTPUTS,
        "constitution": constitutional_afritpps_metadata(),
        "program": program.canonical_dict(),
        "execution_metrics": metrics.canonical_dict(),
        "defines_execution": True,
        "creates_governance_authority": False,
        "creates_proof_authority": False,
        "creates_replay_authority": False,
        "mutates_proof": False,
    }


__all__ = [
    "build_program_from_mappings",
    "build_operational_model",
]
