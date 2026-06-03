def enforce_prediction_boundary(source):
    if source == "prediction":
        return {
            "authority": "non_authoritative",
            "allowed_effect": "recommendation_only",
        }

    return {
        "authority": "requires_replay_or_policy",
        "allowed_effect": "bounded_execution",
    }
