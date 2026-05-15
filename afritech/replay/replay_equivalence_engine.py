"""
afritech.replay.replay_equivalence_engine
=========================================

Canonical replay equivalence verification engine.

Constitutional guarantees:
- execution ↔ replay semantic equivalence
- deterministic replay reconstruction
- witness bundle integrity
- transcript integrity
- mutation trace determinism
- replay trace hash equivalence
- observer-independent replay validation
- closed-world replay admissibility

This engine is:
- fail-fast
- deterministic
- replay-safe
- proof-oriented
- constitutionally admissible

Forbidden:
- probabilistic reconstruction
- partial replay comparison
- observer-relative replay semantics
- undeclared witness participation
"""

from __future__ import annotations

import hashlib
import json

from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# CONSTANTS
# ============================================================

WITNESS_ROOT = Path("afritech/proof")
OUTPUT_ROOT = Path("afritech/replay/output")


# ============================================================
# EXCEPTIONS
# ============================================================

class ReplayEquivalenceError(Exception):
    """
    Raised when replay equivalence validation fails.
    """
    pass


# ============================================================
# FILE LOADING
# ============================================================

def load_json(path: Path) -> Any:
    """
    Deterministic JSON loader.
    """

    if not path.exists():
        raise ReplayEquivalenceError(
            f"missing file: {path}"
        )

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )

    except Exception as exc:
        raise ReplayEquivalenceError(
            f"invalid JSON: {path}"
        ) from exc


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_witness(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Semantic comparison normalization.

    Removes:
    - canonical identity
    - self-referential witness hashes

    Purpose:
    - semantic equivalence
    - observer-independent replay comparison
    """

    excluded = {
        "canonical_identity",
        "witness_hash",
    }

    return {
        key: value
        for key, value in data.items()
        if key not in excluded
    }


def normalize_for_hash(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hash normalization.

    Removes:
    - self-referential witness_hash

    Required for:
    - stable deterministic hashing
    - replay equivalence verification
    """

    return {
        key: value
        for key, value in data.items()
        if key != "witness_hash"
    }


# ============================================================
# HASHING
# ============================================================

def stable_hash(data: Any) -> str:
    """
    Deterministic SHA256 hashing.

    Guarantees:
    - stable ordering
    - replay-safe hashing
    - observer-independent equivalence
    """

    try:

        encoded = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    except TypeError as exc:
        raise ReplayEquivalenceError(
            "non-serializable data"
        ) from exc

    return hashlib.sha256(encoded).hexdigest()


# ============================================================
# BUNDLE RESOLUTION
# ============================================================

def extract_witness_map(
    bundle: Dict[str, Any],
) -> Dict[str, str]:
    """
    Resolve witness references from bundle.
    """

    references = bundle.get("references", [])

    if not isinstance(references, list):
        raise ReplayEquivalenceError(
            "invalid references structure"
        )

    witness_map: Dict[str, str] = {}

    for reference in references:

        if not isinstance(reference, dict):
            raise ReplayEquivalenceError(
                "invalid witness reference entry"
            )

        witness_type = reference.get("witness_type")
        witness_hash = reference.get("witness_hash")

        if not witness_type:
            raise ReplayEquivalenceError(
                "missing witness_type"
            )

        if not witness_hash:
            raise ReplayEquivalenceError(
                "missing witness_hash"
            )

        witness_map[witness_type] = witness_hash

    return witness_map


# ============================================================
# SEMANTIC EQUIVALENCE
# ============================================================

def check_execution_vs_replay(
    execution_data: Dict[str, Any],
    replay_data: Dict[str, Any],
) -> None:
    """
    Validate semantic replay equivalence.
    """

    execution_normalized = normalize_witness(
        execution_data
    )

    replay_normalized = normalize_witness(
        replay_data
    )

    execution_hash = stable_hash(
        execution_normalized
    )

    replay_hash = stable_hash(
        replay_normalized
    )

    if execution_hash != replay_hash:

        print("\n--- EXECUTION ---")
        print(
            json.dumps(
                execution_normalized,
                indent=2,
                sort_keys=True,
            )
        )

        print("\n--- REPLAY ---")
        print(
            json.dumps(
                replay_normalized,
                indent=2,
                sort_keys=True,
            )
        )

        raise ReplayEquivalenceError(
            "execution != replay "
            "(semantic mismatch)"
        )


# ============================================================
# WITNESS HASH VALIDATION
# ============================================================

def check_hash_chain(
    bundle: Dict[str, Any],
    execution_data: Dict[str, Any],
    replay_data: Dict[str, Any],
    mutation_trace: Any,
    transcript: Any,
) -> None:
    """
    Validate witness hash integrity.
    """

    witness_map = extract_witness_map(bundle)

    execution_hash = stable_hash(
        normalize_for_hash(execution_data)
    )

    replay_hash = stable_hash(
        normalize_for_hash(replay_data)
    )

    mutation_hash = stable_hash(
        mutation_trace
    )

    transcript_hash = stable_hash(
        transcript
    )

    if witness_map.get("EXECUTION") != execution_hash:
        raise ReplayEquivalenceError(
            "execution hash mismatch"
        )

    if witness_map.get("REPLAY") != replay_hash:
        raise ReplayEquivalenceError(
            "replay hash mismatch"
        )

    if witness_map.get("MUTATION") != mutation_hash:
        raise ReplayEquivalenceError(
            "mutation hash mismatch"
        )

    if witness_map.get("TRANSCRIPT") != transcript_hash:
        raise ReplayEquivalenceError(
            "transcript hash mismatch"
        )


# ============================================================
# MUTATION TRACE VALIDATION
# ============================================================

def check_mutation_trace(
    trace: List[Dict[str, Any]],
) -> None:
    """
    Validate deterministic mutation ordering.
    """

    if not isinstance(trace, list):
        raise ReplayEquivalenceError(
            "invalid mutation trace"
        )

    if not trace:
        raise ReplayEquivalenceError(
            "empty mutation trace"
        )

    previous_order = -1

    for index, step in enumerate(trace):

        if not isinstance(step, dict):
            raise ReplayEquivalenceError(
                f"invalid mutation step at {index}"
            )

        order = step.get("order")

        if not isinstance(order, int):
            raise ReplayEquivalenceError(
                f"invalid mutation order at {index}"
            )

        if order <= previous_order:
            raise ReplayEquivalenceError(
                "non-deterministic mutation ordering"
            )

        previous_order = order


# ============================================================
# TRANSCRIPT VALIDATION
# ============================================================

def check_transcript(
    transcript: List[Dict[str, Any]],
) -> None:
    """
    Validate transcript structure.
    """

    if not isinstance(transcript, list):
        raise ReplayEquivalenceError(
            "invalid transcript"
        )

    for index, entry in enumerate(transcript):

        if not isinstance(entry, dict):
            raise ReplayEquivalenceError(
                f"invalid transcript entry {index}"
            )

        if "event" not in entry:
            raise ReplayEquivalenceError(
                "missing event field"
            )


# ============================================================
# REPLAY DETERMINISM
# ============================================================

def check_replay_determinism(
    bundle: Dict[str, Any],
) -> None:
    """
    Validate replay trace determinism.
    """

    replay_hash = bundle.get("replay_hash")

    execution_trace_hash = bundle.get(
        "execution_trace_hash"
    )

    if not replay_hash:
        raise ReplayEquivalenceError(
            "missing replay_hash"
        )

    if not execution_trace_hash:
        raise ReplayEquivalenceError(
            "missing execution_trace_hash"
        )

    if replay_hash != execution_trace_hash:
        raise ReplayEquivalenceError(
            "replay_hash != execution_trace_hash"
        )


# ============================================================
# PROOF GENERATION
# ============================================================

def generate_equivalence_proof(
    execution: Dict[str, Any],
    replay: Dict[str, Any],
    mutation_trace: Any,
    transcript: Any,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate deterministic equivalence proof.
    """

    return {
        "status": "EQUIVALENT",

        "execution_hash":
            stable_hash(
                normalize_for_hash(execution)
            ),

        "replay_hash":
            stable_hash(
                normalize_for_hash(replay)
            ),

        "mutation_hash":
            stable_hash(mutation_trace),

        "transcript_hash":
            stable_hash(transcript),

        "trace_replay_hash":
            bundle.get("replay_hash"),

        "equivalence":
            "execution == replay",

        "deterministic":
            True,

        "observer_independent":
            True,

        "replay_safe":
            True,
    }


# ============================================================
# ENGINE
# ============================================================

def run_equivalence() -> None:
    """
    Execute replay equivalence pipeline.
    """

    print(
        "🔁 Running replay equivalence engine..."
    )

    execution = load_json(
        WITNESS_ROOT / "execution_witness.json"
    )

    replay = load_json(
        WITNESS_ROOT / "replay_witness.json"
    )

    mutation_trace = load_json(
        WITNESS_ROOT / "mutation_witness.json"
    )

    transcript = load_json(
        WITNESS_ROOT / "transcript_witness.json"
    )

    bundle = load_json(
        WITNESS_ROOT / "witness_bundle.json"
    )

    # ========================================================
    # VALIDATION PIPELINE
    # ========================================================

    check_execution_vs_replay(
        execution,
        replay,
    )

    check_hash_chain(
        bundle,
        execution,
        replay,
        mutation_trace,
        transcript,
    )

    check_mutation_trace(
        mutation_trace
    )

    check_transcript(
        transcript
    )

    check_replay_determinism(
        bundle
    )

    # ========================================================
    # PROOF OUTPUT
    # ========================================================

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    proof = generate_equivalence_proof(
        execution,
        replay,
        mutation_trace,
        transcript,
        bundle,
    )

    output_path = (
        OUTPUT_ROOT
        / "equivalence_proof.json"
    )

    output_path.write_text(
        json.dumps(
            proof,
            indent=2,
            sort_keys=True,
        )
    )

    print("✅ Replay equivalence verified")
    print("✅ Execution matches replay")
    print("✅ Witness integrity validated")
    print("✅ Mutation trace ordering valid")
    print("✅ Transcript integrity validated")
    print("✅ Replay determinism verified")
    print("✅ Equivalence proof generated")


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    Entrypoint.
    """

    try:

        run_equivalence()

        return 0

    except Exception as exc:

        print(
            f"❌ Replay equivalence failed: {exc}"
        )

        return 1


if __name__ == "__main__":

    import sys

    sys.exit(main())