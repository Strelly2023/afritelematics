from __future__ import annotations

from typing import Any

from afritech.shared.types import stable_hash


RECEIPT_SCHEMA = "afritech.receipt.v1"
TRANSCRIPT_SCHEMA = "afritech.transcript.v1"
MUTATION_TRACE_SCHEMA = "afritech.mutation_trace.v1"
SIGNATURE_ALGORITHM = "sha256-local-deterministic"
SIGNATURE_DOMAIN = "afritech.ga7.constitutional.receipt"


def chain_step(
    previous_hash: str,
    stage: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    step_payload = {
        "previous_hash": previous_hash,
        "stage": stage,
        "payload_hash": stable_hash(payload),
    }
    return {
        **step_payload,
        "step_hash": stable_hash(step_payload),
    }


def build_execution_chain(
    initial_payload: dict[str, Any],
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    current_hash = stable_hash(
        {
            "stage": "input",
            "payload": initial_payload,
        }
    )
    steps: list[dict[str, Any]] = []

    for entry in trace:
        stage = str(entry.get("stage", "unknown"))
        step = chain_step(current_hash, stage, entry)
        steps.append(step)
        current_hash = step["step_hash"]

    return {
        "initial_hash": stable_hash(initial_payload),
        "steps": steps,
        "execution_chain_hash": current_hash,
    }


def build_transcript(
    *,
    program_id: str | None,
    status: str,
    trace: list[dict[str, Any]],
    execution_chain: dict[str, Any],
) -> dict[str, Any]:
    transcript = {
        "schema": TRANSCRIPT_SCHEMA,
        "program_id": program_id,
        "status": status,
        "steps": trace,
        "hashes": [step["step_hash"] for step in execution_chain["steps"]],
        "execution_chain_hash": execution_chain["execution_chain_hash"],
    }
    return {
        **transcript,
        "transcript_hash": stable_hash(transcript),
    }


def build_mutation_trace(
    *,
    program_id: str | None,
    status: str,
    before_state_hash: str,
    after_state_hash: str,
) -> dict[str, Any]:
    transitions = [
        {
            "index": 0,
            "before_state_hash": before_state_hash,
            "operation": "semantic_admission",
            "program_id": program_id,
            "status": status,
            "after_state_hash": after_state_hash,
        }
    ]
    trace = {
        "schema": MUTATION_TRACE_SCHEMA,
        "transitions": transitions,
    }
    return {
        **trace,
        "mutation_trace_hash": stable_hash(trace),
    }


def sign_receipt_payload(payload: dict[str, Any]) -> str:
    return stable_hash(
        {
            "domain": SIGNATURE_DOMAIN,
            "payload": payload,
        }
    )


def receipt_inspection_hash(result: dict[str, Any]) -> str:
    return stable_hash(
        {
            "status": result.get("status"),
            "program_id": result.get("program_id"),
            "reason": result.get("reason"),
            "trace": result.get("trace", []),
            "proof": result.get("proof"),
        }
    )


def build_receipt(
    *,
    decision: str,
    program_id: str | None,
    normalized_expression_hash: str | None,
    proof_hash: str | None,
    execution_chain: dict[str, Any],
    transcript: dict[str, Any],
    mutation_trace: dict[str, Any],
    inspection_hash: str | None,
    epoch: int = 6,
) -> dict[str, Any]:
    receipt_payload = {
        "schema": RECEIPT_SCHEMA,
        "decision": decision,
        "program_id": program_id,
        "normalized_expression_hash": normalized_expression_hash,
        "proof_hash": proof_hash,
        "execution_chain_hash": execution_chain["execution_chain_hash"],
        "transcript_hash": transcript["transcript_hash"],
        "mutation_trace_hash": mutation_trace["mutation_trace_hash"],
        "inspection_hash": inspection_hash,
        "epoch": epoch,
        "replay_binding": stable_hash(
            {
                "program_id": program_id,
                "decision": decision,
                "transcript_hash": transcript["transcript_hash"],
                "execution_chain_hash": execution_chain["execution_chain_hash"],
                "mutation_trace_hash": mutation_trace["mutation_trace_hash"],
            }
        ),
        "signature_algorithm": SIGNATURE_ALGORITHM,
    }
    receipt_hash = stable_hash(receipt_payload)
    signature = sign_receipt_payload(receipt_payload)
    return {
        **receipt_payload,
        "receipt_hash": receipt_hash,
        "signature": signature,
    }


def attach_receipt(
    result: dict[str, Any],
    *,
    initial_payload: dict[str, Any],
    inspection_hash: str | None,
    epoch: int = 6,
) -> dict[str, Any]:
    proof = result.get("proof") or {}
    trace = result.get("trace", [])
    status = str(result.get("status"))
    program_id = result.get("program_id")

    execution_chain = build_execution_chain(initial_payload, trace)
    transcript = build_transcript(
        program_id=program_id,
        status=status,
        trace=trace,
        execution_chain=execution_chain,
    )
    before_state_hash = stable_hash(
        {
            "program_id": program_id,
            "input": initial_payload,
        }
    )
    after_state_hash = stable_hash(
        {
            "program_id": program_id,
            "status": status,
            "proof_hash": proof.get("proof_hash"),
            "transcript_hash": transcript["transcript_hash"],
        }
    )
    mutation_trace = build_mutation_trace(
        program_id=program_id,
        status=status,
        before_state_hash=before_state_hash,
        after_state_hash=after_state_hash,
    )
    receipt = build_receipt(
        decision=status,
        program_id=program_id,
        normalized_expression_hash=proof.get("normalized_expression_hash"),
        proof_hash=proof.get("proof_hash"),
        execution_chain=execution_chain,
        transcript=transcript,
        mutation_trace=mutation_trace,
        inspection_hash=inspection_hash,
        epoch=epoch,
    )

    return {
        **result,
        "input_contract": initial_payload.get("contract"),
        "input_truth_values": initial_payload.get("truth_values"),
        "execution_chain": execution_chain,
        "transcript": transcript,
        "mutation_trace": mutation_trace,
        "receipt": receipt,
    }


def verify_receipt_bundle(bundle: dict[str, Any]) -> bool:
    receipt = bundle.get("receipt")
    transcript = bundle.get("transcript")
    mutation_trace = bundle.get("mutation_trace")
    execution_chain = bundle.get("execution_chain")

    if not all(isinstance(item, dict) for item in (receipt, transcript, mutation_trace, execution_chain)):
        return False

    rebuilt_chain = build_execution_chain(
        {
            "contract": bundle.get("input_contract"),
            "truth_values": bundle.get("input_truth_values"),
        },
        transcript.get("steps", []),
    )
    if rebuilt_chain.get("execution_chain_hash") != execution_chain.get("execution_chain_hash"):
        return False
    if rebuilt_chain.get("steps") != execution_chain.get("steps"):
        return False

    if transcript.get("transcript_hash") != stable_hash(
        {
            "schema": transcript.get("schema"),
            "program_id": transcript.get("program_id"),
            "status": transcript.get("status"),
            "steps": transcript.get("steps"),
            "hashes": transcript.get("hashes"),
            "execution_chain_hash": transcript.get("execution_chain_hash"),
        }
    ):
        return False

    if mutation_trace.get("mutation_trace_hash") != stable_hash(
        {
            "schema": mutation_trace.get("schema"),
            "transitions": mutation_trace.get("transitions"),
        }
    ):
        return False

    if receipt.get("execution_chain_hash") != execution_chain.get("execution_chain_hash"):
        return False
    if receipt.get("transcript_hash") != transcript.get("transcript_hash"):
        return False
    if receipt.get("mutation_trace_hash") != mutation_trace.get("mutation_trace_hash"):
        return False

    payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"receipt_hash", "signature"}
    }
    if receipt.get("receipt_hash") != stable_hash(payload):
        return False
    if receipt.get("signature") != sign_receipt_payload(payload):
        return False

    return True


def reconstruct_receipt_bundle(
    *,
    contract: dict[str, Any],
    truth_values: dict[str, bool],
    result: dict[str, Any],
    inspection_hash: str | None,
    epoch: int = 6,
) -> dict[str, Any]:
    base = {
        key: value
        for key, value in result.items()
        if key not in {
            "execution_chain",
            "transcript",
            "mutation_trace",
            "receipt",
            "input_contract",
            "input_truth_values",
        }
    }
    rebuilt = attach_receipt(
        base,
        initial_payload={
            "contract": contract,
            "truth_values": truth_values,
        },
        inspection_hash=inspection_hash,
        epoch=epoch,
    )
    return {
        **rebuilt,
        "input_contract": contract,
        "input_truth_values": truth_values,
    }
