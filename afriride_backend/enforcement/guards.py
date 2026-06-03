def decide_enforcement_action(trust_score, fraud_flags):
    if fraud_flags >= 3:
        return "manual_review_required"

    if trust_score < 20:
        return "suspend_pending_review"

    if trust_score < 40:
        return "limited_access"

    return "allow"


def enforcement_boundary(action):
    if action in {"manual_review_required", "limited_access", "suspend_pending_review"}:
        return {
            "authority": "policy_guard_required",
            "allowed_effect": action,
            "irreversible": False,
        }

    return {
        "authority": "allow",
        "allowed_effect": "none",
        "irreversible": False,
    }
