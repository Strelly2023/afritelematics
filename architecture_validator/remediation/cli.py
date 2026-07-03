from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from architecture_validator.config import DEFAULT_CONFIG_PATH
from architecture_validator.remediation.self_heal import run_self_healing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run NovaRide autonomous architecture remediation.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--apply", action="store_true", help="Record governed remediation actions.")
    parser.add_argument(
        "--allow-risky",
        action="store_true",
        help="Allow high-risk actions to be recorded as applied. Source editing remains disabled.",
    )
    parser.add_argument(
        "--output",
        default="architecture_remediation_report.json",
        help="Path for remediation report JSON.",
    )
    parser.add_argument(
        "--learning-memory",
        default="architecture_learning_memory.json",
        help="Path for the governed learning memory JSON artifact.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run_self_healing(
        config_path=args.config,
        apply=args.apply,
        allow_risky=args.allow_risky,
        artifact_path=args.output,
        learning_memory_path=args.learning_memory,
    )
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["final_passed"] and payload["manual_review_required"] == 0:
        return 0
    return 1 if payload["manual_review_required"] else 0


if __name__ == "__main__":
    sys.exit(main())
