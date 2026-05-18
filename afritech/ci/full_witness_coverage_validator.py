"""Validate complete witness coverage for proof-critical surfaces."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import (
    REQUIRED_WITNESSES,
    ROOT,
    fail,
    load_yaml,
    main_result,
)


WITNESS_REGISTRY = ROOT / "afritech/proof/witness/WITNESS_REGISTRY.yaml"
LEVEL2_MODEL = ROOT / "afritech/constitution/level2_formal_model.yaml"


def validate() -> None:
    registry = load_yaml(WITNESS_REGISTRY)
    witnesses = registry.get("witnesses")
    if not isinstance(witnesses, dict):
        fail("WITNESS_REGISTRY.yaml must declare witnesses")

    missing = sorted(REQUIRED_WITNESSES - set(witnesses))
    if missing:
        fail(f"missing required completion witnesses: {missing}")

    for witness_id, entry in witnesses.items():
        if not isinstance(entry, dict):
            fail(f"witness {witness_id} must be a mapping")
        for key in ("surface", "epoch", "invariant_refs", "hash_inputs", "verifier"):
            if not entry.get(key):
                fail(f"witness {witness_id} missing {key}")

    model = load_yaml(LEVEL2_MODEL)
    theorem_witnesses = set()
    for theorem in model.get("theorems", []):
        theorem_witnesses.update(theorem.get("requires_witnesses", []))

    missing_from_level2 = sorted(REQUIRED_WITNESSES - theorem_witnesses)
    if missing_from_level2:
        fail(f"Level 2 does not require witnesses: {missing_from_level2}")

    print(f"✅ Witnesses validated: {len(witnesses)}")


def main() -> int:
    return main_result("Full witness coverage validation", validate)


if __name__ == "__main__":
    sys.exit(main())
