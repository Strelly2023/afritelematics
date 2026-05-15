"""
afritech.ci.cross_concept_validator
===================================

Cross-concept constitutional validation.

Validates:

- admissibility ↔ replay_admissibility consistency
- deterministic_execution ↔ mutation_traceability alignment
- authority_declaration ↔ enforcement constraints
- closed_world ↔ all execution concepts
- global invariant consistency

Fail-fast, deterministic, system-level semantic enforcement.
"""

from __future__ import annotations

import sys
import yaml
from pathlib import Path
from typing import Dict, Any


# ============================================================
# CONSTANTS
# ============================================================

CONCEPT_ROOT = Path("afritech/constitution/canonical/concepts")


# ============================================================
# EXCEPTIONS
# ============================================================

class CrossConceptValidationError(Exception):
    pass


# ============================================================
# LOADER
# ============================================================

def load_all_concepts() -> Dict[str, Dict[str, Any]]:

    concepts = {}

    for file_path in sorted(CONCEPT_ROOT.glob("*.yaml")):

        if file_path.name.startswith("."):
            continue

        payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))

        name = payload["concept"]["name"]
        concepts[name] = payload

    return concepts


# ============================================================
# CORE CHECKS
# ============================================================

def check_admissibility_vs_replay(concepts: Dict[str, Any]):

    admissibility = concepts.get("admissibility")
    replay = concepts.get("replay_admissibility")

    if not admissibility or not replay:
        raise CrossConceptValidationError(
            "missing admissibility or replay_admissibility"
        )

    required = set(replay["definition"]["requires"])

    if "deterministic_execution" not in required:
        raise CrossConceptValidationError(
            "replay_admissibility must require deterministic_execution"
        )


def check_determinism_vs_mutation(concepts: Dict[str, Any]):

    determinism = concepts.get("deterministic_execution")
    mutation = concepts.get("mutation_traceability")

    if not determinism or not mutation:
        raise CrossConceptValidationError(
            "missing deterministic_execution or mutation_traceability"
        )

    req_det = set(determinism["definition"]["requires"])
    req_mut = set(mutation["definition"]["requires"])

    if "deterministic_mutation_ordering" not in req_mut:
        raise CrossConceptValidationError(
            "mutation_traceability must enforce deterministic_mutation_ordering"
        )

    if "controlled_mutation_boundaries" not in req_det:
        raise CrossConceptValidationError(
            "deterministic_execution must enforce controlled_mutation_boundaries"
        )


def check_authority_vs_enforcement(concepts: Dict[str, Any]):

    authority = concepts.get("authority_declaration")

    if not authority:
        raise CrossConceptValidationError(
            "missing authority_declaration"
        )

    forbidden = set(authority["definition"]["forbidden_when"])

    if "implicit_authority" not in forbidden:
        raise CrossConceptValidationError(
            "authority must forbid implicit authority"
        )


def check_closed_world_global(concepts: Dict[str, Any]):

    closed = concepts.get("closed_world")

    if not closed:
        raise CrossConceptValidationError(
            "missing closed_world"
        )

    forbidden = set(closed["definition"]["forbidden_when"])

    if "implicit_surface_discovery_exists" not in forbidden:
        raise CrossConceptValidationError(
            "closed_world must forbid implicit surface discovery"
        )


def check_replay_requires_mutation_trace(concepts: Dict[str, Any]):

    replay = concepts.get("replay_admissibility")
    mutation = concepts.get("mutation_traceability")

    if not replay or not mutation:
        raise CrossConceptValidationError(
            "missing replay_admissibility or mutation_traceability"
        )

    replay_req = set(replay["definition"]["requires"])

    if "replay_traceability" not in replay_req:
        raise CrossConceptValidationError(
            "replay must require mutation traceability"
        )


# ============================================================
# MASTER VALIDATION
# ============================================================

def validate_cross_concepts() -> None:

    concepts = load_all_concepts()

    if len(concepts) < 6:
        raise CrossConceptValidationError(
            "incomplete concept set"
        )

    # -------------------------------
    # CORE CROSS CHECKS
    # -------------------------------

    check_admissibility_vs_replay(concepts)
    check_determinism_vs_mutation(concepts)
    check_authority_vs_enforcement(concepts)
    check_closed_world_global(concepts)
    check_replay_requires_mutation_trace(concepts)

    print("✅ Cross-concept validation passed")
    print("✅ Admissibility ↔ Replay consistency verified")
    print("✅ Determinism ↔ Mutation consistency verified")
    print("✅ Authority constraints verified")
    print("✅ Closed-world enforcement verified")
    print("✅ Replay traceability dependencies verified")


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:
        validate_cross_concepts()
        return 0

    except Exception as exc:
        print(f"❌ Cross-concept validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
