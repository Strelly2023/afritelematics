from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


# ============================================================
# CONSTITUTIONAL CONSTANTS
# ============================================================

WITNESS_SCHEMA = (
    "afritech.proof.witness.transcript_witness.v1"
)

CANONICAL_IDENTITY = (
    "afritech.proof.witness.transcript_witness"
)

WITNESS_AUTHORITY = "PROOF"

SUPPORTED_HASH_ALGORITHM = "sha256"

FORBIDDEN_TRANSCRIPT_FIELDS = {

    "observer_identity",
    "reflection_context",
    "probabilistic_context",
    "filesystem_ordering",
    "runtime_memory_address",

}

REQUIRED_TRANSCRIPT_FIELDS = (

    "transcript_hash",
    "execution_trace_hash",
    "mutation_trace_hash",
    "receipt_hash",
    "replay_hash",

)


# ============================================================
# CONSTITUTIONAL IDENTITY
# ============================================================

CANONICAL_IDENTITY = (
    "afritech.proof.witness.transcript_witness"
)

IMPLEMENTATION_STATE = "PARTIAL"

REPLAY_ADMISSIBLE = True

DETERMINISTIC = True

PROOF_ADMISSIBLE = "CONDITIONAL"

RUNTIME_ADMISSIBLE = False

CLOSED_WORLD_ALIGNED = True

OBSERVER_INDEPENDENT = True

REPLAY_SAFE = True

WITNESS_TYPE = "TRANSCRIPT"

REPLAY_SIGNIFICANCE = "CRITICAL"

# ============================================================
# EXCEPTIONS
# ============================================================

class TranscriptWitnessViolation(
    Exception,
):
    """
    Constitutional transcript witness violation.
    """


class TranscriptWitnessValidationError(
    TranscriptWitnessViolation,
):
    """
    Transcript witness validation failure.
    """


