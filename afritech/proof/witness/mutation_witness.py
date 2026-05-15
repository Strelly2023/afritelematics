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
    "afritech.proof.witness.mutation_witness.v1"
)

CANONICAL_IDENTITY = (
    "afritech.proof.witness.mutation_witness"
)

WITNESS_AUTHORITY = "PROOF"

SUPPORTED_HASH_ALGORITHM = "sha256"

AUTHORIZED_MUTATION_GATEWAYS = {

    "afritech.kernel.constitutional_gateway",

}

FORBIDDEN_MUTATION_FIELDS = {

    "observer_identity",
    "reflection_context",
    "probabilistic_context",
    "filesystem_ordering",
    "runtime_memory_address",

}

REQUIRED_MUTATION_FIELDS = (

    "mutation_hash",
    "parent_state_hash",
    "result_state_hash",
    "mutation_trace_hash",
    "execution_trace_hash",

)


# ============================================================
# CONSTITUTIONAL IDENTITY
# ============================================================

CANONICAL_IDENTITY = (
    "afritech.proof.witness.mutation_witness"
)

IMPLEMENTATION_STATE = "PARTIAL"

REPLAY_ADMISSIBLE = True

DETERMINISTIC = True

PROOF_ADMISSIBLE = "CONDITIONAL"

RUNTIME_ADMISSIBLE = False

CLOSED_WORLD_ALIGNED = True

OBSERVER_INDEPENDENT = True

REPLAY_SAFE = True

WITNESS_TYPE = "MUTATION"

REPLAY_SIGNIFICANCE = "REQUIRED"

# ============================================================
# EXCEPTIONS
# ============================================================

class MutationWitnessViolation(
    Exception,
):
    """
    Constitutional mutation witness violation.
    """


class MutationWitnessValidationError(
    MutationWitnessViolation,
):
    """
    Mutation witness validation failure.
    """


