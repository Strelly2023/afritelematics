CRITICAL_FRAUD_THRESHOLD = 1


def has_critical_fraud_event(fraud_flags):
    return fraud_flags >= CRITICAL_FRAUD_THRESHOLD


def safety_status(fraud_flags):
    if has_critical_fraud_event(fraud_flags):
        return {
            "status": "blocked",
            "reason": "critical_fraud_event_detected",
        }

    return {
        "status": "clear",
        "reason": None,
    }
