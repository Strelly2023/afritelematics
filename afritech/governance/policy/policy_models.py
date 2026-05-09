class PolicyDecision:
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUIRE_VOTE = "REQUIRE_VOTE"


class PolicyRule:

    def __init__(self, name, condition_fn, decision):
        """
        condition_fn(adr) -> bool
        decision: APPROVE | REJECT | REQUIRE_VOTE
        """
        self.name = name
        self.condition_fn = condition_fn
        self.decision = decision