class MutationDeterminismError(
    MutationWitnessViolation,
):
    """
    Deterministic mutation semantics failure.
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
# MUTATION RECORD
# ============================================================

@dataclass(frozen=True)
class MutationRecord:

    mutation_type: str

    mutation_order: int

    mutation_surface: str

    mutation_gateway: str

    mutation_payload_hash: str

    deterministic: bool

    replay_safe: bool

    invariant_preserving: bool

    metadata: Dict[str, Any]

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise MutationDeterminismError(
                "non-deterministic mutation record"
            )

        if not self.replay_safe:

            raise MutationWitnessValidationError(
                "mutation record is not replay safe"
            )

        if not self.invariant_preserving:

            raise MutationWitnessValidationError(
                "mutation violates invariants"
            )

        if (
            self.mutation_gateway
            not in AUTHORIZED_MUTATION_GATEWAYS
        ):

            raise MutationWitnessValidationError(
                "unauthorized mutation gateway"
            )

        for forbidden in FORBIDDEN_MUTATION_FIELDS:

            if forbidden in self.metadata:

                raise MutationWitnessValidationError(
                    f"forbidden mutation metadata: "
                    f"{forbidden}"
                )


# ============================================================
# MUTATION WITNESS
# ============================================================

@dataclass(frozen=True)
class MutationWitness:

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

    mutation_hash: str

    parent_state_hash: str

    result_state_hash: str

    mutation_trace_hash: str

    execution_trace_hash: str

    replay_hash: str

    receipt_hash: str

    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    execution_surface: str

    epoch_id: str

    registry_hash: str

    invariant_hash: str

    mutation_gateway: str

    # --------------------------------------------------------
    # MUTATION RECORDS
    # --------------------------------------------------------

    mutations: List[MutationRecord]

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

        result["mutations"] = [

            asdict(mutation)
            for mutation in self.mutations

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

        # ----------------------------------------------------
        # FLAGS
        # ----------------------------------------------------

        if not self.replay_safe:

            raise MutationWitnessValidationError(
                "mutation witness not replay safe"
            )

        if not self.deterministic:

            raise MutationDeterminismError(
                "mutation witness not deterministic"
            )

        if not self.observer_independent:

            raise MutationWitnessValidationError(
                "observer-dependent mutation witness"
            )

        if not self.invariant_preserving:

            raise MutationWitnessValidationError(
                "mutation witness violates invariants"
            )

        if not self.admissible:

            raise MutationWitnessValidationError(
                "inadmissible mutation witness"
            )

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        for field_name in REQUIRED_MUTATION_FIELDS:

            value = getattr(
                self,
                field_name,
                None,
            )

            if not value:

                raise MutationWitnessValidationError(
                    f"missing required field: "
                    f"{field_name}"
                )

        # ----------------------------------------------------
        # GATEWAY VALIDATION
        # ----------------------------------------------------

        if (
            self.mutation_gateway
            not in AUTHORIZED_MUTATION_GATEWAYS
        ):

            raise MutationWitnessValidationError(
                "unauthorized mutation gateway"
            )

        # ----------------------------------------------------
        # HASH ALGORITHM
        # ----------------------------------------------------

        if (
            self.hash_algorithm
            != SUPPORTED_HASH_ALGORITHM
        ):

            raise MutationWitnessValidationError(
                "unsupported hash algorithm"
            )

        # ----------------------------------------------------
        # CANONICAL IDENTITY
        # ----------------------------------------------------

        if (
            self.canonical_identity
            != CANONICAL_IDENTITY
        ):

            raise MutationWitnessValidationError(
                "canonical identity mismatch"
            )

        # ----------------------------------------------------
        # METADATA VALIDATION
        # ----------------------------------------------------

        for forbidden in FORBIDDEN_MUTATION_FIELDS:

            if forbidden in self.metadata:

                raise MutationWitnessValidationError(
                    f"forbidden metadata field: "
                    f"{forbidden}"
                )

        # ----------------------------------------------------
        # MUTATION VALIDATION
        # ----------------------------------------------------

        previous_order = -1

        for mutation in self.mutations:

            mutation.validate()

            if (
                mutation.mutation_order
                <= previous_order
            ):

                raise MutationDeterminismError(
                    "mutation ordering is not strictly "
                    "monotonic"
                )

            previous_order = (
                mutation.mutation_order
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

def create_mutation_witness(
    *,
    parent_state_hash: str,
    result_state_hash: str,
    execution_trace_hash: str,
    replay_hash: str,
    receipt_hash: str,
    execution_surface: str,
    epoch_id: str,
    registry_hash: str,
    invariant_hash: str,
    mutation_gateway: str,
    mutations: List[MutationRecord],
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> MutationWitness:

    metadata = metadata or {}

    # --------------------------------------------------------
    # VALIDATE MUTATIONS
    # --------------------------------------------------------

    for mutation in mutations:

        mutation.validate()

    # --------------------------------------------------------
    # MUTATION TRACE HASH
    # --------------------------------------------------------

    mutation_trace_hash = deterministic_hash(

        [
            asdict(mutation)
            for mutation in mutations
        ]
    )

    # --------------------------------------------------------
    # MUTATION HASH
    # --------------------------------------------------------

    mutation_hash = deterministic_hash({

        "parent_state_hash":
            parent_state_hash,

        "result_state_hash":
            result_state_hash,

        "mutation_trace_hash":
            mutation_trace_hash,

        "execution_trace_hash":
            execution_trace_hash,

        "execution_surface":
            execution_surface,

        "epoch_id":
            epoch_id,
    })

    # --------------------------------------------------------
    # WITNESS ID
    # --------------------------------------------------------

    witness_id = deterministic_hash({

        "mutation_hash":
            mutation_hash,

        "mutation_trace_hash":
            mutation_trace_hash,

        "execution_trace_hash":
            execution_trace_hash,

        "epoch_id":
            epoch_id,
    })

    witness = MutationWitness(

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

        mutation_hash=mutation_hash,

        parent_state_hash=parent_state_hash,

        result_state_hash=result_state_hash,

        mutation_trace_hash=mutation_trace_hash,

        execution_trace_hash=execution_trace_hash,

        replay_hash=replay_hash,

        receipt_hash=receipt_hash,

        # ----------------------------------------------------
        # EXECUTION
        # ----------------------------------------------------

        execution_surface=execution_surface,

        epoch_id=epoch_id,

        registry_hash=registry_hash,

        invariant_hash=invariant_hash,

        mutation_gateway=mutation_gateway,

        # ----------------------------------------------------
        # MUTATIONS
        # ----------------------------------------------------

        mutations=mutations,

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

def write_mutation_witness(
    *,
    witness: MutationWitness,
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


def load_mutation_witness(
    path: Path,
) -> MutationWitness:

    raw = path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw)

    mutations = [

        MutationRecord(**item)
        for item in data.pop("mutations", [])

    ]

    witness = MutationWitness(

        mutations=mutations,
        **data,
    )

    witness.validate()

    return witness


# ============================================================
# REPLAY EQUIVALENCE
# ============================================================

def mutation_replay_equivalent(
    left: MutationWitness,
    right: MutationWitness,
) -> bool:

    left.validate()
    right.validate()

    comparable_fields = (

        "mutation_hash",
        "mutation_trace_hash",
        "execution_trace_hash",
        "parent_state_hash",
        "result_state_hash",
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
class MutationWitnessBundle:

    witnesses: List[MutationWitness]

    bundle_hash: str

    deterministic: bool

    replay_safe: bool

    generated_at: str

    def validate(
        self,
    ) -> None:

        if not self.deterministic:

            raise MutationDeterminismError(
                "bundle is not deterministic"
            )

        if not self.replay_safe:

            raise MutationWitnessValidationError(
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


def create_mutation_bundle(
    witnesses: List[MutationWitness],
) -> MutationWitnessBundle:

    for witness in witnesses:

        witness.validate()

    bundle_hash = deterministic_hash(

        [
            witness.witness_hash()
            for witness in witnesses
        ]
    )

    bundle = MutationWitnessBundle(

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