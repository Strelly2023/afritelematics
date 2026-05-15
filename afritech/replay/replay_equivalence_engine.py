"""
afritech.replay.replay_equivalence_engine
=========================================

Replay equivalence verification engine.

Validates:

- execution ↔ replay semantic equivalence
- reference-based witness bundle integrity
- transcript integrity
- mutation trace ordering
- deterministic reconstruction
- replay trace hash determinism (NEW)

Fail-fast, deterministic, proof-oriented.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List


# ============================================================
# PATHS
# ============================================================

WITNESS_ROOT = Path("afritech/proof")
OUTPUT_ROOT = Path("afritech/replay/output")


# ============================================================
# EXCEPTIONS
# ============================================================

class ReplayEquivalenceError(Exception):
    pass


# ============================================================
# UTILITIES
# ============================================================

def load_json(path: Path) -> Any:
    if not path.exists():
        raise ReplayEquivalenceError(f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ReplayEquivalenceError(f"invalid JSON: {path}") from exc


def normalize_witness(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic comparison normalization.
    Removes identity fields.
    """
    excluded = {"canonical_identity", "witness_hash"}
    return {k: v for k, v in data.items() if k not in excluded}


def normalize_for_hash(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integrity hashing normalization.
    Removes self-referential hash only.
    """
    return {k: v for k, v in data.items() if k != "witness_hash"}


def stable_hash(data: Any) -> str:
    try:
        encoded = json.dumps(data, sort_keys=True).encode("utf-8")
    except TypeError as exc:
        raise ReplayEquivalenceError("non-serializable data") from exc

    return hashlib.sha256(encoded).hexdigest()


# ============================================================
# BUNDLE RESOLUTION
# ============================================================

def extract_witness_map(bundle: Dict[str, Any]) -> Dict[str, str]:
    refs = bundle.get("references", [])

    if not isinstance(refs, list):
        raise ReplayEquivalenceError("invalid references structure")

    result: Dict[str, str] = {}

    for ref in refs:
        wtype = ref.get("witness_type")
        whash = ref.get("witness_hash")

        if not wtype or not whash:
            raise ReplayEquivalenceError("invalid witness reference")

        result[wtype] = whash

    return result


# ============================================================
# CORE CHECKS
# ============================================================

def check_execution_vs_replay(exec_data: Any, replay_data: Any) -> None:
    """
    ✅ Semantic equivalence (normalized)
    """
    exec_norm = normalize_witness(exec_data)
    replay_norm = normalize_witness(replay_data)

    if stable_hash(exec_norm) != stable_hash(replay_norm):

        print("\n--- EXECUTION (normalized) ---")
        print(json.dumps(exec_norm, indent=2))

        print("\n--- REPLAY (normalized) ---")
        print(json.dumps(replay_norm, indent=2))

        raise ReplayEquivalenceError(
            "execution != replay (semantic mismatch)"
        )


def check_hash_chain(
    bundle: Dict[str, Any],
    exec_data: Any,
    replay_data: Any,
    trace_data: Any,
    transcript_data: Any,
) -> None:
    """
    ✅ Witness integrity (no circular hashing)
    """

    witness_map = extract_witness_map(bundle)

    exec_hash = stable_hash(normalize_for_hash(exec_data))
    replay_hash = stable_hash(normalize_for_hash(replay_data))
    mutation_hash = stable_hash(trace_data)
    transcript_hash = stable_hash(transcript_data)

    if witness_map.get("EXECUTION") != exec_hash:
        raise ReplayEquivalenceError("execution hash mismatch")

    if witness_map.get("REPLAY") != replay_hash:
        raise ReplayEquivalenceError("replay hash mismatch")

    if witness_map.get("MUTATION") != mutation_hash:
        raise ReplayEquivalenceError("mutation hash mismatch")

    if witness_map.get("TRANSCRIPT") != transcript_hash:
        raise ReplayEquivalenceError("transcript hash mismatch")


def check_mutation_trace(trace: List[Dict[str, Any]]) -> None:

    if not isinstance(trace, list) or not trace:
        raise ReplayEquivalenceError("invalid mutation trace")

    last_order = -1

    for idx, step in enumerate(trace):

        if not isinstance(step, dict):
            raise ReplayEquivalenceError(f"invalid mutation step at {idx}")

        order = step.get("order")

        if not isinstance(order, int) or order <= last_order:
            raise ReplayEquivalenceError("non-deterministic mutation ordering")

        last_order = order


def check_transcript(transcript: List[Dict[str, Any]]) -> None:

    if not isinstance(transcript, list):
        raise ReplayEquivalenceError("invalid transcript")

    for idx, entry in enumerate(transcript):

        if not isinstance(entry, dict):
            raise ReplayEquivalenceError(f"invalid transcript entry {idx}")

        if "event" not in entry:
            raise ReplayEquivalenceError("missing event field")


def check_replay_determinism(bundle: Dict[str, Any]) -> None:
    """
    ✅ NEW: Replay trace-level determinism
    """

    replay_hash = bundle.get("replay_hash")
    execution_trace_hash = bundle.get("execution_trace_hash")

    if not replay_hash or not execution_trace_hash:
        raise ReplayEquivalenceError(
            "missing replay_hash or execution_trace_hash"
        )

    if replay_hash != execution_trace_hash:
        raise ReplayEquivalenceError(
            "replay_hash != execution_trace_hash (non-deterministic execution)"
        )


# ============================================================
# ENGINE
# ============================================================

def run_equivalence() -> None:

    print("🔁 Running replay equivalence engine...")

    execution = load_json(WITNESS_ROOT / "execution_witness.json")
    replay = load_json(WITNESS_ROOT / "replay_witness.json")
    trace = load_json(WITNESS_ROOT / "mutation_witness.json")
    transcript = load_json(WITNESS_ROOT / "transcript_witness.json")
    bundle = load_json(WITNESS_ROOT / "witness_bundle.json")

    # ✅ VALIDATION PIPELINE

    check_execution_vs_replay(execution, replay)
    check_hash_chain(bundle, execution, replay, trace, transcript)
    check_mutation_trace(trace)
    check_transcript(transcript)
    check_replay_determinism(bundle)  # ✅ NEW

    # ✅ PROOF OUTPUT

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    proof = {
        "status": "EQUIVALENT",
        "execution_hash": stable_hash(normalize_for_hash(execution)),
        "replay_hash": stable_hash(normalize_for_hash(replay)),
        "mutation_hash": stable_hash(trace),
        "transcript_hash": stable_hash(transcript),
        "trace_replay_hash": bundle.get("replay_hash"),
        "result": "execution == replay",
    }

    (OUTPUT_ROOT / "equivalence_proof.json").write_text(
        json.dumps(proof, indent=2)
    )

    print("✅ Replay equivalence verified")
    print("✅ Execution matches replay")
    print("✅ Mutation trace ordering valid")
    print("✅ Transcript integrity validated")
    print("✅ Replay determinism verified")
    print("✅ Proof generated")


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    try:
        run_equivalence()
        return 0
    except Exception as exc:
        print(f"❌ Replay equivalence failed: {exc}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())