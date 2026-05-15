from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


# ============================================================
# CONSTITUTIONAL CONSTANTS
# ============================================================

WITNESS_SCHEMA = (
    "afritech.proof.witness.replay_witness.v1"
)

WITNESS_AUTHORITY = "PROOF"

CANONICAL_IDENTITY = (
    "afritech.proof.witness.replay_witness"
)

SUPPORTED_HASH_ALGORITHM = "sha256"

REQUIRED_WITNESS_FIELDS = (
    "receipt_hash",
    "replay_hash",
    "execution_trace_hash",
    "transcript_hash",
    "mutation_trace_hash",
)

FORBIDDEN_WITNESS_FIELDS = (
    "observer_identity",
    "filesystem_ordering",
    "probabilistic_context",
    "reflection_context",
)


# ============================================================
# CONSTITUTIONAL IDENTITY
# ============================================================

CANONICAL_IDENTITY = (
    "afritech.proof.witness.replay_witness"
)

IMPLEMENTATION_STATE = "IMPLEMENTED"

REPLAY_ADMISSIBLE = True

DETERMINISTIC = True

PROOF_ADMISSIBLE = True

RUNTIME_ADMISSIBLE = False

CLOSED_WORLD_ALIGNED = True

OBSERVER_INDEPENDENT = True

REPLAY_SAFE = True

WITNESS_TYPE = "REPLAY"

REPLAY_SIGNIFICANCE = "CRITICAL"

# ============================================================
# FAILURE TYPES
# ============================================================

class ReplayWitnessViolation(
    Exception,
):
    """
    Constitutional replay witness violation.
    """


class ReplayWitnessValidationError(
    ReplayWitnessViolation,
):
    """
    Raised when witness validation fails.
    """


class ReplayWitnessDeterminismError(
    ReplayWitnessViolation,
):
    """
    Raised when deterministic guarantees fail.
    """


# ============================================================
# HASHING
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
# REPLAY WITNESS
# ============================================================

@dataclass(frozen=True)
class ReplayWitness:

    # --------------------------------------------------------
    # IDENTITY
    # --------------------------------------------------------

    schema: str

    authority: str

    canonical_identity: str

    witness_id: str

    # --------------------------------------------------------
    # REPLAY
    # --------------------------------------------------------

    replay_hash: str

    receipt_hash: str

    execution_trace_hash: str

    transcript_hash: str

    mutation_trace_hash: str

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    execution_surface: str

    epoch_id: str

    registry_hash: str

    invariant_hash: str

    # --------------------------------------------------------
    # TIMING
    # --------------------------------------------------------

    generated_at: str

    hash_algorithm: str

    # --------------------------------------------------------
    # VALIDATION FLAGS
    # --------------------------------------------------------

    replay_safe: bool

    deterministic: bool

    observer_independent: bool

    admissible: bool

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

        return asdict(self)

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

        # ----------------------------------------------------
        # REQUIRED FLAGS
        # ----------------------------------------------------

        if not self.replay_safe:

            raise ReplayWitnessValidationError(
                "witness is not replay safe"
            )

        if not self.deterministic:

            raise ReplayWitnessDeterminismError(
                "witness is not deterministic"
            )

        if not self.observer_independent:

            raise ReplayWitnessValidationError(
                "observer-dependent witness detected"
            )

        if not self.admissible:

            raise ReplayWitnessValidationError(
                "inadmissible replay witness"
            )

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        for field_name in REQUIRED_WITNESS_FIELDS:

            value = getattr(
                self,
                field_name,
                None,
            )

            if not value:

                raise ReplayWitnessValidationError(
                    f"missing required witness "
                    f"field: {field_name}"
                )

        # ----------------------------------------------------
        # FORBIDDEN METADATA
        # ----------------------------------------------------

        for forbidden in FORBIDDEN_WITNESS_FIELDS:

            if forbidden in self.metadata:

                raise ReplayWitnessValidationError(
                    f"forbidden metadata detected: "
                    f"{forbidden}"
                )

        # ----------------------------------------------------
        # HASH ALGORITHM
        # ----------------------------------------------------

        if (
            self.hash_algorithm
            != SUPPORTED_HASH_ALGORITHM
        ):

            raise ReplayWitnessValidationError(
                "unsupported hash algorithm"
            )

        # ----------------------------------------------------
        # CANONICAL IDENTITY
        # ----------------------------------------------------

        if (
            self.canonical_identity
            != CANONICAL_IDENTITY
        ):

            raise ReplayWitnessValidationError(
                "canonical identity mismatch"
            )

    # --------------------------------------------------------
    # WITNESS HASH
    # --------------------------------------------------------

    def witness_hash(
        self,
    ) -> str:

        return deterministic_hash(
            self.to_dict()
        )


