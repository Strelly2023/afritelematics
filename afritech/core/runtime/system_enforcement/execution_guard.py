from pathlib import Path
from typing import Any

import yaml

from afritech.semantic_engine.evaluator.evaluator import evaluate
from afritech.semantic_engine.ir.hasher import canonical_json, hash_expression
from afritech.semantic_engine.ir.schema import SemanticProgram, SystemInvalid
from afritech.semantic_engine.optimizer.normalizer import normalize
from afritech.semantic_engine.parser.ir_builder import compile_semantic_yaml
from afritech.semantic_engine.proof.proof_builder import build_proof, validate_proof
from afritech.semantic_engine.satisfiability.solver import admissible
from afritech.core.runtime.receipts import attach_receipt, receipt_inspection_hash


def load_contract_payload(source: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(source, dict):
        return source

    path = Path(source)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemInvalid("semantic_yaml_must_be_mapping")
    return payload


def truth_values_from_payload(payload: dict[str, Any]) -> dict[str, bool]:
    truth_values = payload.get("truth_values", {})
    if not isinstance(truth_values, dict):
        raise SystemInvalid("truth_values_must_be_mapping")
    return {str(symbol): bool(value) for symbol, value in truth_values.items()}


def enforce_execution(
    program: SemanticProgram,
    truth_values: dict[str, bool],
) -> tuple[bool, dict]:
    result, proof, normalized = admissible(
        program.expression,
        truth_values,
        program.declared_symbols,
    )

    if not result:
        raise SystemInvalid("execution_not_admissible")

    expected_hash = hash_expression(normalized)

    if proof["normalized_expression_hash"] != expected_hash:
        raise SystemInvalid("hash_mismatch")

    validate_proof(proof, normalized)

    return True, proof


def admit_semantic_yaml(source, truth_values: dict[str, bool]) -> tuple[bool, dict]:
    return enforce_execution(compile_semantic_yaml(source), truth_values)


def admit_contract(
    source: str | Path | dict[str, Any],
    truth_values: dict[str, bool] | None = None,
) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    initial_payload: dict[str, Any] = {
        "contract": None,
        "truth_values": truth_values,
    }

    try:
        payload = load_contract_payload(source)
        if truth_values is None:
            truth_values = truth_values_from_payload(payload)
        initial_payload = {
            "contract": payload,
            "truth_values": truth_values,
        }

        program = compile_semantic_yaml(payload)
        trace.append(
            {
                "stage": "compile",
                "program_id": program.id,
                "declared_symbols": sorted(program.declared_symbols),
                "output": "s_ir",
            }
        )

        normalized = normalize(program.expression)
        trace.append(
            {
                "stage": "normalize",
                "canonical_expression": canonical_json(normalized),
                "output": "normalized_s_ir",
            }
        )

        normalized_hash = hash_expression(normalized)
        trace.append(
            {
                "stage": "hash",
                "normalized_expression_hash": normalized_hash,
            }
        )

        evaluated = evaluate(normalized, truth_values, program.declared_symbols)
        trace.append(
            {
                "stage": "evaluate",
                "result": bool(evaluated),
            }
        )

        proof = build_proof(normalized, evaluated)
        validate_proof(proof, normalized)
        trace.append(
            {
                "stage": "proof",
                "proof_hash": proof["proof_hash"],
                "normalized_expression_hash": proof["normalized_expression_hash"],
            }
        )

        decision = "ADMIT" if evaluated else "DENY"
        reason = None if evaluated else "execution_not_admissible"

        trace.append(
            {
                "stage": "admission_gate",
                "decision": decision,
                **({"reason": reason} if reason else {}),
            }
        )

        result = {
            "status": decision,
            "program_id": program.id,
            "proof": proof,
            "trace": trace,
        }
        if reason:
            result["reason"] = reason
        return attach_receipt(
            result,
            initial_payload=initial_payload,
            inspection_hash=receipt_inspection_hash(result),
        )

    except SystemInvalid as exc:
        trace.append(
            {
                "stage": "admission_gate",
                "decision": "SYSTEM_INVALID",
                "reason": exc.reason,
            }
        )
        result = {
            "status": "SYSTEM_INVALID",
            "reason": exc.reason,
            "trace": trace,
        }
        return attach_receipt(
            result,
            initial_payload=initial_payload,
            inspection_hash=receipt_inspection_hash(result),
        )
