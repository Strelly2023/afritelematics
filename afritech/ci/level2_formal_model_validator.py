"""
AfriTech Level 2 Formal Model Validator.

This validator binds the Level 2 consistency model to real
constitutional artifacts: semantic atoms, core axioms, invariant IR,
and declared receipt witnesses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = ROOT / "afritech/constitution/level2_formal_model.yaml"
SEMANTIC_ATOMS_CORE = ROOT / "afritech/constitution/semantic_atoms_core.yaml"
CORE_AXIOMS_DIR = ROOT / "afritech/constitution/core"
INVARIANTS_IR = ROOT / "afritech/constitution/compiled/invariants_ir.json"
WITNESS_REGISTRY = ROOT / "afritech/proof/witness/WITNESS_REGISTRY.yaml"

EXPECTED_SCHEMA = "afritech.constitution.level2.formal_model.v1"
EXPECTED_TUPLE = ["Sigma", "A", "I", "T", "E", "R"]
EXPECTED_THEOREMS = {
    f"L2-THM-{index:03d}"
    for index in range(1, 13)
}
FINAL_PROPERTY_ID = "L2-COMPLETE-SYSTEM-PROPERTY"


class Level2FormalModelError(Exception):
    """Raised when Level 2 formal model validation fails."""


def fail(message: str) -> None:
    raise Level2FormalModelError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing YAML artifact: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"YAML artifact must be a mapping: {path}")
    return payload


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing JSON artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"JSON artifact must be a mapping: {path}")
    return payload


def load_semantic_atoms() -> set[str]:
    payload = load_yaml(SEMANTIC_ATOMS_CORE)
    atoms = payload.get("semantic_atoms")
    if not isinstance(atoms, dict) or not atoms:
        fail("semantic_atoms_core.yaml must declare semantic_atoms")
    return set(atoms)


def load_core_axioms() -> set[str]:
    axiom_ids: set[str] = set()

    for path in sorted(CORE_AXIOMS_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        payload = load_yaml(path)
        axioms = payload.get("axioms")
        if not isinstance(axioms, list) or not axioms:
            fail(f"core axiom file lacks axioms: {path}")
        for axiom in axioms:
            if not isinstance(axiom, dict):
                fail(f"invalid axiom entry in {path}")
            axiom_id = axiom.get("id")
            if not isinstance(axiom_id, str) or not axiom_id:
                fail(f"axiom entry missing id in {path}")
            axiom_ids.add(axiom_id)

    if not axiom_ids:
        fail("no core axioms discovered")

    return axiom_ids


def load_invariant_ids() -> set[str]:
    payload = load_json(INVARIANTS_IR)
    invariant_ids: set[str] = set()

    canonical = payload.get("canonical_invariants", [])
    if isinstance(canonical, list):
        invariant_ids.update(
            item for item in canonical
            if isinstance(item, str)
        )

    runtime_projection = payload.get("runtime_projection", [])
    if isinstance(runtime_projection, list):
        invariant_ids.update(
            item for item in runtime_projection
            if isinstance(item, str)
        )

    for key in ("invariants", "semantic_invariants"):
        section = payload.get(key, {})
        if isinstance(section, dict):
            invariant_ids.update(section)

    if not invariant_ids:
        fail("compiled invariant IR contains no invariant ids")

    return invariant_ids


def load_witness_ids() -> set[str]:
    payload = load_yaml(WITNESS_REGISTRY)
    witnesses = payload.get("witnesses")
    if not isinstance(witnesses, dict) or not witnesses:
        fail("WITNESS_REGISTRY.yaml must declare witnesses")
    return set(witnesses)


def require_list(
    mapping: dict[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = mapping.get(key)
    if not isinstance(value, list):
        fail(f"{context} must define list field: {key}")
    return value


def require_subset(
    values: list[Any],
    allowed: set[str],
    label: str,
    context: str,
) -> None:
    invalid = sorted(
        value for value in values
        if not isinstance(value, str) or value not in allowed
    )
    if invalid:
        fail(f"{context} references unknown {label}: {invalid}")


def validate_system_tuple(model: dict[str, Any]) -> None:
    system = model.get("system")
    if not isinstance(system, dict):
        fail("formal model must define system")

    tuple_value = require_list(system, "tuple", "system")
    if tuple_value != EXPECTED_TUPLE:
        fail(
            "system tuple must be "
            f"{EXPECTED_TUPLE}, got {tuple_value}"
        )

    state_space = system.get("state_space")
    if not isinstance(state_space, dict):
        fail("system must define state_space")

    fields = require_list(state_space, "fields", "state_space")
    required_fields = {"epoch", "registry", "surfaces", "invariants", "history"}
    if set(fields) != required_fields:
        fail(
            "state_space fields must be "
            f"{sorted(required_fields)}, got {fields}"
        )

    transition = system.get("transition_system")
    if not isinstance(transition, dict):
        fail("system must define transition_system")

    for flag in ("deterministic", "invariant_preserving", "guard_filtered"):
        if transition.get(flag) is not True:
            fail(f"transition_system.{flag} must be true")

    execution = system.get("execution_rules")
    if not isinstance(execution, dict):
        fail("system must define execution_rules")

    for flag in ("closed_world", "deterministic", "declared_surface_required"):
        if execution.get(flag) is not True:
            fail(f"execution_rules.{flag} must be true")


def validate_model(model: dict[str, Any]) -> None:
    if model.get("schema") != EXPECTED_SCHEMA:
        fail(f"invalid schema: {model.get('schema')}")

    validate_system_tuple(model)

    atom_ids = load_semantic_atoms()
    axiom_ids = load_core_axioms()
    invariant_ids = load_invariant_ids()
    witness_ids = load_witness_ids()

    system = model["system"]
    model_atoms = require_list(system, "semantic_atoms", "system")
    require_subset(model_atoms, atom_ids, "semantic atoms", "system")
    if set(model_atoms) != atom_ids:
        fail(
            "Level 2 semantic atoms must exactly match core atoms: "
            f"{sorted(model_atoms)} != {sorted(atom_ids)}"
        )

    runtime_projection = require_list(
        system,
        "runtime_projection",
        "system",
    )
    require_subset(
        runtime_projection,
        invariant_ids,
        "invariants",
        "system.runtime_projection",
    )

    replay_operator = system.get("replay_operator")
    if not isinstance(replay_operator, dict):
        fail("system must define replay_operator")
    replay_requirements = require_list(
        replay_operator,
        "requires",
        "system.replay_operator",
    )
    require_subset(
        replay_requirements,
        witness_ids,
        "witnesses",
        "system.replay_operator",
    )

    theorems = model.get("theorems")
    if not isinstance(theorems, list):
        fail("formal model must define theorem list")

    theorem_ids: set[str] = set()
    for theorem in theorems:
        if not isinstance(theorem, dict):
            fail("theorem entries must be mappings")
        theorem_id = theorem.get("id")
        if not isinstance(theorem_id, str) or not theorem_id:
            fail("theorem missing id")
        if theorem_id in theorem_ids:
            fail(f"duplicate theorem id: {theorem_id}")
        theorem_ids.add(theorem_id)

        context = f"theorem {theorem_id}"
        statement = theorem.get("statement")
        verifier = theorem.get("verifier")
        if not isinstance(statement, str) or not statement.strip():
            fail(f"{context} must define statement")
        if not isinstance(verifier, str) or not verifier.strip():
            fail(f"{context} must define verifier")

        requires_atoms = require_list(theorem, "requires_atoms", context)
        requires_axioms = require_list(theorem, "requires_axioms", context)
        requires_invariants = require_list(
            theorem,
            "requires_invariants",
            context,
        )
        requires_witnesses = require_list(
            theorem,
            "requires_witnesses",
            context,
        )

        require_subset(requires_atoms, atom_ids, "semantic atoms", context)
        require_subset(requires_axioms, axiom_ids, "axioms", context)
        require_subset(
            requires_invariants,
            invariant_ids,
            "invariants",
            context,
        )
        require_subset(
            requires_witnesses,
            witness_ids,
            "witnesses",
            context,
        )

    if theorem_ids != EXPECTED_THEOREMS:
        fail(
            "Level 2 theorem set mismatch: "
            f"missing={sorted(EXPECTED_THEOREMS - theorem_ids)} "
            f"extra={sorted(theorem_ids - EXPECTED_THEOREMS)}"
        )

    final_property = model.get("final_property")
    if not isinstance(final_property, dict):
        fail("formal model must define final_property")
    if final_property.get("id") != FINAL_PROPERTY_ID:
        fail("final_property id mismatch")

    depends_on = require_list(
        final_property,
        "depends_on",
        "final_property",
    )
    require_subset(depends_on, theorem_ids, "theorems", "final_property")
    if set(depends_on) != theorem_ids:
        fail("final_property must depend on all Level 2 theorems")


def run() -> None:
    model = load_yaml(MODEL_PATH)
    validate_model(model)

    print("✅ Level 2 formal consistency model validated")
    print(f"✅ Theorems resolved: {len(EXPECTED_THEOREMS)}")
    print("✅ Semantic atoms, axioms, invariants, and witnesses aligned")
    print("✅ Final complete-system property bound to all Level 2 theorems")


def main() -> int:
    try:
        run()
        return 0
    except Level2FormalModelError as exc:
        print(f"❌ Level 2 formal model validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