class TranscriptDeterminismError(
    TranscriptWitnessViolation,
):
    """
    Deterministic transcript semantics failure.
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
# TRANSCRIPT EVENT
# ============================================================

@dataclass(frozen=True)
class TranscriptEvent:

    event_order: int

    event_type: str

    execution_surface: str

    event_hash: str

    deterministic: bool

    replay_safe: bool

    invariant_preserving: bool

    metadata: Dict[str, Any]

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise TranscriptDeterminismError(
                "non-deterministic transcript event"
            )

        if not self.replay_safe:

            raise TranscriptWitnessValidationError(
                "transcript event is not replay safe"
            )

        if not self.invariant_preserving:

            raise TranscriptWitnessValidationError(
                "transcript event violates invariants"
            )

        for forbidden in FORBIDDEN_TRANSCRIPT_FIELDS:

            if forbidden in self.metadata:

                raise TranscriptWitnessValidationError(
                    f"forbidden transcript metadata: "
                    f"{forbidden}"
                )


# ============================================================
# TRANSCRIPT WITNESS
# ============================================================

@dataclass(frozen=True)
class TranscriptWitness:

    # --------------------------------------------------------
    # IDENTITY
    # --------------------------------------------------------

    schema: str

    authority: str

    canonical_identity: str

    witness_id: str

    # --------------------------------------------------------
    # HASHES
    # --------------------------------------------------------

    transcript_hash: str

    execution_trace_hash: str

    mutation_trace_hash: str

    replay_hash: str

    receipt_hash: str

    registry_hash: str

    invariant_hash: str

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    execution_surface: str

    epoch_id: str

    # --------------------------------------------------------
    # TRANSCRIPT EVENTS
    # --------------------------------------------------------

    transcript_events: List[
        TranscriptEvent
    ]

    # --------------------------------------------------------
    # VALIDATION FLAGS
    # --------------------------------------------------------

    replay_safe: bool

    deterministic: bool

    observer_independent: bool

    invariant_preserving: bool

    admissible: bool

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

        result = asdict(self)

        result["transcript_events"] = [

            asdict(event)
            for event in self.transcript_events

        ]

        return result

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

            raise TranscriptWitnessValidationError(
                "transcript witness not replay safe"
            )

        if not self.deterministic:

            raise TranscriptDeterminismError(
                "transcript witness not deterministic"
            )

        if not self.observer_independent:

            raise TranscriptWitnessValidationError(
                "observer-dependent transcript"
            )

        if not self.invariant_preserving:

            raise TranscriptWitnessValidationError(
                "transcript violates invariants"
            )

        if not self.admissible:

            raise TranscriptWitnessValidationError(
                "inadmissible transcript witness"
            )

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        for field_name in REQUIRED_TRANSCRIPT_FIELDS:

            value = getattr(
                self,
                field_name,
                None,
            )

            if not value:

                raise TranscriptWitnessValidationError(
                    f"missing required field: "
                    f"{field_name}"
                )

        # ----------------------------------------------------
        # HASH ALGORITHM
        # ----------------------------------------------------

        if (
            self.hash_algorithm
            != SUPPORTED_HASH_ALGORITHM
        ):

            raise TranscriptWitnessValidationError(
                "unsupported hash algorithm"
            )

        # ----------------------------------------------------
        # CANONICAL IDENTITY
        # ----------------------------------------------------

        if (
            self.canonical_identity
            != CANONICAL_IDENTITY
        ):

            raise TranscriptWitnessValidationError(
                "canonical identity mismatch"
            )

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        for forbidden in FORBIDDEN_TRANSCRIPT_FIELDS:

            if forbidden in self.metadata:

                raise TranscriptWitnessValidationError(
                    f"forbidden transcript metadata: "
                    f"{forbidden}"
                )

        # ----------------------------------------------------
        # EVENT ORDERING
        # ----------------------------------------------------

        previous_order = -1

        for event in self.transcript_events:

            event.validate()

            if (
                event.event_order
                <= previous_order
            ):

                raise TranscriptDeterminismError(
                    "transcript event ordering "
                    "is not monotonic"
                )

            previous_order = (
                event.event_order
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

def create_transcript_witness(
    *,
    execution_trace_hash: str,
    mutation_trace_hash: str,
    replay_hash: str,
    receipt_hash: str,
    registry_hash: str,
    invariant_hash: str,
    execution_surface: str,
    epoch_id: str,
    transcript_events: List[
        TranscriptEvent
    ],
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> TranscriptWitness:

    metadata = metadata or {}

    # --------------------------------------------------------
    # VALIDATE EVENTS
    # --------------------------------------------------------

    for event in transcript_events:

        event.validate()

    # --------------------------------------------------------
    # TRANSCRIPT HASH
    # --------------------------------------------------------

    transcript_hash = deterministic_hash(

        [
            asdict(event)
            for event in transcript_events
        ]
    )

    # --------------------------------------------------------
    # WITNESS ID
    # --------------------------------------------------------

    witness_id = deterministic_hash({

        "transcript_hash":
            transcript_hash,

        "execution_trace_hash":
            execution_trace_hash,

        "mutation_trace_hash":
            mutation_trace_hash,

        "epoch_id":
            epoch_id,
    })

    witness = TranscriptWitness(

        # ----------------------------------------------------
        # IDENTITY
        # ----------------------------------------------------

        schema=WITNESS_SCHEMA,

        authority=WITNESS_AUTHORITY,

        canonical_identity=CANONICAL_IDENTITY,

        witness_id=witness_id,

        # ----------------------------------------------------
        # HASHES
        # ----------------------------------------------------

        transcript_hash=transcript_hash,

        execution_trace_hash=(
            execution_trace_hash
        ),

        mutation_trace_hash=(
            mutation_trace_hash
        ),

        replay_hash=replay_hash,

        receipt_hash=receipt_hash,

        registry_hash=registry_hash,

        invariant_hash=invariant_hash,

        # ----------------------------------------------------
        # EXECUTION
        # ----------------------------------------------------

        execution_surface=execution_surface,

        epoch_id=epoch_id,

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        transcript_events=(
            transcript_events
        ),

        # ----------------------------------------------------
        # FLAGS
        # ----------------------------------------------------

        replay_safe=True,

        deterministic=True,

        observer_independent=True,

        invariant_preserving=True,

        admissible=True,

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

    witness.validate()

    return witness


# ============================================================
# PERSISTENCE
# ============================================================

def write_transcript_witness(
    *,
    witness: TranscriptWitness,
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


def load_transcript_witness(
    path: Path,
) -> TranscriptWitness:

    raw = path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw)

    transcript_events = [

        TranscriptEvent(**item)
        for item in data.pop(
            "transcript_events",
            [],
        )

    ]

    witness = TranscriptWitness(

        transcript_events=(
            transcript_events
        ),

        **data,
    )

    witness.validate()

    return witness


# ============================================================
# REPLAY EQUIVALENCE
# ============================================================

def transcript_replay_equivalent(
    left: TranscriptWitness,
    right: TranscriptWitness,
) -> bool:

    left.validate()
    right.validate()

    comparable_fields = (

        "transcript_hash",
        "execution_trace_hash",
        "mutation_trace_hash",
        "replay_hash",
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


# ============================================================
# WITNESS BUNDLE
# ============================================================

@dataclass(frozen=True)
class TranscriptWitnessBundle:

    witnesses: List[
        TranscriptWitness
    ]

    bundle_hash: str

    deterministic: bool

    replay_safe: bool

    generated_at: str

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise TranscriptDeterminismError(
                "bundle is not deterministic"
            )

        if not self.replay_safe:

            raise TranscriptWitnessValidationError(
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

            "deterministic":
                self.deterministic,

            "replay_safe":
                self.replay_safe,

            "generated_at":
                self.generated_at,
        }


def create_transcript_bundle(
    witnesses: List[
        TranscriptWitness
    ],
) -> TranscriptWitnessBundle:

    for witness in witnesses:

        witness.validate()

    bundle_hash = deterministic_hash(

        [
            witness.witness_hash()
            for witness in witnesses
        ]
    )

    bundle = TranscriptWitnessBundle(

        witnesses=witnesses,

        bundle_hash=bundle_hash,

        deterministic=True,

        replay_safe=True,

        generated_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    bundle.validate()

    return bundle