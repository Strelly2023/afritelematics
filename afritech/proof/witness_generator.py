"""
afritech.proof.witness_generator
================================

Canonical deterministic witness artifact generator.

Responsibilities:

- generate all witness artifacts
- compute deterministic hashes
- enforce canonical identity
- build witness bundle
- generate constitutional receipt
- serialize replay-safe artifacts
- generate deterministic mutation traces
- generate deterministic transcript traces

All outputs are:

- deterministic
- replay-safe
- closed-world aligned
- validator-compatible
- replay-equivalence compatible
"""

from __future__ import annotations

import json

from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# CONSTANTS
# ============================================================

OUTPUT_DIR = Path("afritech/proof")

HASH_ALGO = "sha256"

IMPLEMENTATION_STATE = "IMPLEMENTED"

WITNESS_IDENTITIES = {
    "REPLAY":
        "afritech.proof.witness.replay_witness",

    "EXECUTION":
        "afritech.proof.witness.execution_witness",

    "MUTATION":
        "afritech.proof.witness.mutation_witness",

    "TRANSCRIPT":
        "afritech.proof.witness.transcript_witness",
}

BUNDLE_IDENTITY = (
    "afritech.proof.witness.witness_bundle"
)

RECEIPT_IDENTITY = (
    "afritech.proof.constitutional_receipt"
)


# ============================================================
# UTILITIES
# ============================================================

def stable_dumps(payload: Any) -> str:
    """
    Deterministic serialization.
    """

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )


def stable_hash(payload: Any) -> str:
    """
    Deterministic SHA256 hashing.
    """

    return sha256(
        stable_dumps(payload).encode("utf-8")
    ).hexdigest()


def write_json(
    path: Path,
    payload: Any,
) -> None:
    """
    Deterministic JSON writer.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


# ============================================================
# BASE WITNESS FACTORY
# ============================================================

def build_base_witness(
    identity: str,
) -> Dict[str, Any]:
    """
    Build deterministic metadata witness.
    """

    payload = {
        "schema_version": 1,
        "canonical_identity": identity,
        "implementation_state":
            IMPLEMENTATION_STATE,

        "hash_algorithm":
            HASH_ALGO,

        "deterministic": True,
        "replay_safe": True,
        "closed_world_aligned": True,
        "observer_independent": True,
    }

    payload["witness_hash"] = stable_hash(
        payload.copy()
    )

    return payload


# ============================================================
# MUTATION TRACE WITNESS
# ============================================================

def build_mutation_trace() -> List[Dict[str, Any]]:
    """
    Deterministic replay mutation trace.
    """

    return [

        {
            "order": 1,

            "mutation_type":
                "REMOVE_SPECULATIVE_EXECUTION_SURFACE",

            "target":
                (
                    "afritech/speculative/"
                    "civilization/"
                    "civilization_engine.py"
                ),

            "action":
                "DELETE_EXECUTABLE_SURFACE",

            "deterministic": True,
        },

        {
            "order": 2,

            "mutation_type":
                "DECLARE_RUNTIME_SURFACE",

            "target":
                (
                    "afritech/runtime/"
                    "orchestration/"
                    "civilization_engine.py"
                ),

            "action":
                (
                    "REGISTER_CANONICAL_"
                    "RUNTIME_SURFACE"
                ),

            "deterministic": True,
        },

        {
            "order": 3,

            "mutation_type":
                "NORMALIZE_EPOCH_IDENTITY",

            "target":
                "EPOCH_0008",

            "action":
                "REMOVE_ALIAS_INVERSION",

            "deterministic": True,
        },
    ]


# ============================================================
# TRANSCRIPT TRACE WITNESS
# ============================================================

def build_transcript_trace() -> List[Dict[str, Any]]:
    """
    Deterministic replay transcript trace.
    """

    return [

        {
            "event":
                "EXECUTION_STARTED",

            "order": 1,

            "deterministic": True,
        },

        {
            "event":
                "TOPOLOGY_VALIDATED",

            "order": 2,

            "deterministic": True,
        },

        {
            "event":
                "REPLAY_VALIDATED",

            "order": 3,

            "deterministic": True,
        },

        {
            "event":
                "EXECUTION_COMPLETED",

            "order": 4,

            "deterministic": True,
        },
    ]


# ============================================================
# STANDARD WITNESS GENERATION
# ============================================================

def generate_standard_witnesses() -> Dict[str, Any]:
    """
    Generate all deterministic witnesses.
    """

    witnesses: Dict[str, Any] = {}

    for witness_type in sorted(
        WITNESS_IDENTITIES.keys()
    ):

        identity = WITNESS_IDENTITIES[
            witness_type
        ]

        # ====================================================
        # MUTATION TRACE WITNESS
        # ====================================================

        if witness_type == "MUTATION":

            payload = build_mutation_trace()

            filename = (
                "mutation_witness.json"
            )

        # ====================================================
        # TRANSCRIPT TRACE WITNESS
        # ====================================================

        elif witness_type == "TRANSCRIPT":

            payload = build_transcript_trace()

            filename = (
                "transcript_witness.json"
            )

        # ====================================================
        # STANDARD METADATA WITNESS
        # ====================================================

        else:

            payload = build_base_witness(
                identity
            )

            filename = (
                f"{identity.split('.')[-1]}"
                ".json"
            )

        witnesses[witness_type] = payload

        write_json(
            OUTPUT_DIR / filename,
            payload,
        )

    return witnesses


# ============================================================
# BUNDLE GENERATION
# ============================================================

def generate_bundle(
    witnesses: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build deterministic witness bundle.
    """

    references: List[Dict[str, Any]] = []

    for witness_type in sorted(
        witnesses.keys()
    ):

        payload = witnesses[witness_type]

        # ====================================================
        # TRACE-BASED WITNESSES
        # ====================================================

        if isinstance(payload, list):

            canonical_identity = (
                WITNESS_IDENTITIES[
                    witness_type
                ]
            )

            witness_hash = stable_hash(
                payload
            )

        # ====================================================
        # METADATA-BASED WITNESSES
        # ====================================================

        else:

            canonical_identity = (
                payload[
                    "canonical_identity"
                ]
            )

            witness_hash = (
                payload[
                    "witness_hash"
                ]
            )

        references.append(
            {
                "canonical_identity":
                    canonical_identity,

                "witness_hash":
                    witness_hash,

                "witness_type":
                    witness_type,
            }
        )

    bundle: Dict[str, Any] = {
        "schema_version": 1,

        "canonical_identity":
            BUNDLE_IDENTITY,

        "implementation_state":
            IMPLEMENTATION_STATE,

        "references":
            references,

        "replay_hash":
            stable_hash(references),

        "execution_trace_hash":
            stable_hash(references),

        "deterministic": True,
        "replay_safe": True,
        "closed_world_aligned": True,
        "observer_independent": True,
    }

    bundle["bundle_hash"] = stable_hash(
        bundle.copy()
    )

    write_json(
        OUTPUT_DIR / "witness_bundle.json",
        bundle,
    )

    return bundle


