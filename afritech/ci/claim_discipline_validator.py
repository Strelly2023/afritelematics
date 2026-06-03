from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml
# afritech.ci.claim_discipline_validator

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "afritech/constitution/CLAIM_DISCIPLINE.yaml"
BINDINGS = ROOT / "afritech/constitution/CLAIM_EVIDENCE_BINDINGS.yaml"
IMPLEMENTATION_REGISTRY = ROOT / "afritech/architecture/implementation_registry.yaml"
REQUIRED_CLAIM_FIELDS = {
    "id",
    "statement",
    "scope",
    "evidence",
    "validator",
    "counter_test",
    "falsification_tests",
    "lineage",
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
REQUIRED_COMPRESSION_KEYS = {
    "schema",
    "objective",
    "minimal_basis",
    "reductions",
}
REQUIRED_NEGATIVE_CAPABILITY_FIELDS = {
    "id",
    "cannot_claim",
    "reason",
}
REQUIRED_BINDING_FIELDS = {
    "id",
    "status",
    "statement",
    "scope",
    "evidence",
    "implementation_refs",
    "validators",
    "non_claims",
}
EXPECTED_BINDING_CLAIMS = (
    "continuity_under_simulated_disruption",
    "deterministic_replay",
    "identity_and_coordination_continuity",
    "enforcement_integrity",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_policy() -> dict[str, Any]:
    payload = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("claim discipline policy must be a mapping")
    return payload


def load_bindings() -> dict[str, Any]:
    payload = yaml.safe_load(BINDINGS.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("claim evidence bindings must be a mapping")
    return payload


'''def load_implementation_registry() -> dict[str, Any]:
    payload = yaml.safe_load(IMPLEMENTATION_REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("implementation registry must be a mapping")
    return payload
'''
def load_implementation_registry() -> dict[str, Any]:
    """
    Load the canonical implementation registry.

    Preferred path:
        use registry_loader if available.

    Fallback path:
        deterministically compose the split registries.
    """

    try:
        from afritech.architecture.registry_loader import (  # type: ignore
            load_implementation_registry as composed_loader,
        )

        payload = composed_loader()

        if not isinstance(payload, dict):
            fail("registry_loader returned non-mapping implementation registry")

        return payload

    except ModuleNotFoundError:
        payload = yaml.safe_load(
            IMPLEMENTATION_REGISTRY.read_text(encoding="utf-8")
        )

        if not isinstance(payload, dict):
            fail("implementation registry must be a mapping")

        architecture_dir = IMPLEMENTATION_REGISTRY.parent

        sub_modules = architecture_dir / "sub_modules_registry.yaml"
        sub_enforcement = architecture_dir / "sub_enforcement_registry.yaml"

        if sub_modules.exists():
            modules_payload = yaml.safe_load(
                sub_modules.read_text(encoding="utf-8")
            )

            if not isinstance(modules_payload, dict):
                fail("sub modules registry must be a mapping")

            payload["implementations"] = modules_payload.get(
                "implementations",
                {},
            )

        if sub_enforcement.exists():
            enforcement_payload = yaml.safe_load(
                sub_enforcement.read_text(encoding="utf-8")
            )

            if not isinstance(enforcement_payload, dict):
                fail("sub enforcement registry must be a mapping")

            for key, value in enforcement_payload.items():
                if key not in {"metadata", "registry"}:
                    payload[key] = value

        implementations = payload.get("implementations")

        if not isinstance(implementations, dict) or not implementations:
            fail("implementation registry must define implementations")

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

        falsification_tests = claim["falsification_tests"]
        if not isinstance(falsification_tests, list) or not falsification_tests:
            fail(f"{claim['id']} must define falsification tests")

        lineage = claim["lineage"]
        if not isinstance(lineage, dict):
            fail(f"{claim['id']} must define claim lineage")

        if not lineage.get("epoch"):
            fail(f"{claim['id']} lineage must declare epoch")

        validators = lineage.get("validated_by")
        if not isinstance(validators, list) or not validators:
            fail(f"{claim['id']} lineage must bind validators")

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


def validate_canonical_compression(payload: dict[str, Any]) -> None:
    compression = payload.get("canonical_compression")
    if not isinstance(compression, dict):
        fail("claim discipline must define canonical compression")

    missing = REQUIRED_COMPRESSION_KEYS - set(compression)
    if missing:
        fail(f"canonical compression missing fields: {sorted(missing)}")

    if compression["schema"] != "afritech.constitution.compression_basis.v1":
        fail("canonical compression schema mismatch")

    basis = compression["minimal_basis"]
    if not isinstance(basis, dict) or len(basis) < 4:
        fail("canonical compression must define minimal basis")

    reductions = compression["reductions"]
    if not isinstance(reductions, dict) or not reductions:
        fail("canonical compression must define reductions")

    for name, reduction in reductions.items():
        if not isinstance(reduction, dict):
            fail(f"compression reduction must be mapping: {name}")
        if not reduction.get("expression"):
            fail(f"compression reduction missing expression: {name}")
        replaced = reduction.get("replaces")
        if not isinstance(replaced, list) or not replaced:
            fail(f"compression reduction missing replaced concepts: {name}")


def validate_negative_capabilities(payload: dict[str, Any]) -> None:
    capabilities = payload.get("negative_capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        fail("claim discipline must define negative capabilities")

    for capability in capabilities:
        if not isinstance(capability, dict):
            fail("negative capability entries must be mappings")

        missing = REQUIRED_NEGATIVE_CAPABILITY_FIELDS - set(capability)
        if missing:
            fail(
                f"{capability.get('id', '<unknown>')} missing fields: "
                f"{sorted(missing)}"
            )

        if not capability["cannot_claim"] or not capability["reason"]:
            fail(f"{capability['id']} must define bounded non-capability")


def validate_claim_evidence_bindings(
    forbidden_terms: list[str],
) -> None:
    payload = load_bindings()
    registry = load_implementation_registry()

    if payload.get("schema") != "afritech.constitution.claim_evidence_bindings.v1":
        fail("claim evidence bindings schema mismatch")
    if payload.get("status") != "PROVEN_GOVERNANCE":
        fail("claim evidence bindings status mismatch")
    if payload.get("authority") != "afritech.demo.proof":
        fail("claim evidence bindings authority mismatch")
    if payload.get("classification") != "CLAIM_EVIDENCE_BINDING":
        fail("claim evidence bindings classification mismatch")
    if (
        payload.get("binding_rule")
        != "No IMPLEMENTED claim is admissible without executable evidence and validator binding."
    ):
        fail("claim evidence binding rule mismatch")

    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        fail("claim evidence bindings must define claims")

    claim_ids = tuple(claim.get("id") for claim in claims if isinstance(claim, dict))
    if claim_ids != EXPECTED_BINDING_CLAIMS:
        fail(f"claim evidence binding ids mismatch: {claim_ids}")

    implementations = registry.get("implementations")
    if not isinstance(implementations, dict) or not implementations:
        fail("implementation registry must define implementations")

    for claim in claims:
        if not isinstance(claim, dict):
            fail("claim evidence binding entries must be mappings")

        missing = REQUIRED_BINDING_FIELDS - set(claim)
        if missing:
            fail(f"{claim.get('id', '<unknown>')} missing binding fields: {sorted(missing)}")

        if claim["status"] != "IMPLEMENTED":
            fail(f"{claim['id']} binding must be IMPLEMENTED")

        if not claim["scope"]:
            fail(f"{claim['id']} binding has empty scope")

        evidence = claim["evidence"]
        if not isinstance(evidence, list) or not evidence:
            fail(f"{claim['id']} binding must define executable evidence")

        implementation_refs = claim["implementation_refs"]
        if not isinstance(implementation_refs, list) or not implementation_refs:
            fail(f"{claim['id']} binding must define implementation refs")

        for implementation_ref in implementation_refs:
            if implementation_ref not in implementations:
                fail(
                    f"{claim['id']} references missing implementation: "
                    f"{implementation_ref}"
                )
            implementation = implementations[implementation_ref]
            if not isinstance(implementation, dict):
                fail(f"{implementation_ref} registry entry must be a mapping")
            if implementation.get("implementation_state") != "IMPLEMENTED":
                fail(f"{implementation_ref} must be IMPLEMENTED for claim binding")
            semantic_properties = implementation.get("semantic_properties")
            if not isinstance(semantic_properties, dict):
                fail(f"{implementation_ref} must define semantic properties")
            if semantic_properties.get("replay_admissible") is not True:
                fail(f"{implementation_ref} must be replay admissible")
            if semantic_properties.get("proof_admissible") is not True:
                fail(f"{implementation_ref} must be proof admissible")
            if semantic_properties.get("deterministic_execution") is not True:
                fail(f"{implementation_ref} must be deterministic")

        validators = claim["validators"]
        if not isinstance(validators, list) or not validators:
            fail(f"{claim['id']} binding must define validators")

        non_claims = claim["non_claims"]
        if not isinstance(non_claims, list) or not non_claims:
            fail(f"{claim['id']} binding must define non-claims")

        validate_forbidden_terms(
            str(claim["statement"]),
            forbidden_terms,
            context=f"claim evidence binding {claim['id']}",
        )


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
    validate_canonical_compression(payload)
    validate_claims(payload, forbidden_terms)
    validate_new_surfaces(payload)
    validate_readiness_boundary(payload)
    validate_negative_capabilities(payload)
    validate_claim_evidence_bindings(forbidden_terms)


def main() -> int:
    try:
        validate()
        print("✅ Claim discipline validation PASSED")
        print("✅ Claims scoped, evidenced, validator-bound, and counter-tested")
        print("✅ New surfaces declare compression or complexity justification")
        print("✅ Canonical compression basis and falsification tests validated")
        print("✅ Negative capabilities explicitly bounded")
        print("✅ Claim-evidence bindings validated")
        print("✅ Global readiness claims remain forbidden")
        return 0
    except Exception as exc:
        print(f"❌ Claim discipline validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
