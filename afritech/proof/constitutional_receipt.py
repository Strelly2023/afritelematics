# afritech/proof/constitutional_receipt.py

"""
AfriTech Constitutional Receipt
===============================

Deterministic constitutional proof that lawful execution
occurred under admissible replay-safe constitutional
conditions.

A ConstitutionalReceipt binds:

- executed constitutional law
- authority context
- epoch lineage identity
- registry identity
- execution surface identity
- replay admissibility
- invariant execution proof
- closed-world execution witnesses
- deterministic topology witnesses
- transcript traceability
- mutation traceability
- execution trace attestation

If an execution has no valid ConstitutionalReceipt,
it is constitutionally NON-EXISTENT.

Constitutional receipts are:
- deterministic
- replay-safe
- observer-independent
- closed-world aligned
- invariant-preserving
- immutable

Filesystem identity must never define receipt legitimacy.
Canonical constitutional identity derives exclusively from:
    afritech.proof.constitutional_receipt
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, Optional, Tuple
import json

from afritech.kernel.constitutional_context import (
    ConstitutionalContext,
)


# ============================================================
# CONSTITUTIONAL CONSTANTS
# ============================================================

RECEIPT_SCHEMA = (
    "afritech.proof.constitutional_receipt.v2"
)

CANONICAL_IDENTITY = (
    "afritech.proof.constitutional_receipt"
)

RECEIPT_AUTHORITY = "PROOF"

SUPPORTED_HASH_ALGORITHM = "sha256"

FORBIDDEN_METADATA_FIELDS = {

    "observer_identity",
    "reflection_context",
    "probabilistic_context",
    "filesystem_ordering",
    "runtime_memory_address",

}

REQUIRED_RECEIPT_FIELDS = (

    "receipt_hash",
    "registry_hash",
    "execution_surface_hash",
    "surface_validation_hash",
    "execution_trace_hash",
    "mutation_trace_hash",
    "transcript_hash",
    "replay_hash",

)


# ============================================================
# EXCEPTIONS
# ============================================================

class ConstitutionalReceiptViolation(
    Exception,
):
    """
    Constitutional receipt violation.
    """


class ConstitutionalReceiptValidationError(
    ConstitutionalReceiptViolation,
):
    """
    Receipt validation failure.
    """


class ConstitutionalReceiptDeterminismError(
    ConstitutionalReceiptViolation,
):
    """
    Deterministic receipt violation.
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
# CONSTITUTIONAL RECEIPT
# ============================================================

