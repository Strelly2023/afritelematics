def generate_proof(decision):
    return {
        "action": decision.action,
        "allowed": decision.allowed,
        "justification": decision.reason,
    }