def evaluate_mobility_policy(policy, journey_request):
    rules = policy.rules or {}
    max_cost = rules.get("max_travel_cost")
    requested_cost = journey_request.get("estimated_cost")

    if max_cost is not None and requested_cost is not None and requested_cost > max_cost:
        return {
            "allowed": False,
            "reason": "max_travel_cost_exceeded",
            "authority": "policy_constraint",
        }

    approved_modes = rules.get("approved_modes")
    requested_modes = journey_request.get("requested_modes", [])
    if approved_modes and any(mode not in approved_modes for mode in requested_modes):
        return {
            "allowed": False,
            "reason": "mode_not_approved",
            "authority": "policy_constraint",
        }

    return {
        "allowed": True,
        "reason": None,
        "authority": "policy_constraint",
    }
