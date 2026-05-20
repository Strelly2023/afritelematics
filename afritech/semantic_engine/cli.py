from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract
from afritech.semantic_engine.ir.schema import SystemInvalid


def _load_truth_values(path: str | None) -> dict[str, bool] | None:
    if path is None:
        return None

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemInvalid("truth_values_must_be_mapping")
    return {str(symbol): bool(value) for symbol, value in payload.items()}


def _compact(result: dict[str, Any]) -> dict[str, Any]:
    proof = result.get("proof", {})
    return {
        "status": result["status"],
        "program_id": result.get("program_id"),
        "reason": result.get("reason"),
        "normalized_expression_hash": proof.get("normalized_expression_hash"),
        "proof_hash": proof.get("proof_hash"),
        "trace_stages": [entry["stage"] for entry in result.get("trace", [])],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m afritech.semantic_engine.cli",
        description="Run a semantic contract through the single-process admission MVP.",
    )
    parser.add_argument("contract", help="Path to a semantic contract YAML file.")
    parser.add_argument(
        "--truth-values",
        help="Optional YAML mapping of symbol truth values. Defaults to truth_values in the contract.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Emit full normalization/hash/evaluation/proof trace.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = admit_contract(
        args.contract,
        truth_values=_load_truth_values(args.truth_values),
    )
    output = result if args.trace else _compact(result)
    print(json.dumps(output, indent=2 if args.pretty else None, sort_keys=True))

    if result["status"] == "ADMIT":
        return 0
    if result["status"] == "DENY":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
