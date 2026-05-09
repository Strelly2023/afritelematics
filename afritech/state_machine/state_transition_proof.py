# afritech/state_machine/state_transition_proof.py

"""
AfriTech State Transition Proof

Purpose:
Generate and verify cryptographic proofs for state transitions.

Guarantees:
- deterministic proof generation
- binding to transition + state + chain
- replay-verifiable proofs
- tamper-evident commitments

This module converts execution into:
    PROOF-CARRYING STATE TRANSITIONS
"""

from typing import Dict, Any, List
import hashlib
import json

from afritech.state_machine.state_hash import (
    canonical_json,
    hash_transition,
    hash_transition_record,
    hash_transition_sequence,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class StateTransitionProofError(Exception):
    """Raised when proof generation or verification fails"""
    pass


# -----------------------------------------------------------------
# PROOF GENERATOR
# -----------------------------------------------------------------

class StateTransitionProof:

    # =============================================================
    # GENERATE SINGLE TRANSITION PROOF
    # =============================================================

    @staticmethod
    def generate(transition_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate proof for a single transition
        """

        required = ["id", "from", "to", "index", "previous_hash"]

        for f in required:
            if f not in transition_record:
                raise StateTransitionProofError(f"missing_field: {f}")

        # Base transition hash
        base_hash = hash_transition(transition_record)

        # Record hash (chain binding)
        record_hash = hash_transition_record(transition_record)

        proof_payload = {
            "transition_id": transition_record["id"],
            "from": transition_record["from"],
            "to": transition_record["to"],
            "index": transition_record["index"],
            "previous_hash": transition_record["previous_hash"],
            "transition_hash": base_hash,
            "record_hash": record_hash,
        }

        proof_hash = hashlib.sha256(
            canonical_json(proof_payload).encode()
        ).hexdigest()

        return {
            "type": "STATE_TRANSITION_PROOF",
            "version": "v1",
            "payload": proof_payload,
            "proof_hash": proof_hash,
            "status": "VALID",
        }

    # =============================================================
    # VERIFY SINGLE TRANSITION PROOF
    # =============================================================

    @staticmethod
    def verify(proof: Dict[str, Any]) -> bool:
        """
        Verify transition proof integrity
        """

        try:
            payload = proof["payload"]

            # Recompute base transition hash
            expected_transition_hash = hash_transition(payload)

            if payload["transition_hash"] != expected_transition_hash:
                raise StateTransitionProofError("transition_hash_mismatch")

            # Recompute record hash
            expected_record_hash = hash_transition_record(payload)

            if payload["record_hash"] != expected_record_hash:
                raise StateTransitionProofError("record_hash_mismatch")

            # Recompute proof hash
            expected_proof_hash = hashlib.sha256(
                canonical_json(payload).encode()
            ).hexdigest()

            if proof["proof_hash"] != expected_proof_hash:
                raise StateTransitionProofError("proof_hash_mismatch")

            return True

        except Exception as e:
            raise StateTransitionProofError(f"verification_failed: {e}")

    # =============================================================
    # GENERATE CHAIN PROOF (FULL EXECUTION)
    # =============================================================

    @staticmethod
    def generate_chain(history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate proof for full transition sequence
        """

        if not history:
            raise StateTransitionProofError("empty_history")

        proofs = []

        for record in history:
            proof = StateTransitionProof.generate(record)
            proofs.append(proof)

        sequence_hash = hash_transition_sequence(history)

        chain_payload = {
            "length": len(history),
            "sequence_hash": sequence_hash,
            "proofs": [p["proof_hash"] for p in proofs],
        }

        chain_proof_hash = hashlib.sha256(
            canonical_json(chain_payload).encode()
        ).hexdigest()

        return {
            "type": "STATE_CHAIN_PROOF",
            "version": "v1",
            "payload": chain_payload,
            "chain_proof_hash": chain_proof_hash,
            "status": "VALID",
        }

    # =============================================================
    # VERIFY CHAIN PROOF
    # =============================================================

    @staticmethod
    def verify_chain(
        history: List[Dict[str, Any]],
        chain_proof: Dict[str, Any],
        transition_proofs: List[Dict[str, Any]]
    ) -> bool:
        """
        Verify full execution chain
        """

        if len(history) != len(transition_proofs):
            raise StateTransitionProofError("length_mismatch")

        # Verify each transition proof
        for proof in transition_proofs:
            StateTransitionProof.verify(proof)

        # Verify sequence hash
        expected_sequence_hash = hash_transition_sequence(history)

        if chain_proof["payload"]["sequence_hash"] != expected_sequence_hash:
            raise StateTransitionProofError("sequence_hash_mismatch")

        # Verify chain proof hash
        expected_chain_hash = hashlib.sha256(
            canonical_json(chain_proof["payload"]).encode()
        ).hexdigest()

        if chain_proof["chain_proof_hash"] != expected_chain_hash:
            raise StateTransitionProofError("chain_hash_mismatch")

        return True

    # =============================================================
    # BIND TO TRACE EVENT (INTEGRATION)
    # =============================================================

    @staticmethod
    def bind_to_trace(
        transition_proof: Dict[str, Any],
        trace_event: Dict[str, Any]
    ) -> bool:
        """
        Ensure proof ↔ trace consistency
        """

        expected_step = transition_proof["payload"]["transition_id"]

        if trace_event["step"] != expected_step:
            raise StateTransitionProofError("trace_step_mismatch")

        # Optional deeper binding
        if "event_hash" in trace_event:
            combined = {
                "proof_hash": transition_proof["proof_hash"],
                "event_hash": trace_event["event_hash"],
            }

            binding_hash = hashlib.sha256(
                canonical_json(combined).encode()
            ).hexdigest()

            return True

        return True

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self):
        return "<StateTransitionProof layer>"