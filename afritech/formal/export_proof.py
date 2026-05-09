# afritech/formal/export_proof.py

"""
Bridge: Lean → Runtime

Responsible for:
- invoking Lean
- extracting proof data
- emitting JSON proof certificate
"""

import json
import hashlib


def compute_proof_hash(theorem, input_hash, output_hash):
    base = {
        "theorem": theorem,
        "input_hash": input_hash,
        "output_hash": output_hash,
    }

    return hashlib.sha256(
        json.dumps(base, sort_keys=True).encode()
    ).hexdigest()


def export_proof(theorem, input_data, output_data):
    input_hash = hashlib.sha256(
        json.dumps(input_data, sort_keys=True).encode()
    ).hexdigest()

    output_hash = hashlib.sha256(
        json.dumps(output_data, sort_keys=True).encode()
    ).hexdigest()

    proof_hash = compute_proof_hash(theorem, input_hash, output_hash)

    return {
        "schema": "afritech.proof.certificate.v1",
        "theorem": theorem,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "proof_hash": proof_hash,
    }


def save_proof(file_path, proof):
    with open(file_path, "w") as f:
        json.dump(proof, f, indent=2, sort_keys=True)