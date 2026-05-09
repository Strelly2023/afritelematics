"""
afritech/zk/groth16_verifier.py

Gro using Groth16 (snarkjs backend).Groth16 Verifier

Responsibilities:
- Validate proof structure
- Ensure deterministic public input binding
- Call snarkjs verifier
- Enforce consensus-safe validation
"""

from __future__ import annotations

from typing import Dict, Any
import json
import subprocess
import tempfile
import os

from afritech.zk.interface import ZKVerifier, ZKProof, ZKError


# -----------------------------------------------------------------
# GROTH16 VERIFIER
# -----------------------------------------------------------------

class Groth16Verifier(ZKVerifier):
    """
    Groth16 verifier implementation using snarkjs
    """

    scheme = "groth16"

    def __init__(
        self,
        verification_key_path: str,
        snarkjs_path: str = "snarkjs",
    ):
        """
        :param verification_key_path: path to verification key (.json)
        :param snarkjs_path: path to snarkjs binary
        """

        self.verification_key_path = verification_key_path
        self.snarkjs_path = snarkjs_path

        if not os.path.exists(self.verification_key_path):
            raise ZKError(f"missing_verification_key: {verification_key_path}")

    # -----------------------------------------------------------------
    # VERIFY
    # -----------------------------------------------------------------

    def verify(self, proof: ZKProof) -> bool:
        """
        Main verification entrypoint
        """

        # ---------------------------------------------------------
        # STRUCTURAL VALIDATION
        # ---------------------------------------------------------
        if not isinstance(proof, ZKProof):
            raise ZKError("invalid_proof_object")

        if not proof.verify():
            raise ZKError("invalid_proof_structure")

        if proof.scheme != self.scheme:
            raise ZKError(f"scheme_mismatch: expected {self.scheme}")

        # ---------------------------------------------------------
        # RUN SNARKJS VERIFICATION
        # ---------------------------------------------------------
        try:
            result = self._run_groth16_verify(proof)
        except subprocess.CalledProcessError as e:
            raise ZKError(f"snarkjs_verify_failed: {str(e)}")

        if not isinstance(result, bool):
            raise ZKError("invalid_verifier_output")

        return result

    # -----------------------------------------------------------------
    # INTERNAL: CALL SNARKJS
    # -----------------------------------------------------------------

    def _run_groth16_verify(self, proof: ZKProof) -> bool:

        with tempfile.TemporaryDirectory() as tmpdir:

            proof_file = os.path.join(tmpdir, "proof.json")
            public_file = os.path.join(tmpdir, "public.json")

            # -----------------------------------------------------
            # PARSE PROOF JSON
            # -----------------------------------------------------
            try:
                proof_json = json.loads(proof.proof.decode())
            except Exception:
                raise ZKError("invalid_proof_encoding")

            # -----------------------------------------------------
            # WRITE TEMP FILES
            # -----------------------------------------------------
            with open(proof_file, "w") as f:
                json.dump(proof_json, f)

            # public inputs must be ordered list for snarkjs
            public_inputs_list = self._public_inputs_to_list(proof.public_inputs)

            with open(public_file, "w") as f:
                json.dump(public_inputs_list, f)

            # -----------------------------------------------------
            # EXECUTE VERIFICATION
            # -----------------------------------------------------
            cmd = [
                self.snarkjs_path,
                "groth16",
                "verify",
                self.verification_key_path,
                public_file,
                proof_file,
            ]

            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # -----------------------------------------------------
            # INTERPRET RESULT
            # -----------------------------------------------------
            if completed.returncode != 0:
                raise subprocess.CalledProcessError(
                    completed.returncode,
                    cmd,
                    completed.stdout,
                    completed.stderr
                )

            output = completed.stdout.lower()

            # snarkjs returns "OK!" or similar
            if "ok" in output:
                return True

            return False

    # -----------------------------------------------------------------
    # PUBLIC INPUT CONVERSION
    # -----------------------------------------------------------------

    def _public_inputs_to_list(self, public_inputs: Dict[str, Any]):
        """
        Convert canonical dict → ordered list for snarkjs

        IMPORTANT:
        Order MUST match circuit declaration order
        """

        # enforce deterministic key ordering
        keys = sorted(public_inputs.keys())

        values = []

        for k in keys:
            v = public_inputs[k]

            # convert hex strings or hashes to integers if needed
            if isinstance(v, str):
                try:
                    values.append(int(v, 16))
                except ValueError:
                    # fallback: hash string
                    values.append(self._string_to_field(v))
            else:
                values.append(v)

        return values

    # -----------------------------------------------------------------
    # STRING → FIELD
    # -----------------------------------------------------------------

    def _string_to_field(self, value: str) -> int:
        """
        Convert arbitrary string into field element
        """
        return int.from_bytes(value.encode(), "big") % (2**254 - 1)