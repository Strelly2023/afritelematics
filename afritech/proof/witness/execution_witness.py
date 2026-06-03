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
    "afritech.proof.witness.execution_witness.v1"
)

CANONICAL_IDENTITY = (
    "afritech.proof.witness.execution_witness"
)

WITNESS_AUTHORITY = "PROOF"

SUPPORTED_HASH_ALGORITHM = "sha256"

FORBIDDEN_EXECUTION_FIELDS = {

    "observer_identity",
    "filesystem_ordering",
    "reflection_context",
    "probabilistic_context",
    "runtime_memory_address",
    "non_deterministic_seed",

}

REQUIRED_EXECUTION_FIELDS = (

    "execution_hash",
    "execution_trace_hash",
    "mutation_trace_hash",
    "transcript_hash",
    "receipt_hash",
    "replay_hash",

)

AUTHORIZED_EXECUTION_SURFACES = {

    "afritech.core.runtime.admission",
    "afritech.core.runtime.replay",
    "afritech.kernel.constitutional_gateway",

}


# ============================================================
# CONSTITUTIONAL IDENTITY
# ============================================================

CANONICAL_IDENTITY = (
    "afritech.proof.witness.execution_witness"
)

IMPLEMENTATION_STATE = "IMPLEMENTED"

REPLAY_ADMISSIBLE = True

DETERMINISTIC = True

PROOF_ADMISSIBLE = True

RUNTIME_ADMISSIBLE = False

CLOSED_WORLD_ALIGNED = True

OBSERVER_INDEPENDENT = True

REPLAY_SAFE = True

WITNESS_TYPE = "EXECUTION"

REPLAY_SIGNIFICANCE = "REQUIRED"

# ============================================================
# EXCEPTIONS
# ============================================================

class ExecutionWitnessViolation(
    Exception,
):
    """
    Constitutional execution witness violation.
    """


class ExecutionWitnessValidationError(
    ExecutionWitnessViolation,
):
    """
    Execution witness validation failure.
    """


