"""AfriTPPS execution metrics."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.afritpps.constants import (
    AFRITPPS_COMPONENT,
    AFRITPPS_PILLAR,
    EXECUTION_METRIC_TYPES,
    MATURITY_LEVELS,
    METRIC_CLASSIFICATION,
)
from afritech.afritpps.models import AfriTPPSCapability, AfriTPPSProgram


class AfriTPPSMetricError(ValueError):
    """Raised when AfriTPPS metric data is invalid."""


MATURITY_SCORES = {
    maturity: index + 1 for index, maturity in enumerate(MATURITY_LEVELS)
}


@dataclass(frozen=True)
class AfriTPPSExecutionMetric:
    """Immutable execution metric."""

    metric_type: str
    value: int | float
    unit: str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.metric_type not in EXECUTION_METRIC_TYPES:
            raise AfriTPPSMetricError(f"unsupported metric_type: {self.metric_type}")
        if not isinstance(self.value, (int, float)):
            raise AfriTPPSMetricError("metric value must be numeric")
        if not self.unit:
            raise AfriTPPSMetricError("metric unit is required")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "classification": METRIC_CLASSIFICATION,
            "metric_type": self.metric_type,
            "label": self.label or self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "defines_execution": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


@dataclass(frozen=True)
class AfriTPPSMetricBundle:
    """Immutable bundle of execution metrics."""

    metrics: tuple[AfriTPPSExecutionMetric, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "component": AFRITPPS_COMPONENT,
            "pillar": AFRITPPS_PILLAR,
            "metric_count": len(self.metrics),
            "metrics": tuple(metric.canonical_dict() for metric in self.metrics),
            "defines_execution": True,
            "creates_governance_authority": False,
            "creates_proof_authority": False,
            "creates_replay_authority": False,
            "mutates_proof": False,
        }


def calculate_readiness_score(
    capabilities: tuple[AfriTPPSCapability, ...],
) -> float:
    if not capabilities:
        raise AfriTPPSMetricError("readiness requires at least one capability")

    total = sum(MATURITY_SCORES[item.maturity_level] for item in capabilities)
    maximum = len(capabilities) * len(MATURITY_LEVELS)
    return round((total / maximum) * 100, 2)


def build_program_metric_bundle(program: AfriTPPSProgram) -> AfriTPPSMetricBundle:
    if not isinstance(program, AfriTPPSProgram):
        raise AfriTPPSMetricError("expected AfriTPPSProgram")

    readiness = calculate_readiness_score(program.capabilities)

    return AfriTPPSMetricBundle(
        metrics=(
            AfriTPPSExecutionMetric(
                metric_type="capability_count",
                value=len(program.capabilities),
                unit="count",
                label="Capability count",
            ),
            AfriTPPSExecutionMetric(
                metric_type="workflow_count",
                value=len(program.workflows),
                unit="count",
                label="Workflow count",
            ),
            AfriTPPSExecutionMetric(
                metric_type="readiness_score",
                value=readiness,
                unit="percent",
                label="Readiness score",
            ),
        )
    )


__all__ = [
    "AfriTPPSExecutionMetric",
    "AfriTPPSMetricBundle",
    "AfriTPPSMetricError",
    "calculate_readiness_score",
    "build_program_metric_bundle",
]
