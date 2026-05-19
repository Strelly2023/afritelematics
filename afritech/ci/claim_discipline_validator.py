from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "afritech/constitution/CLAIM_DISCIPLINE.yaml"
REQUIRED_CLAIM_FIELDS = {
    "id",
    "statement",
    "scope",
    "evidence",
    "validator",
    "counter_test",
}
REQUIRED_SURFACE_FIELDS = {
    "id",
    "surface",
    "compression_target",
    "complexity_justification",
}
FORBIDDEN_READINESS_FLAGS = {
    "global_deployment_readiness_claimed",
    "production_survivability_claimed",
    "distributed_byzantine_consensus_claimed",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_policy() -> dict[str, Any]:
    payload = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("claim discipline policy must be a mapping")
    return payload


def validate_forbidden_terms(
    text: str,
    forbidden_terms: list[str],
    *,
    context: str,
) -> None:
    lowered = text.lower()
    for term in forbidden_terms:
        if term.lower() in lowered:
            fail(f"forbidden claim term in {context}: {term}")


def validate_core_rules(payload: dict[str, Any]) -> None:
    rules = payload.get("core_rules")
    if not isinstance(rules, list) or len(rules) != 3:
        fail("claim discipline must define exactly three core rules")

    required_rules = {
        "No expansion without compression.",
        "No claim without executable evidence.",
        "No proof without a harder counter-test waiting behind it.",
    }
    discovered = {rule.get("rule") for rule in rules if isinstance(rule, dict)}
    if discovered != required_rules:
        fail("claim discipline core rules mismatch")


def validate_claims(
    payload: dict[str, Any],
    forbidden_terms: list[str],
) -> None:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        fail("claim discipline must define claims")

    for claim in claims:
        if not isinstance(claim, dict):
            fail("claim entries must be mappings")

        missing = REQUIRED_CLAIM_FIELDS - set(claim)
        if missing:
            fail(f"{claim.get('id', '<unknown>')} missing fields: {sorted(missing)}")

        if not claim["scope"]:
            fail(f"{claim['id']} has empty scope")

        evidence = claim["evidence"]
        if not isinstance(evidence, list) or not evidence:
            fail(f"{claim['id']} must bind executable evidence")

        if claim["validator"] != "afritech.ci.claim_discipline_validator":
            fail(f"{claim['id']} must bind to claim discipline validator")

        if not claim["counter_test"]:
            fail(f"{claim['id']} must name a harder counter-test")

        validate_forbidden_terms(
            str(claim["statement"]),
            forbidden_terms,
            context=claim["id"],
        )


def validate_new_surfaces(payload: dict[str, Any]) -> None:
    surfaces = payload.get("new_surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        fail("claim discipline must define new surfaces")

    for surface in surfaces:
        if not isinstance(surface, dict):
            fail("new surface entries must be mappings")

        missing = REQUIRED_SURFACE_FIELDS - set(surface)
        if missing:
            fail(f"{surface.get('id', '<unknown>')} missing fields: {sorted(missing)}")

        if not surface["compression_target"] and not surface["complexity_justification"]:
            fail(
                f"{surface['id']} must define compression target or "
                "complexity justification"
            )


def validate_readiness_boundary(payload: dict[str, Any]) -> None:
    boundary = payload.get("readiness_boundary")
    if not isinstance(boundary, dict):
        fail("claim discipline must define readiness boundary")

    for flag in FORBIDDEN_READINESS_FLAGS:
        if boundary.get(flag) is not False:
            fail(f"forbidden readiness claim must remain false: {flag}")


def validate() -> None:
    payload = load_policy()

    if payload.get("schema") != "afritech.constitution.claim_discipline.v1":
        fail("claim discipline schema mismatch")

    classification = payload.get("allowed_classification")
    if not isinstance(classification, str) or not classification.strip():
        fail("claim discipline must define allowed classification")

    forbidden_terms = payload.get("forbidden_claim_terms")
    if not isinstance(forbidden_terms, list) or not forbidden_terms:
        fail("claim discipline must define forbidden claim terms")

    validate_forbidden_terms(
        classification,
        forbidden_terms,
        context="allowed_classification",
    )
    validate_core_rules(payload)
    validate_claims(payload, forbidden_terms)
    validate_new_surfaces(payload)
    validate_readiness_boundary(payload)


def main() -> int:
    try:
        validate()
        print("✅ Claim discipline validation PASSED")
        print("✅ Claims scoped, evidenced, validator-bound, and counter-tested")
        print("✅ New surfaces declare compression or complexity justification")
        print("✅ Global readiness claims remain forbidden")
        return 0
    except Exception as exc:
        print(f"❌ Claim discipline validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