# ============================================================
# WITNESS FACTORY
# ============================================================

def create_replay_witness(
    *,
    replay_hash: str,
    receipt_hash: str,
    execution_trace_hash: str,
    transcript_hash: str,
    mutation_trace_hash: str,
    execution_surface: str,
    epoch_id: str,
    registry_hash: str,
    invariant_hash: str,
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> ReplayWitness:

    metadata = metadata or {}

    # --------------------------------------------------------
    # DETERMINISTIC IDENTITY
    # --------------------------------------------------------

    witness_seed = {

        "replay_hash":
            replay_hash,

        "receipt_hash":
            receipt_hash,

        "execution_trace_hash":
            execution_trace_hash,

        "transcript_hash":
            transcript_hash,

        "mutation_trace_hash":
            mutation_trace_hash,

        "execution_surface":
            execution_surface,

        "epoch_id":
            epoch_id,

        "registry_hash":
            registry_hash,

        "invariant_hash":
            invariant_hash,
    }

    witness_id = deterministic_hash(
        witness_seed
    )

    witness = ReplayWitness(

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------

        schema=WITNESS_SCHEMA,

        authority=WITNESS_AUTHORITY,

        canonical_identity=CANONICAL_IDENTITY,

        witness_id=witness_id,

        # ----------------------------------------------------
        # REPLAY
        # ----------------------------------------------------

        replay_hash=replay_hash,

        receipt_hash=receipt_hash,

        execution_trace_hash=execution_trace_hash,

        transcript_hash=transcript_hash,

        mutation_trace_hash=mutation_trace_hash,

        # ----------------------------------------------------
        # EXECUTION
        # ----------------------------------------------------

        execution_surface=execution_surface,

        epoch_id=epoch_id,

        registry_hash=registry_hash,

        invariant_hash=invariant_hash,

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
        # FLAGS
        # ----------------------------------------------------

        replay_safe=True,

        deterministic=True,

        observer_independent=True,

        admissible=True,

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        metadata=metadata,
    )

    witness.validate()

    return witness


# ============================================================
# PERSISTENCE
# ============================================================

def write_replay_witness(
    *,
    witness: ReplayWitness,
    output_path: Path,
) -> None:

    witness.validate()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        witness.to_json(),
        encoding="utf-8",
    )


def load_replay_witness(
    path: Path,
) -> ReplayWitness:

    raw = path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw)

    witness = ReplayWitness(
        **data
    )

    witness.validate()

    return witness


# ============================================================
# REPLAY EQUIVALENCE
# ============================================================

def replay_equivalent(
    left: ReplayWitness,
    right: ReplayWitness,
) -> bool:

    left.validate()
    right.validate()

    comparable_fields = (

        "replay_hash",
        "receipt_hash",
        "execution_trace_hash",
        "transcript_hash",
        "mutation_trace_hash",
        "execution_surface",
        "epoch_id",
        "registry_hash",
        "invariant_hash",
    )

    for field_name in comparable_fields:

        if (
            getattr(left, field_name)
            != getattr(right, field_name)
        ):

            return False

    return True


# ============================================================
# WITNESS BUNDLE
# ============================================================

@dataclass(frozen=True)
class ReplayWitnessBundle:

    witnesses: List[ReplayWitness]

    bundle_hash: str

    generated_at: str

    deterministic: bool

    replay_safe: bool

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise ReplayWitnessValidationError(
                "bundle is not deterministic"
            )

        if not self.replay_safe:

            raise ReplayWitnessValidationError(
                "bundle is not replay safe"
            )

        for witness in self.witnesses:

            witness.validate()

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {

            "witnesses": [
                witness.to_dict()
                for witness in self.witnesses
            ],

            "bundle_hash":
                self.bundle_hash,

            "generated_at":
                self.generated_at,

            "deterministic":
                self.deterministic,

            "replay_safe":
                self.replay_safe,
        }


def create_witness_bundle(
    witnesses: List[ReplayWitness],
) -> ReplayWitnessBundle:

    for witness in witnesses:

        witness.validate()

    bundle_hash = deterministic_hash(

        [
            witness.witness_hash()
            for witness in witnesses
        ]
    )

    bundle = ReplayWitnessBundle(

        witnesses=witnesses,

        bundle_hash=bundle_hash,

        generated_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        deterministic=True,

        replay_safe=True,
    )

    bundle.validate()

    return bundle