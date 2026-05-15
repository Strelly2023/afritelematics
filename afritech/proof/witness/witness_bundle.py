from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from afritech.proof.witness.replay_witness import (
    ReplayWitness,
)

from afritech.proof.witness.mutation_witness import (
    MutationWitness,
)

from afritech.proof.witness.transcript_witness import (
    TranscriptWitness,
)

from afritech.proof.witness.execution_witness import (
    ExecutionWitness,
)


# ============================================================
# CONSTITUTIONAL CONSTANTS
# ============================================================

BUNDLE_SCHEMA = (
    "afritech.proof.witness.witness_bundle.v1"
)

CANONICAL_IDENTITY = (
    "afritech.proof.witness.witness_bundle"
)

BUNDLE_AUTHORITY = "PROOF"

SUPPORTED_HASH_ALGORITHM = "sha256"

FORBIDDEN_BUNDLE_FIELDS = {

    "observer_identity",
    "reflection_context",
    "probabilistic_context",
    "filesystem_ordering",
    "runtime_memory_address",

}


# ============================================================
# CONSTITUTIONAL IDENTITY
# ============================================================

CANONICAL_IDENTITY = (
    "afritech.proof.witness.witness_bundle"
)

IMPLEMENTATION_STATE = "IMPLEMENTED"

REPLAY_ADMISSIBLE = True

DETERMINISTIC = True

PROOF_ADMISSIBLE = True

RUNTIME_ADMISSIBLE = False

CLOSED_WORLD_ALIGNED = True

OBSERVER_INDEPENDENT = True

REPLAY_SAFE = True

WITNESS_TYPE = "BUNDLE"

REPLAY_SIGNIFICANCE = "CRITICAL"

# ============================================================
# EXCEPTIONS
# ============================================================

class WitnessBundleViolation(
    Exception,
):
    """
    Constitutional witness bundle violation.
    """


class WitnessBundleValidationError(
    WitnessBundleViolation,
):
    """
    Witness bundle validation failure.
    """


class WitnessBundleDeterminismError(
    WitnessBundleViolation,
):
    """
    Witness bundle determinism failure.
    """


# ============================================================
# DETERMINISTIC SERIALIZATION
# ============================================================

