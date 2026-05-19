"""Validate the global CI completeness policy."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import ROOT, fail, load_yaml, main_result


POLICY = ROOT / "afritech/ci/completeness_policy.yaml"
EXPECTED_RULES = {
    "COMP_001",
    "COMP_002",
    "COMP_003",
    "COMP_004",
    "COMP_005",
}


def validate() -> None:
    payload = load_yaml(POLICY)
    if payload.get("schema") != "afritech.ci.completeness.v1":
        fail("completeness policy schema mismatch")

    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        fail("completeness policy must declare rules")

    discovered: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            fail("completeness policy rule entries must be mappings")
        rule_id = rule.get("id")
        discovered.add(rule_id)
        if not isinstance(rule.get("rule"), str) or not rule["rule"].strip():
            fail(f"{rule_id} must define rule text")
        enforced_by = rule.get("enforced_by")
        if not isinstance(enforced_by, list) or not enforced_by:
            fail(f"{rule_id} must define enforced_by")
        for module in enforced_by:
            if not isinstance(module, str) or not module.startswith("afritech."):
                fail(f"{rule_id} has invalid enforcement module: {module}")

    if discovered != EXPECTED_RULES:
        fail(
            "completeness policy rules mismatch: "
            f"missing={sorted(EXPECTED_RULES - discovered)} "
            f"extra={sorted(discovered - EXPECTED_RULES)}"
        )

    failure = payload.get("failure")
    if not isinstance(failure, dict):
        fail("completeness policy must define failure")
    if failure.get("block_merge") is not True:
        fail("completeness policy must block merge on failure")
    if failure.get("severity") != "CRITICAL":
        fail("completeness policy severity must be CRITICAL")

    print("✅ Completeness policy validation PASSED")
    print(f"✅ Completeness rules enforced: {len(rules)}")


def main() -> int:
    return main_result("Completeness policy validation", validate)


if __name__ == "__main__":
    sys.exit(main())
