from afritech.governance.policy.policy_models import PolicyDecision, PolicyRule


class PolicyEngineError(Exception):
    pass


class PolicyRulesEngine:

    def __init__(self):
        self.rules = []

        # Register default rules
        self._register_default_rules()

    # -----------------------------------------------------------------
    # ADD RULE
    # -----------------------------------------------------------------

    def add_rule(self, rule: PolicyRule):
        self.rules.append(rule)

    # -----------------------------------------------------------------
    # EVALUATE ADR
    # -----------------------------------------------------------------

    def evaluate(self, adr):

        for rule in self.rules:

            try:
                if rule.condition_fn(adr):
                    return {
                        "decision": rule.decision,
                        "rule": rule.name
                    }

            except Exception:
                continue

        # Default behavior
        return {
            "decision": PolicyDecision.REQUIRE_VOTE,
            "rule": "default_fallback"
        }

    # -----------------------------------------------------------------
    # DEFAULT RULES
    # -----------------------------------------------------------------

    def _register_default_rules(self):

        # ✅ 1. AUTO-APPROVE: minor drift
        def minor_drift_rule(adr):
            return adr["drift_report"].get("details", {}).get("comparison") == "hash_only"

        self.add_rule(PolicyRule(
            name="minor_drift_auto_approve",
            condition_fn=minor_drift_rule,
            decision=PolicyDecision.APPROVE
        ))

        # ✅ 2. AUTO-REJECT: critical kernel mismatch
        def kernel_violation_rule(adr):
            return adr["context"].get("kernel_hash") is None

        self.add_rule(PolicyRule(
            name="kernel_integrity_violation",
            condition_fn=kernel_violation_rule,
            decision=PolicyDecision.REJECT
        ))

        # ✅ 3. REQUIRE VOTE: default complex change
        def default_rule(_):
            return True

        self.add_rule(PolicyRule(
            name="fallback_requires_vote",
            condition_fn=default_rule,
            decision=PolicyDecision.REQUIRE_VOTE
        ))