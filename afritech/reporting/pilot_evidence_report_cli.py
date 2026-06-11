from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from afritech.reporting.pilot_evidence_report import (
    build_pilot_evidence_run_report,
)
from afritech.reporting.pilot_evidence_report_validator import (
    PilotEvidenceReportValidationError,
    validate_pilot_evidence_report,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        records = _read_records(Path(args.input))
        report = build_pilot_evidence_run_report(args.pilot_run_id, records)
        payload = report.canonical_dict()
        if args.validate:
            validate_pilot_evidence_report(payload)

        output = report.markdown_text() if args.format == "markdown" else report.json_text()
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
            if not output.endswith("\n"):
                sys.stdout.write("\n")
    except (OSError, ValueError, json.JSONDecodeError, PilotEvidenceReportValidationError) as exc:
        sys.stderr.write(f"pilot evidence report failed: {exc}\n")
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m afritech.reporting.pilot_evidence_report_cli",
        description="Generate review-only pilot evidence reports from observability records.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to observability records JSON or JSONL.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Report output format.",
    )
    parser.add_argument("--output", help="Optional output path. Defaults to stdout.")
    parser.add_argument(
        "--pilot-run-id",
        default="pilot-run-observability",
        help="Pilot run identifier attached to every report entry.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated report boundaries before writing.",
    )
    return parser


def _read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return _read_jsonl_records(path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict) and isinstance(raw.get("records"), list):
        records = raw["records"]
    elif isinstance(raw, dict) and isinstance(raw.get("entries"), list):
        records = raw["entries"]
    else:
        raise ValueError("input must be a list or an object with records/entries list")

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("all observability records must be objects")
    return list(records)


def _read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"JSONL line {line_number} must be an object")
        records.append(record)
    return records


if __name__ == "__main__":
    raise SystemExit(main())
