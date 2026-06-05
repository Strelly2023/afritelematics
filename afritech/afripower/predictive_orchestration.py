"""Read-only predictive orchestration suggestions for AfriPower."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.afripower.contracts.read_only_contract import assert_read_only_contract
from afritech.afritpps.orchestration import AfriTPPSOrchestrationIntent, OrchestrationStep


@dataclass(frozen=True)
class RankedExecutionOption:
    name: str
    score: float
    risk: str
    rationale: str


@dataclass(frozen=True)
class PredictiveOrchestrationRecommendation:
    intent: AfriTPPSOrchestrationIntent
    ranked_options: tuple[RankedExecutionOption, ...]
    anomalies: tuple[str, ...]
    advisory_only: bool = True
    execution_authority: bool = False

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intent": {
                "orchestration_id": self.intent.orchestration_id,
                "name": self.intent.name,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "domain": step.domain,
                        "operation": step.operation,
                        "dependencies": list(step.dependencies),
                    }
                    for step in self.intent.operations
                ],
            },
            "ranked_options": [
                {
                    "name": option.name,
                    "score": option.score,
                    "risk": option.risk,
                    "rationale": option.rationale,
                }
                for option in self.ranked_options
            ],
            "anomalies": list(self.anomalies),
            "advisory_only": self.advisory_only,
            "execution_authority": self.execution_authority,
        }


@dataclass(frozen=True)
class PatternLearningReport:
    common_flows: tuple[str, ...]
    failure_points: tuple[str, ...]
    latency_profiles: dict[str, str]
    read_only: bool = True


@dataclass(frozen=True)
class RiskScore:
    failure_probability: float
    dependency_risk: str
    verification_delay: str
    explanation: str
    execution_authority: bool = False


def suggest_orchestration(context: dict[str, Any]) -> PredictiveOrchestrationRecommendation:
    assert_read_only_contract()
    last_event = str(context.get("last_event") or "")
    actor_id = str(context.get("actor_id") or "actor:unknown")
    ride_id = str(context.get("ride_id") or "ride:unknown")
    driver_id = str(context.get("driver_id") or actor_id)

    if last_event == "TripCompleted":
        intent = _driver_post_trip_intent(actor_id=actor_id, driver_id=driver_id, ride_id=ride_id)
        anomalies = _detect_missing_expected_steps(context)
        return PredictiveOrchestrationRecommendation(
            intent=intent,
            ranked_options=(
                RankedExecutionOption(
                    name="post_trip_work_health_flow",
                    score=0.91,
                    risk="low",
                    rationale="TripCompleted commonly leads to work logging and health check.",
                ),
            ),
            anomalies=anomalies,
        )

    return PredictiveOrchestrationRecommendation(
        intent=AfriTPPSOrchestrationIntent(
            orchestration_id="suggestion.noop",
            name="No eligible orchestration suggestion",
            operations=(),
            policy_context={"source": "AfriPower", "advisory_only": True},
        ),
        ranked_options=(
            RankedExecutionOption(
                name="no_action",
                score=1.0,
                risk="none",
                rationale="No matching predictive rule.",
            ),
        ),
        anomalies=(),
    )


def detect_anomalies(context: dict[str, Any]) -> tuple[str, ...]:
    assert_read_only_contract()
    return _detect_missing_expected_steps(context)


def learn_patterns(events: tuple[dict[str, Any], ...]) -> PatternLearningReport:
    assert_read_only_contract()
    transitions: dict[str, int] = {}
    failure_points: list[str] = []
    previous = ""
    for event in events:
        event_type = str(event.get("event_type") or "")
        status = str(event.get("status") or "")
        if previous and event_type:
            key = f"{previous}->{event_type}"
            transitions[key] = transitions.get(key, 0) + 1
        if status.lower() in {"failed", "timeout", "blocked"} and event_type:
            failure_points.append(event_type)
        if event_type:
            previous = event_type

    common = tuple(
        key for key, _ in sorted(transitions.items(), key=lambda item: (-item[1], item[0]))
    )
    return PatternLearningReport(
        common_flows=common,
        failure_points=tuple(sorted(set(failure_points))),
        latency_profiles={"default": "unknown_without_timestamps"},
    )


def score_risk(intent: AfriTPPSOrchestrationIntent) -> RiskScore:
    assert_read_only_contract()
    step_count = len(intent.operations)
    dependency_count = sum(len(step.dependencies) for step in intent.operations)
    failure_probability = min(0.05 + (step_count * 0.03) + (dependency_count * 0.04), 0.95)
    dependency_risk = "high" if dependency_count > step_count else "medium" if dependency_count else "low"
    verification_delay = "medium" if step_count > 3 else "low"
    return RiskScore(
        failure_probability=round(failure_probability, 2),
        dependency_risk=dependency_risk,
        verification_delay=verification_delay,
        explanation=explain_suggestion(intent),
    )


def explain_suggestion(intent: AfriTPPSOrchestrationIntent) -> str:
    assert_read_only_contract()
    domains = sorted({step.domain for step in intent.operations})
    return (
        f"Recommended as advisory-only plan across {', '.join(domains) or 'no domains'} "
        f"with {len(intent.operations)} proposed steps. Execution remains AfriTPPS-controlled."
    )


def _driver_post_trip_intent(
    *,
    actor_id: str,
    driver_id: str,
    ride_id: str,
) -> AfriTPPSOrchestrationIntent:
    return AfriTPPSOrchestrationIntent(
        orchestration_id=f"suggestion.post_trip.{ride_id}",
        name="Suggested post-trip driver flow",
        operations=(
            OrchestrationStep(
                step_id="work_completed",
                domain="AfriTalent",
                operation="WorkCompleted",
                actor_id=actor_id,
                subject_id=f"work:{ride_id}",
                payload={"worker_id": driver_id, "work_id": ride_id},
                signature={"signature_mode": "development_adapter"},
                dependencies=(),
            ),
            OrchestrationStep(
                step_id="health_check",
                domain="AfriHealth",
                operation="HealthCheckTriggered",
                actor_id="operator:health",
                subject_id=f"health:{driver_id}",
                payload={"driver_id": driver_id, "reason": "post_trip_check"},
                signature={"signature_mode": "development_adapter"},
                dependencies=(),
            ),
        ),
        policy_context={"source": "AfriPower", "advisory_only": True},
    )


def _detect_missing_expected_steps(context: dict[str, Any]) -> tuple[str, ...]:
    expected = set(context.get("expected_next_steps") or ())
    observed = set(context.get("observed_steps") or ())
    missing = tuple(sorted(expected - observed))
    return tuple(f"missing_expected_step:{step}" for step in missing)
