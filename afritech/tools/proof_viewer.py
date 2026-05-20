from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract
from afritech.semantic_engine.inspection import inspect_admission, mermaid_proof_graph


def load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("input must be a mapping")
    return payload


def load_result_or_contract(path: Path) -> dict[str, Any]:
    payload = load_payload(path)
    if "status" in payload and "trace" in payload:
        return payload
    if "contract" in payload and isinstance(payload["contract"], dict):
        return admit_contract(payload["contract"], truth_values=payload.get("truth_values"))
    return admit_contract(payload)


def summary(result: dict[str, Any]) -> str:
    inspection = inspect_admission(result)
    proof = inspection["proof"]
    lines = [
        f"status: {inspection['status']}",
        f"program_id: {inspection.get('program_id')}",
        f"reason: {inspection.get('reason')}",
        f"trace_complete: {inspection['trace_complete']}",
        f"proof_present: {proof['present']}",
        f"normalized_expression_hash: {proof['normalized_expression_hash']}",
        f"proof_hash: {proof['proof_hash']}",
        f"inspection_hash: {inspection['inspection_hash']}",
        "timeline:",
    ]
    for entry in inspection["timeline"]:
        detail = entry.get("decision") or entry.get("reason") or entry.get("hash") or ""
        lines.append(f"  {entry['index']}. {entry['stage']} {detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m afritech.tools.proof_viewer",
        description="Inspect semantic admission proof and trace artifacts.",
    )
    parser.add_argument("input", help="Path to a contract YAML or admission result JSON/YAML.")
    parser.add_argument(
        "--format",
        choices=["summary", "json", "mermaid"],
        default="summary",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = load_result_or_contract(Path(args.input))

    if args.format == "summary":
        print(summary(result))
    elif args.format == "json":
        print(json.dumps(inspect_admission(result), indent=2, sort_keys=True))
    else:
        print(mermaid_proof_graph(result))

    return 0 if result.get("status") in {"ADMIT", "DENY"} else 1


if __name__ == "__main__":
    sys.exit(main())