class ExecutionDeterminismError(
    ExecutionWitnessViolation,
):
    """
    Deterministic execution failure.
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
# EXECUTION STEP
# ============================================================

@dataclass(frozen=True)
class ExecutionStep:

    step_order: int

    execution_surface: str

    operation_type: str

    operation_hash: str

    deterministic: bool

    replay_safe: bool

    invariant_preserving: bool

    metadata: Dict[str, Any]

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise ExecutionDeterminismError(
                "non-deterministic execution step"
            )

        if not self.replay_safe:

            raise ExecutionWitnessValidationError(
                "execution step not replay safe"
            )

        if not self.invariant_preserving:

            raise ExecutionWitnessValidationError(
                "execution step violates invariants"
            )

        if (
            self.execution_surface
            not in AUTHORIZED_EXECUTION_SURFACES
        ):

            raise ExecutionWitnessValidationError(
                "unauthorized execution surface"
            )

        for forbidden in FORBIDDEN_EXECUTION_FIELDS:

            if forbidden in self.metadata:

                raise ExecutionWitnessValidationError(
                    f"forbidden execution metadata: "
                    f"{forbidden}"
                )


# ============================================================
# EXECUTION WITNESS
# ============================================================

@dataclass(frozen=True)
class ExecutionWitness:

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

    execution_hash: str

    execution_trace_hash: str

    mutation_trace_hash: str

    transcript_hash: str

    replay_hash: str

    receipt_hash: str

    registry_hash: str

    invariant_hash: str

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    execution_surface: str

    epoch_id: str

    execution_steps: List[
        ExecutionStep
    ]

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

        result = asdict(self)

        result["execution_steps"] = [

            asdict(step)
            for step in self.execution_steps

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

            raise ExecutionWitnessValidationError(
                "execution witness not replay safe"
            )

        if not self.deterministic:

            raise ExecutionDeterminismError(
                "execution witness not deterministic"
            )

        if not self.observer_independent:

            raise ExecutionWitnessValidationError(
                "observer-dependent execution witness"
            )

        if not self.invariant_preserving:

            raise ExecutionWitnessValidationError(
                "execution witness violates invariants"
            )

        if not self.admissible:

            raise ExecutionWitnessValidationError(
                "inadmissible execution witness"
            )

        if not self.closed_world_aligned:

            raise ExecutionWitnessValidationError(
                "execution witness violates "
                "closed-world semantics"
            )

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        for field_name in REQUIRED_EXECUTION_FIELDS:

            value = getattr(
                self,
                field_name,
                None,
            )

            if not value:

                raise ExecutionWitnessValidationError(
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

            raise ExecutionWitnessValidationError(
                "unsupported hash algorithm"
            )

        # ----------------------------------------------------
        # CANONICAL IDENTITY
        # ----------------------------------------------------

        if (
            self.canonical_identity
            != CANONICAL_IDENTITY
        ):

            raise ExecutionWitnessValidationError(
                "canonical identity mismatch"
            )

        # ----------------------------------------------------
        # EXECUTION SURFACE
        # ----------------------------------------------------

        if (
            self.execution_surface
            not in AUTHORIZED_EXECUTION_SURFACES
        ):

            raise ExecutionWitnessValidationError(
                "unauthorized execution surface"
            )

        # ----------------------------------------------------
        # METADATA VALIDATION
        # ----------------------------------------------------

        for forbidden in FORBIDDEN_EXECUTION_FIELDS:

            if forbidden in self.metadata:

                raise ExecutionWitnessValidationError(
                    f"forbidden metadata field: "
                    f"{forbidden}"
                )

        # ----------------------------------------------------
        # STEP VALIDATION
        # ----------------------------------------------------

        previous_order = -1

        for step in self.execution_steps:

            step.validate()

            if (
                step.step_order
                <= previous_order
            ):

                raise ExecutionDeterminismError(
                    "execution step ordering "
                    "is not strictly monotonic"
                )

            previous_order = (
                step.step_order
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

def create_execution_witness(
    *,
    execution_trace_hash: str,
    mutation_trace_hash: str,
    transcript_hash: str,
    replay_hash: str,
    receipt_hash: str,
    registry_hash: str,
    invariant_hash: str,
    execution_surface: str,
    epoch_id: str,
    execution_steps: List[
        ExecutionStep
    ],
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> ExecutionWitness:

    metadata = metadata or {}

    # --------------------------------------------------------
    # VALIDATE STEPS
    # --------------------------------------------------------

    for step in execution_steps:

        step.validate()

    # --------------------------------------------------------
    # EXECUTION HASH
    # --------------------------------------------------------

    execution_hash = deterministic_hash(

        [
            asdict(step)
            for step in execution_steps
        ]
    )

    # --------------------------------------------------------
    # WITNESS ID
    # --------------------------------------------------------

    witness_id = deterministic_hash({

        "execution_hash":
            execution_hash,

        "execution_trace_hash":
            execution_trace_hash,

        "mutation_trace_hash":
            mutation_trace_hash,

        "transcript_hash":
            transcript_hash,

        "epoch_id":
            epoch_id,
    })

    witness = ExecutionWitness(

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

        execution_hash=execution_hash,

        execution_trace_hash=(
            execution_trace_hash
        ),

        mutation_trace_hash=(
            mutation_trace_hash
        ),

        transcript_hash=(
            transcript_hash
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

        execution_steps=(
            execution_steps
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

    witness.validate()

    return witness


# ============================================================
# PERSISTENCE
# ============================================================

def write_execution_witness(
    *,
    witness: ExecutionWitness,
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


def load_execution_witness(
    path: Path,
) -> ExecutionWitness:

    raw = path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw)

    execution_steps = [

        ExecutionStep(**item)
        for item in data.pop(
            "execution_steps",
            [],
        )

    ]

    witness = ExecutionWitness(

        execution_steps=(
            execution_steps
        ),

        **data,
    )

    witness.validate()

    return witness


# ============================================================
# REPLAY EQUIVALENCE
# ============================================================

def execution_replay_equivalent(
    left: ExecutionWitness,
    right: ExecutionWitness,
) -> bool:

    left.validate()
    right.validate()

    comparable_fields = (

        "execution_hash",
        "execution_trace_hash",
        "mutation_trace_hash",
        "transcript_hash",
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
class ExecutionWitnessBundle:

    witnesses: List[
        ExecutionWitness
    ]

    bundle_hash: str

    deterministic: bool

    replay_safe: bool

    closed_world_aligned: bool

    generated_at: str

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise ExecutionDeterminismError(
                "bundle is not deterministic"
            )

        if not self.replay_safe:

            raise ExecutionWitnessValidationError(
                "bundle is not replay safe"
            )

        if not self.closed_world_aligned:

            raise ExecutionWitnessValidationError(
                "bundle violates closed-world "
                "alignment"
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

            "closed_world_aligned":
                self.closed_world_aligned,

            "generated_at":
                self.generated_at,
        }


def create_execution_bundle(
    witnesses: List[
        ExecutionWitness
    ],
) -> ExecutionWitnessBundle:

    for witness in witnesses:

        witness.validate()

    bundle_hash = deterministic_hash(

        [
            witness.witness_hash()
            for witness in witnesses
        ]
    )

    bundle = ExecutionWitnessBundle(

        witnesses=witnesses,

        bundle_hash=bundle_hash,

        deterministic=True,

        replay_safe=True,

        closed_world_aligned=True,

        generated_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    bundle.validate()

    return bundle
# ============================================================
# ✅ PHASE 0 COMPATIBILITY WITNESS
# ============================================================

def generate_witness(
    trace,
):
    """
    Minimal Phase 0 witness wrapper.

    Preserves compatibility with the
    constitutional witness system.
    """

    required = {
        "surface",
        "hash",
    }

    missing = required.difference(trace)

    if missing:
        raise ExecutionWitnessValidationError(
            "trace missing required witness fields"
        )

    step = ExecutionStep(
        step_order=0,
        execution_surface=(
            "afritech.core.runtime.replay"
        ),
        operation_type="phase0_execution",
        operation_hash=trace["hash"],
        deterministic=True,
        replay_safe=True,
        invariant_preserving=True,
        metadata={},
    )

    witness = create_execution_witness(
        execution_trace_hash=trace["hash"],
        mutation_trace_hash=trace["hash"],
        transcript_hash=trace["hash"],
        replay_hash=trace["hash"],
        receipt_hash=trace["hash"],
        registry_hash=trace["hash"],
        invariant_hash=trace["hash"],
        execution_surface=(
            "afritech.core.runtime.replay"
        ),
        epoch_id="phase0",
        execution_steps=[step],
        metadata={
            "phase": 0,
            "compatibility_mode": True,
        },
    )

    return witness.to_dict()