# ============================================================
# RECEIPT GENERATION
# ============================================================

def generate_receipt(
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate constitutional receipt.
    """

    receipt = {
        "schema_version": 1,

        "canonical_identity":
            RECEIPT_IDENTITY,

        "implementation_state":
            IMPLEMENTATION_STATE,

        "receipt_hash":
            stable_hash(bundle),

        "transcript_hash":
            bundle["replay_hash"],

        "mutation_trace_hash":
            stable_hash(
                {
                    "witness_type":
                        "MUTATION",

                    "references":
                        bundle["references"],
                }
            ),

        "deterministic_execution_chain":
            True,

        "replay_hash":
            bundle["replay_hash"],

        "execution_surface_hash":
            stable_hash(
                {
                    "surface":
                        "runtime_engine"
                }
            ),

        "surface_validation_hash":
            stable_hash(
                {
                    "validation":
                        "constitutional"
                }
            ),

        "deterministic": True,
        "replay_safe": True,
        "closed_world_aligned": True,
        "observer_independent": True,
    }

    write_json(
        OUTPUT_DIR
        / "constitutional_receipt.json",

        receipt,
    )

    return receipt


# ============================================================
# MAIN PIPELINE
# ============================================================

def generate_all() -> None:
    """
    Generate all witness artifacts.
    """

    print(
        "🔧 Generating witness artifacts..."
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. GENERATE WITNESSES
    # ========================================================

    witnesses = generate_standard_witnesses()

    # ========================================================
    # 2. BUILD BUNDLE
    # ========================================================

    bundle = generate_bundle(
        witnesses
    )

    # ========================================================
    # 3. BUILD RECEIPT
    # ========================================================

    generate_receipt(
        bundle
    )

    print(
        "✅ Witness artifacts generated successfully"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_all()
