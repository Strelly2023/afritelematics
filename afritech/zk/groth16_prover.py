"""
afritech/zk/groth16_prover.py

Groth16 Prover
==============

Generates zk-SNARK proofs using Groth16 (snarkjs backend).

Responsibilities:
- Prepare deterministic witness inputs
- Call external prover (snarkjs or compatible)
- Construct ZKProof object
- Ensure canonical public inputs

NOTE:
Requires compiled circuit + proving key:
- circuit.wasm
- circuit.zkey
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import json
import hashlib
import subprocess
import tempfile
import os

from afritech.zk.interface import ZKProver, ZKProof, ZKError


# -----------------------------------------------------------------
# GROTH16 PROVER
# -----------------------------------------------------------------

class Groth16Prover(ZKProver):
    """
    Groth16 prover implementation using snarkjs
    """

    scheme = "groth16"

    def __init__(
        self,
        wasm_path: str,
        zkey_path: str,
        snarkjs_path: str = "snarkjs",
    ):
        """
        :param wasm_path: compiled circuit wasm file
        :param zkey_path: proving key (.zkey)
        :param snarkjs_path: path to snarkjs binary
        """

        self.wasm_path = wasm_path
        self.zkey_path = zkey_path
        self.snarkjs_path = snarkjs_path

        if not os.path.exists(self.wasm_path):
            raise ZKError(f"missing_wasm: {wasm_path}")

        if not os.path.exists(self.zkey_path):
            raise ZKError(f"missing_zkey: {zkey_path}")

    # -----------------------------------------------------------------
    # MAIN PROVE METHOD
    # -----------------------------------------------------------------

    def prove(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ) -> ZKProof:

        # ---------------------------------------------------------
        # 1. BUILD PUBLIC INPUTS (CANONICAL)
        # ---------------------------------------------------------

        public_inputs = self.build_public_inputs(input_data, output_data)

        # ---------------------------------------------------------
        # 2. BUILD WITNESS INPUT (CIRCUIT INPUT JSON)
        # ---------------------------------------------------------

        witness_input = self._build_witness(input_data, output_data)

        # ---------------------------------------------------------
        # 3. GENERATE PROOF USING SNARKJS
        # ---------------------------------------------------------

        proof_bytes, public = self._run_groth16_prover(witness_input)

        # ---------------------------------------------------------
        # 4. CONSISTENCY CHECK (CRITICAL)
        # ---------------------------------------------------------

        # enforce that public inputs match circuit outputs
        canonical_public = self._canonical(public)

        expected_public = self._canonical(public_inputs)

        if self._public_inputs_mismatch(canonical_public, expected_public):
            raise ZKError("public_inputs_mismatch")

        # ---------------------------------------------------------
        # 5. BUILD ZKPROOF
        # ---------------------------------------------------------

        return ZKProof(
            proof=proof_bytes,
            public_inputs=expected_public,
            scheme=self.scheme,
            metadata={
                "backend": "groth16",
                "circuit": os.path.basename(self.wasm_path),
            },
        )

    # -----------------------------------------------------------------
    # WITNESS BUILDING
    # -----------------------------------------------------------------

    def _build_witness(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Converts runtime data into circuit-compatible witness
        """

        return {
            "payload": self._encode_payload(input_data.get("payload", {})),
            "payload_hash": self._hash(input_data.get("payload", {})),
            "result": self._encode_result(output_data),
            "result_hash": self._hash(output_data),
            "authority_id": self._hash(input_data.get("authority_profile")),
            "transcript_hash": self._hash(
                input_data.get("replay_requirements", {})
            ),
            "circuit_version": 1,
        }

    # -----------------------------------------------------------------
    # CALL SNARKJS
    # -----------------------------------------------------------------

    def _run_groth16_prover(self, witness: Dict[str, Any]):

        with tempfile.TemporaryDirectory() as tmpdir:

            input_file = os.path.join(tmpdir, "input.json")
            proof_file = os.path.join(tmpdir, "proof.json")
            public_file = os.path.join(tmpdir, "public.json")

            # write input
            with open(input_file, "w") as f:
                json.dump(witness, f)

            # call snarkjs
            cmd = [
                self.snarkjs_path,
                "groth16",
                "fullprove",
                input_file,
                self.wasm_path,
                self.zkey_path,
                proof_file,
                public_file,
            ]

            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                raise ZKError(f"snarkjs_failed: {str(e)}")

            # load outputs
            with open(proof_file) as f:
                proof_json = json.load(f)

            with open(public_file) as f:
                public_json = json.load(f)

            proof_bytes = json.dumps(proof_json).encode()

            return proof_bytes, public_json

    # -----------------------------------------------------------------
    # ENCODERS
    # -----------------------------------------------------------------

    def _encode_payload(self, payload: Dict[str, Any]):
        """
        Convert payload to list of field elements
        """
        encoded = json.dumps(payload, sort_keys=True)
        return [int.from_bytes(encoded.encode(), "big") % (2**254 - 1)]

    def _encode_result(self, output: Dict[str, Any]):
        encoded = json.dumps(output, sort_keys=True)
        return int.from_bytes(encoded.encode(), "big") % (2**254 - 1)

    # -----------------------------------------------------------------
    # UTILS
    # -----------------------------------------------------------------

    def _hash(self, data: Any) -> str:
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def _canonical(self, data):
        return json.loads(json.dumps(data, sort_keys=True))

    def _public_inputs_mismatch(self, a, b):
        return json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True)
