from afritech_v1.shared.decision import Decision

def evaluate(action: str) -> Decision:
    if action == "WRITE":
        return Decision(action, True, "WRITE allowed in v0")
    return Decision(action, False, "Action not allowed")