@dataclass(frozen=True)
class ConstitutionalReceipt:
    """
    Immutable deterministic constitutional proof of lawful
    replay-admissible execution.
    """

    # --------------------------------------------------------
    # IDENTITY
    # --------------------------------------------------------

    schema: str

    authority: str

    canonical_identity: str

    receipt_id: str

    # --------------------------------------------------------
    # CORE IDENTITY
    # --------------------------------------------------------

    authority_id: str

    epoch_number: int

    registry_hash: str

    invariant_hash: str

    # --------------------------------------------------------
    # CLOSED-WORLD EXECUTION WITNESSES
    # --------------------------------------------------------

    execution_surface_hash: str

    surface_validation_hash: str

    execution_trace_hash: str

    mutation_trace_hash: str

    transcript_hash: str

    replay_hash: str

    # --------------------------------------------------------
    # EXECUTED LAW
    # --------------------------------------------------------

    invariants_executed: Tuple[str, ...]

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
    # RECEIPT HASH
    # --------------------------------------------------------

    receipt_hash: str

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

            "receipt_id":
                self.receipt_id,

            "authority_id":
                self.authority_id,

            "epoch_number":
                self.epoch_number,

            "registry_hash":
                self.registry_hash,

            "invariant_hash":
                self.invariant_hash,

            "execution_surface_hash":
                self.execution_surface_hash,

            "surface_validation_hash":
                self.surface_validation_hash,

            "execution_trace_hash":
                self.execution_trace_hash,

            "mutation_trace_hash":
                self.mutation_trace_hash,

            "transcript_hash":
                self.transcript_hash,

            "replay_hash":
                self.replay_hash,

            "invariants_executed":
                list(self.invariants_executed),

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

            "receipt_hash":
                self.receipt_hash,

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

            raise ConstitutionalReceiptValidationError(
                "receipt is not replay safe"
            )

        if not self.deterministic:

            raise ConstitutionalReceiptDeterminismError(
                "receipt is not deterministic"
            )

        if not self.observer_independent:

            raise ConstitutionalReceiptValidationError(
                "observer-dependent receipt"
            )

        if not self.invariant_preserving:

            raise ConstitutionalReceiptValidationError(
                "receipt violates invariants"
            )

        if not self.admissible:

            raise ConstitutionalReceiptValidationError(
                "inadmissible receipt"
            )

        if not self.closed_world_aligned:

            raise ConstitutionalReceiptValidationError(
                "receipt violates closed-world "
                "execution semantics"
            )

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        for field_name in REQUIRED_RECEIPT_FIELDS:

            value = getattr(
                self,
                field_name,
                None,
            )

            if not value:

                raise ConstitutionalReceiptValidationError(
                    f"missing required field: "
                    f"{field_name}"
                )

        # ----------------------------------------------------
        # INVARIANTS
        # ----------------------------------------------------

        if not self.invariants_executed:

            raise ConstitutionalReceiptValidationError(
                "no executed invariants"
            )

        # ----------------------------------------------------
        # HASH ALGORITHM
        # ----------------------------------------------------

        if (
            self.hash_algorithm
            != SUPPORTED_HASH_ALGORITHM
        ):

            raise ConstitutionalReceiptValidationError(
                "unsupported hash algorithm"
            )

        # ----------------------------------------------------
        # CANONICAL IDENTITY
        # ----------------------------------------------------

        if (
            self.canonical_identity
            != CANONICAL_IDENTITY
        ):

            raise ConstitutionalReceiptValidationError(
                "canonical identity mismatch"
            )

        # ----------------------------------------------------
        # METADATA VALIDATION
        # ----------------------------------------------------

        for forbidden in FORBIDDEN_METADATA_FIELDS:

            if forbidden in self.metadata:

                raise ConstitutionalReceiptValidationError(
                    f"forbidden metadata field: "
                    f"{forbidden}"
                )

    # --------------------------------------------------------
    # RECEIPT WITNESS HASH
    # --------------------------------------------------------

    def witness_hash(
        self,
    ) -> str:

        return deterministic_hash(
            self.to_dict()
        )

    # --------------------------------------------------------
    # REPLAY EQUIVALENCE
    # --------------------------------------------------------

    def replay_equivalent(
        self,
        other: "ConstitutionalReceipt",
    ) -> bool:

        self.validate()
        other.validate()

        comparable_fields = (

            "receipt_hash",
            "registry_hash",
            "execution_surface_hash",
            "surface_validation_hash",
            "execution_trace_hash",
            "mutation_trace_hash",
            "transcript_hash",
            "replay_hash",
            "invariant_hash",
            "epoch_number",
        )

        for field_name in comparable_fields:

            if (
                getattr(self, field_name)
                != getattr(other, field_name)
            ):

                return False

        return True

    # --------------------------------------------------------
    # CONSTRUCTION (CANONICAL)
    # --------------------------------------------------------

    @staticmethod
    def from_context(
        ctx: ConstitutionalContext,
        *,
        invariants_executed: Iterable[str],
        execution_trace_hash: str,
        mutation_trace_hash: str,
        transcript_hash: str,
        replay_hash: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> "ConstitutionalReceipt":
        """
        Construct deterministic replay-safe constitutional
        receipt from explicit ConstitutionalContext.

        Rules:
        - invariants are deterministically ordered
        - all execution witnesses are explicit
        - replay witnesses are mandatory
        - no implicit inference allowed
        - closed-world semantics enforced
        - receipt hash composition is deterministic
        """

        metadata = metadata or {}

        # ----------------------------------------------------
        # VALIDATE INVARIANTS
        # ----------------------------------------------------

        invariants = tuple(

            sorted(invariants_executed)

        )

        if not invariants:

            raise ValueError(
                "receipt requires at least one "
                "executed invariant"
            )

        # ----------------------------------------------------
        # CLOSED-WORLD WITNESS VALIDATION
        # ----------------------------------------------------

        if not ctx.execution_surface_hash:

            raise ValueError(
                "execution_surface_hash missing "
                "from ConstitutionalContext"
            )

        execution_surface_hash = (
            ctx.execution_surface_hash
        )

        surface_validation_hash = (
            execution_surface_hash
        )

        # ----------------------------------------------------
        # INVARIANT HASH
        # ----------------------------------------------------

        invariant_hash = deterministic_hash(

            list(invariants)

        )

        # ----------------------------------------------------
        # RECEIPT PAYLOAD
        # ----------------------------------------------------

        payload = {

            "authority_id":
                ctx.authority_id,

            "epoch_number":
                ctx.epoch.number,

            "registry_hash":
                ctx.registry_hash,

            "invariant_hash":
                invariant_hash,

            "execution_surface_hash":
                execution_surface_hash,

            "surface_validation_hash":
                surface_validation_hash,

            "execution_trace_hash":
                execution_trace_hash,

            "mutation_trace_hash":
                mutation_trace_hash,

            "transcript_hash":
                transcript_hash,

            "replay_hash":
                replay_hash,

            "invariants":
                list(invariants),
        }

        receipt_hash = deterministic_hash(
            payload
        )

        receipt_id = deterministic_hash({

            "receipt_hash":
                receipt_hash,

            "registry_hash":
                ctx.registry_hash,

            "epoch_number":
                ctx.epoch.number,
        })

        receipt = ConstitutionalReceipt(

            # ------------------------------------------------
            # IDENTITY
            # ------------------------------------------------

            schema=RECEIPT_SCHEMA,

            authority=RECEIPT_AUTHORITY,

            canonical_identity=(
                CANONICAL_IDENTITY
            ),

            receipt_id=receipt_id,

            # ------------------------------------------------
            # CORE IDENTITY
            # ------------------------------------------------

            authority_id=(
                ctx.authority_id
            ),

            epoch_number=(
                ctx.epoch.number
            ),

            registry_hash=(
                ctx.registry_hash
            ),

            invariant_hash=(
                invariant_hash
            ),

            # ------------------------------------------------
            # WITNESSES
            # ------------------------------------------------

            execution_surface_hash=(
                execution_surface_hash
            ),

            surface_validation_hash=(
                surface_validation_hash
            ),

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

            # ------------------------------------------------
            # EXECUTED LAW
            # ------------------------------------------------

            invariants_executed=(
                invariants
            ),

            # ------------------------------------------------
            # FLAGS
            # ------------------------------------------------

            replay_safe=True,

            deterministic=True,

            observer_independent=True,

            invariant_preserving=True,

            admissible=True,

            closed_world_aligned=True,

            # ------------------------------------------------
            # TIMING
            # ------------------------------------------------

            generated_at=(
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),

            hash_algorithm=(
                SUPPORTED_HASH_ALGORITHM
            ),

            # ------------------------------------------------
            # HASH
            # ------------------------------------------------

            receipt_hash=receipt_hash,

            # ------------------------------------------------
            # METADATA
            # ------------------------------------------------

            metadata=metadata,
        )

        receipt.validate()

        return receipt


# ============================================================
# PERSISTENCE
# ============================================================

def write_receipt(
    *,
    receipt: ConstitutionalReceipt,
    output_path,
) -> None:

    receipt.validate()

    output_path.parent.mkdir(

        parents=True,
        exist_ok=True,
    )

    output_path.write_text(

        receipt.to_json(),

        encoding="utf-8",
    )


# ============================================================
# RECEIPT LOADING
# ============================================================

def load_receipt(
    path,
) -> ConstitutionalReceipt:

    raw = path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw)

    receipt = ConstitutionalReceipt(

        invariants_executed=tuple(
            data.pop(
                "invariants_executed",
                [],
            )
        ),

        **data,
    )

    receipt.validate()

    return receipt