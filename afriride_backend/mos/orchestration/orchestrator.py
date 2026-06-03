from mos.optimization.scoring import rank_journey_options
from mos.policies.services import evaluate_mobility_policy
from mos.scheduling.services import add_journey_segment, create_journey, journey_projection


class MobilityOrchestrator:
    """Plan coordinated journeys without certifying segment truth."""

    def __init__(self, policies=None):
        self.policies = policies or []

    def plan_journey(self, request):
        for policy in self.policies:
            policy_result = evaluate_mobility_policy(policy, request)
            if not policy_result["allowed"]:
                return {
                    "planned": False,
                    "reason": policy_result["reason"],
                    "authority": "policy_blocked_coordination",
                }

        options = request.get("options", [])
        ranked_options = rank_journey_options(options)
        selected = ranked_options[0] if ranked_options else None

        if selected is None:
            return {
                "planned": False,
                "reason": "no_journey_option_available",
                "authority": "coordination_projection",
            }

        journey = create_journey(
            user_id=request["user_id"],
            metadata={
                "request": request,
                "selected_option": selected,
                "authority": "journey_plan_projection",
            },
        )

        for index, segment in enumerate(selected.get("segments", [])):
            add_journey_segment(
                journey=journey,
                segment_type=segment["segment_type"],
                sequence=index,
                start_location=segment["start_location"],
                end_location=segment["end_location"],
                evidence_reference=segment.get("evidence_reference", ""),
            )

        return {
            "planned": True,
            "journey": journey_projection(journey),
            "selected_option": selected,
            "authority": "coordination_projection",
        }