def stable_json_dumps(
    value: Any,
) -> str:

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def deterministic_hash(
    value: Any,
) -> str:

    encoded = stable_json_dumps(
        value
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


# ============================================================
# WITNESS REFERENCE
# ============================================================

@dataclass(frozen=True)
class WitnessReference:

    witness_type: str

    witness_hash: str

    witness_id: str

    deterministic: bool

    replay_safe: bool

    admissible: bool

    metadata: Dict[str, Any]

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise WitnessBundleDeterminismError(
                "non-deterministic witness reference"
            )

        if not self.replay_safe:

            raise WitnessBundleValidationError(
                "non replay-safe witness reference"
            )

        if not self.admissible:

            raise WitnessBundleValidationError(
                "inadmissible witness reference"
            )

        for forbidden in FORBIDDEN_BUNDLE_FIELDS:

            if forbidden in self.metadata:

                raise WitnessBundleValidationError(
                    f"forbidden metadata field: "
                    f"{forbidden}"
                )


# ============================================================
# WITNESS BUNDLE
# ============================================================

@dataclass(frozen=True)
class WitnessBundle:

    # --------------------------------------------------------
    # IDENTITY
    # --------------------------------------------------------

    schema: str

    authority: str

    canonical_identity: str

    bundle_id: str

    # --------------------------------------------------------
    # WITNESS REFERENCES
    # --------------------------------------------------------

    replay_witnesses: List[
        ReplayWitness
    ]

    mutation_witnesses: List[
        MutationWitness
    ]

    transcript_witnesses: List[
        TranscriptWitness
    ]

    execution_witnesses: List[
        ExecutionWitness
    ]

    references: List[
        WitnessReference
    ]

    # --------------------------------------------------------
    # GLOBAL HASHES
    # --------------------------------------------------------

    bundle_hash: str

    replay_hash: str

    transcript_hash: str

    mutation_trace_hash: str

    execution_trace_hash: str

    receipt_hash: str

    registry_hash: str

    invariant_hash: str

    # --------------------------------------------------------
    # EXECUTION CONTEXT
    # --------------------------------------------------------

    epoch_id: str

    execution_surface: str

    # --------------------------------------------------------
    # VALIDATION FLAGS
    # --------------------------------------------------------

    replay_safe: bool

    deterministic: bool

    observer_independent: bool

    invariant_preserving: bool

    admissible: bool

    closed_world_aligned: bool

    # --------------------------------------------------------
    # TIMING
    # --------------------------------------------------------

    generated_at: str

    hash_algorithm: str

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata: Dict[str, Any]

    # --------------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------------

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {

            "schema":
                self.schema,

            "authority":
                self.authority,

            "canonical_identity":
                self.canonical_identity,

            "bundle_id":
                self.bundle_id,

            "replay_witnesses": [

                witness.to_dict()
                for witness
                in self.replay_witnesses

            ],

            "mutation_witnesses": [

                witness.to_dict()
                for witness
                in self.mutation_witnesses

            ],

            "transcript_witnesses": [

                witness.to_dict()
                for witness
                in self.transcript_witnesses

            ],

            "execution_witnesses": [

                witness.to_dict()
                for witness
                in self.execution_witnesses

            ],

            "references": [

                asdict(reference)
                for reference
                in self.references

            ],

            "bundle_hash":
                self.bundle_hash,

            "replay_hash":
                self.replay_hash,

            "transcript_hash":
                self.transcript_hash,

            "mutation_trace_hash":
                self.mutation_trace_hash,

            "execution_trace_hash":
                self.execution_trace_hash,

            "receipt_hash":
                self.receipt_hash,

            "registry_hash":
                self.registry_hash,

            "invariant_hash":
                self.invariant_hash,

            "epoch_id":
                self.epoch_id,

            "execution_surface":
                self.execution_surface,

            "replay_safe":
                self.replay_safe,

            "deterministic":
                self.deterministic,

            "observer_independent":
                self.observer_independent,

            "invariant_preserving":
                self.invariant_preserving,

            "admissible":
                self.admissible,

            "closed_world_aligned":
                self.closed_world_aligned,

            "generated_at":
                self.generated_at,

            "hash_algorithm":
                self.hash_algorithm,

            "metadata":
                self.metadata,
        }

    def to_json(
        self,
    ) -> str:

        return stable_json_dumps(
            self.to_dict()
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def validate(
        self,
    ) -> None:

        if not self.replay_safe:

            raise WitnessBundleValidationError(
                "bundle is not replay safe"
            )

        if not self.deterministic:

            raise WitnessBundleDeterminismError(
                "bundle is not deterministic"
            )

        if not self.observer_independent:

            raise WitnessBundleValidationError(
                "observer-dependent bundle"
            )

        if not self.invariant_preserving:

            raise WitnessBundleValidationError(
                "bundle violates invariants"
            )

        if not self.admissible:

            raise WitnessBundleValidationError(
                "inadmissible witness bundle"
            )

        if not self.closed_world_aligned:

            raise WitnessBundleValidationError(
                "bundle violates closed-world "
                "semantics"
            )

        if (
            self.hash_algorithm
            != SUPPORTED_HASH_ALGORITHM
        ):

            raise WitnessBundleValidationError(
                "unsupported hash algorithm"
            )

        if (
            self.canonical_identity
            != CANONICAL_IDENTITY
        ):

            raise WitnessBundleValidationError(
                "canonical identity mismatch"
            )

        for forbidden in FORBIDDEN_BUNDLE_FIELDS:

            if forbidden in self.metadata:

                raise WitnessBundleValidationError(
                    f"forbidden metadata field: "
                    f"{forbidden}"
                )

        # ----------------------------------------------------
        # WITNESS VALIDATION
        # ----------------------------------------------------

        for witness in self.replay_witnesses:

            witness.validate()

        for witness in self.mutation_witnesses:

            witness.validate()

        for witness in self.transcript_witnesses:

            witness.validate()

        for witness in self.execution_witnesses:

            witness.validate()

        # ----------------------------------------------------
        # REFERENCE VALIDATION
        # ----------------------------------------------------

        for reference in self.references:

            reference.validate()

        # ----------------------------------------------------
        # CONSISTENCY VALIDATION
        # ----------------------------------------------------

        self._validate_hash_consistency()

    # --------------------------------------------------------
    # CONSISTENCY VALIDATION
    # --------------------------------------------------------

    def _validate_hash_consistency(
        self,
    ) -> None:

        for witness in self.replay_witnesses:

            if (
                witness.replay_hash
                != self.replay_hash
            ):

                raise WitnessBundleValidationError(
                    "replay hash mismatch"
                )

        for witness in self.transcript_witnesses:

            if (
                witness.transcript_hash
                != self.transcript_hash
            ):

                raise WitnessBundleValidationError(
                    "transcript hash mismatch"
                )

        for witness in self.mutation_witnesses:

            if (
                witness.mutation_trace_hash
                != self.mutation_trace_hash
            ):

                raise WitnessBundleValidationError(
                    "mutation trace hash mismatch"
                )

        for witness in self.execution_witnesses:

            if (
                witness.execution_trace_hash
                != self.execution_trace_hash
            ):

                raise WitnessBundleValidationError(
                    "execution trace hash mismatch"
                )

    # --------------------------------------------------------
    # BUNDLE HASH
    # --------------------------------------------------------

    def witness_hash(
        self,
    ) -> str:

        return deterministic_hash(
            self.to_dict()
        )


# ============================================================
# REFERENCE FACTORY
# ============================================================

def create_reference(
    *,
    witness_type: str,
    witness_hash: str,
    witness_id: str,
) -> WitnessReference:

    return WitnessReference(

        witness_type=witness_type,

        witness_hash=witness_hash,

        witness_id=witness_id,

        deterministic=True,

        replay_safe=True,

        admissible=True,

        metadata={},
    )


# ============================================================
# BUNDLE FACTORY
# ============================================================

def create_witness_bundle(
    *,
    replay_witnesses: List[
        ReplayWitness
    ],
    mutation_witnesses: List[
        MutationWitness
    ],
    transcript_witnesses: List[
        TranscriptWitness
    ],
    execution_witnesses: List[
        ExecutionWitness
    ],
    epoch_id: str,
    execution_surface: str,
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> WitnessBundle:

    metadata = metadata or {}

    # --------------------------------------------------------
    # VALIDATE INPUT WITNESSES
    # --------------------------------------------------------

    for witness in replay_witnesses:

        witness.validate()

    for witness in mutation_witnesses:

        witness.validate()

    for witness in transcript_witnesses:

        witness.validate()

    for witness in execution_witnesses:

        witness.validate()

    # --------------------------------------------------------
    # GLOBAL HASHES
    # --------------------------------------------------------

    replay_hash = (
        replay_witnesses[0].replay_hash
    )

    transcript_hash = (
        transcript_witnesses[0]
        .transcript_hash
    )

    mutation_trace_hash = (
        mutation_witnesses[0]
        .mutation_trace_hash
    )

    execution_trace_hash = (
        execution_witnesses[0]
        .execution_trace_hash
    )

    receipt_hash = (
        replay_witnesses[0]
        .receipt_hash
    )

    registry_hash = (
        replay_witnesses[0]
        .registry_hash
    )

    invariant_hash = (
        replay_witnesses[0]
        .invariant_hash
    )

    # --------------------------------------------------------
    # REFERENCES
    # --------------------------------------------------------

    references: List[
        WitnessReference
    ] = []

    for witness in replay_witnesses:

        references.append(

            create_reference(

                witness_type="REPLAY",

                witness_hash=(
                    witness.witness_hash()
                ),

                witness_id=(
                    witness.witness_id
                ),
            )
        )

    for witness in mutation_witnesses:

        references.append(

            create_reference(

                witness_type="MUTATION",

                witness_hash=(
                    witness.witness_hash()
                ),

                witness_id=(
                    witness.witness_id
                ),
            )
        )

    for witness in transcript_witnesses:

        references.append(

            create_reference(

                witness_type="TRANSCRIPT",

                witness_hash=(
                    witness.witness_hash()
                ),

                witness_id=(
                    witness.witness_id
                ),
            )
        )

    for witness in execution_witnesses:

        references.append(

            create_reference(

                witness_type="EXECUTION",

                witness_hash=(
                    witness.witness_hash()
                ),

                witness_id=(
                    witness.witness_id
                ),
            )
        )

    # --------------------------------------------------------
    # BUNDLE HASH
    # --------------------------------------------------------

    bundle_hash = deterministic_hash({

        "replay": [

            witness.witness_hash()
            for witness
            in replay_witnesses

        ],

        "mutation": [

            witness.witness_hash()
            for witness
            in mutation_witnesses

        ],

        "transcript": [

            witness.witness_hash()
            for witness
            in transcript_witnesses

        ],

        "execution": [

            witness.witness_hash()
            for witness
            in execution_witnesses

        ],
    })

    # --------------------------------------------------------
    # BUNDLE ID
    # --------------------------------------------------------

    bundle_id = deterministic_hash({

        "bundle_hash":
            bundle_hash,

        "epoch_id":
            epoch_id,

        "execution_surface":
            execution_surface,
    })

    bundle = WitnessBundle(

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------

        schema=BUNDLE_SCHEMA,

        authority=BUNDLE_AUTHORITY,

        canonical_identity=(
            CANONICAL_IDENTITY
        ),

        bundle_id=bundle_id,

        # ----------------------------------------------------
        # WITNESSES
        # ----------------------------------------------------

        replay_witnesses=(
            replay_witnesses
        ),

        mutation_witnesses=(
            mutation_witnesses
        ),

        transcript_witnesses=(
            transcript_witnesses
        ),

        execution_witnesses=(
            execution_witnesses
        ),

        references=references,

        # ----------------------------------------------------
        # HASHES
        # ----------------------------------------------------

        bundle_hash=bundle_hash,

        replay_hash=replay_hash,

        transcript_hash=(
            transcript_hash
        ),

        mutation_trace_hash=(
            mutation_trace_hash
        ),

        execution_trace_hash=(
            execution_trace_hash
        ),

        receipt_hash=receipt_hash,

        registry_hash=registry_hash,

        invariant_hash=invariant_hash,

        # ----------------------------------------------------
        # EXECUTION CONTEXT
        # ----------------------------------------------------

        epoch_id=epoch_id,

        execution_surface=(
            execution_surface
        ),

        # ----------------------------------------------------
        # FLAGS
        # ----------------------------------------------------

        replay_safe=True,

        deterministic=True,

        observer_independent=True,

        invariant_preserving=True,

        admissible=True,

        closed_world_aligned=True,

        # ----------------------------------------------------
        # TIMING
        # ----------------------------------------------------

        generated_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        hash_algorithm=(
            SUPPORTED_HASH_ALGORITHM
        ),

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        metadata=metadata,
    )

    bundle.validate()

    return bundle


# ============================================================
# PERSISTENCE
# ============================================================

def write_witness_bundle(
    *,
    bundle: WitnessBundle,
    output_path: Path,
) -> None:

    bundle.validate()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(

        bundle.to_json(),

        encoding="utf-8",
    )


# ============================================================
# REPLAY EQUIVALENCE
# ============================================================

def bundle_replay_equivalent(
    left: WitnessBundle,
    right: WitnessBundle,
) -> bool:

    left.validate()
    right.validate()

    comparable_fields = (

        "bundle_hash",
        "replay_hash",
        "transcript_hash",
        "mutation_trace_hash",
        "execution_trace_hash",
        "receipt_hash",
        "registry_hash",
        "invariant_hash",
        "epoch_id",
    )

    for field_name in comparable_fields:

        if (
            getattr(left, field_name)
            != getattr(right, field_name)
        ):

            return False

    return True