# afritech/federation/federation_verifier.py

"""
AfriTech Federation Verifier

Purpose:
Validate execution across multiple independent AfriTech systems.

Enforces:
- inter-system consensus
- result hash agreement
- proof integrity
- optional signature presence
- deterministic verification

Failure → federated consensus failure → result invalid
"""

from typing import List, Dict, Any
from collections import defaultdict


class FederationError(Exception):
    """Raised when federated verification fails"""
    pass


class FederationVerifier:
    """
    Federated consensus verifier across systems.

    Guarantees:
    - deterministic multi-system agreement
    - quorum enforcement
    - cross-system consistency
    """

    def __init__(
        self,
        quorum_ratio: float = 0.67,
        min_systems: int = 3,
        require_proof_hash: bool = True,
        require_signature: bool = False,
    ):
        self.quorum_ratio = quorum_ratio
        self.min_systems = min_systems
        self.require_proof_hash = require_proof_hash
        self.require_signature = require_signature

    # -----------------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # -----------------------------------------------------------------

    def verify(self, system_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        system_results format:

        [
            {
                "system_id": "SYS_A",
                "context_hash": "...",
                "result_hash": "...",
                "proof_hash": "...",
                "signature": "..."
            }
        ]
        """

        self._validate_structure(system_results)
        self._validate_min_systems(system_results)
        self._validate_context_consistency(system_results)

        # -------------------------------------------------------------
        # CONSENSUS ON RESULT HASH
        # -------------------------------------------------------------
        result_consensus = self._compute_consensus(system_results, "result_hash")

        # -------------------------------------------------------------
        # OPTIONAL PROOF HASH VALIDATION
        # -------------------------------------------------------------
        if self.require_proof_hash:
            proof_consensus = self._compute_consensus(system_results, "proof_hash")

            if proof_consensus["value"] != result_consensus["value"]:
                raise FederationError("proof_result_mismatch")

        # -------------------------------------------------------------
        # SIGNATURE VALIDATION (STRUCTURAL)
        # -------------------------------------------------------------
        if self.require_signature:
            self._validate_signatures(system_results)

        # -------------------------------------------------------------
        # QUORUM CHECK
        # -------------------------------------------------------------
        self._validate_quorum(result_consensus)

        # -------------------------------------------------------------
        # BUILD FEDERATED PROOF
        # -------------------------------------------------------------
        return self._build_proof(system_results, result_consensus)

    # -----------------------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------------------

    def _validate_structure(self, system_results: List[Dict[str, Any]]):
        if not isinstance(system_results, list) or not system_results:
            raise FederationError("invalid_system_result_structure")

        required_fields = [
            "system_id",
            "context_hash",
            "result_hash",
        ]

        if self.require_proof_hash:
            required_fields.append("proof_hash")

        for system in system_results:
            for field in required_fields:
                if field not in system:
                    raise FederationError(f"missing_field: {field}")

    def _validate_min_systems(self, system_results):
        if len(system_results) < self.min_systems:
            raise FederationError("insufficient_systems")

    def _validate_context_consistency(self, system_results):
        context_hashes = {s["context_hash"] for s in system_results}

        if len(context_hashes) != 1:
            raise FederationError("context_mismatch")

    def _validate_signatures(self, system_results):
        for system in system_results:
            if not system.get("signature"):
                raise FederationError(
                    f"missing_signature: {system['system_id']}"
                )

    # -----------------------------------------------------------------
    # CONSENSUS
    # -----------------------------------------------------------------

    def _compute_consensus(self, results, key: str) -> Dict[str, Any]:
        counts = defaultdict(int)

        for r in results:
            counts[r[key]] += 1

        best_value = None
        best_count = 0

        for value, count in counts.items():
            if count > best_count:
                best_value = value
                best_count = count

        total = len(results)
        ratio = best_count / total

        return {
            "value": best_value,
            "count": best_count,
            "total": total,
            "ratio": ratio,
        }

    # -----------------------------------------------------------------
    # QUORUM
    # -----------------------------------------------------------------

    def _validate_quorum(self, consensus: Dict[str, Any]):
        if consensus["ratio"] < self.quorum_ratio:
            raise FederationError(
                f"federated_quorum_failed: {consensus['ratio']} < {self.quorum_ratio}"
            )

    # -----------------------------------------------------------------
    # PROOF GENERATION
    # -----------------------------------------------------------------

    def _build_proof(
        self,
        system_results: List[Dict[str, Any]],
        consensus: Dict[str, Any],
    ) -> Dict[str, Any]:

        proof = {
            "proof_type": "FEDERATED_EXECUTION_PROOF",
            "context_hash": system_results[0]["context_hash"],
            "final_result_hash": consensus["value"],
            "agreement_ratio": consensus["ratio"],
            "consensus_achieved": True,
            "system_count": consensus["total"],
            "agreeing_systems": [],
            "disagreeing_systems": [],
            "systems": [],
        }

        for system in system_results:

            is_agree = system["result_hash"] == consensus["value"]

            enriched = {
                "system_id": system["system_id"],
                "result_hash": system["result_hash"],
                "proof_hash": system.get("proof_hash"),
                "signature": system.get("signature"),
                "agrees": is_agree,
            }

            proof["systems"].append(enriched)

            if is_agree:
                proof["agreeing_systems"].append(system["system_id"])
            else:
                proof["disagreeing_systems"].append(system["system_id"])

        return proof
