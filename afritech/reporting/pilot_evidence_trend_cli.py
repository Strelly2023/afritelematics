from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from afritech.reporting.pilot_evidence_report import AUTHORITY_SOURCE
from afritech.reporting.pilot_evidence_trend import (
    TREND_CLASSIFICATION,
    PilotEvidenceTrendComparisonError,
    compare_pilot_evidence_reports,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        reports = [_read_report_payload(Path(path)) for path in args.input]
        payload = compare_pilot_evidence_reports(reports).canonical_dict()
        if args.validate:
            _validate_trend_payload(payload)

        output = json.dumps(payload, indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(f"{output}\n", encoding="utf-8")
        else:
            sys.stdout.write(f"{output}\n")
    except (OSError, ValueError, json.JSONDecodeError, PilotEvidenceTrendComparisonError) as exc:
        sys.stderr.write(f"pilot evidence trend failed: {exc}\n")
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m afritech.reporting.pilot_evidence_trend_cli",
        description="Compare generated review-only pilot evidence report JSON payloads.",
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Generated pilot report JSON payload files to compare in order.",
    )
    parser.add_argument("--output", help="Optional output path. Defaults to stdout.")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated trend boundaries before writing.",
    )
    return parser


def _read_report_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain one generated report JSON object")
    return payload


def _validate_trend_payload(payload: dict[str, Any]) -> None:
    if payload.get("classification") != TREND_CLASSIFICATION:
        raise PilotEvidenceTrendComparisonError(
            "trend classification must be REVIEWABLE_PILOT_EVIDENCE_TREND"
        )
    if payload.get("production_proof") is not False:
        raise PilotEvidenceTrendComparisonError("trend production_proof must be false")
    if payload.get("authority_source") != AUTHORITY_SOURCE:
        raise PilotEvidenceTrendComparisonError(
            "trend authority_source must be observability_only"
        )


if __name__ == "__main__":
    raise SystemExit(main())
