from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from architecture_validator.config import DEFAULT_CONFIG_PATH, load_config
from architecture_validator.engine.context import ValidatorContext
from architecture_validator.engine.runner import run_rules
from architecture_validator.report.formatter import format_json_report, format_text_report
from architecture_validator.report.json_report import write_json_report
from architecture_validator.rules.ai_governance import check_ai_governance
from architecture_validator.rules.api_contracts import check_api_contracts
from architecture_validator.rules.ast_validation import check_ast_validation
from architecture_validator.rules.blockchain_verification import check_blockchain_verification
from architecture_validator.rules.code_scanning import check_ui_authority
from architecture_validator.rules.documentation import check_documentation
from architecture_validator.rules.invariants import check_invariants
from architecture_validator.rules.openapi_diff import check_openapi_diff
from architecture_validator.rules.replay import check_replay
from architecture_validator.rules.security import check_security
from architecture_validator.rules.tests_alignment import check_tests_alignment


def run_checks(config_path: str | Path = DEFAULT_CONFIG_PATH):
    config = load_config(config_path)
    return run_rules(ValidatorContext(config=config), [
        check_invariants,
        check_ast_validation,
        check_api_contracts,
        check_openapi_diff,
        check_blockchain_verification,
        check_security,
        check_ai_governance,
        check_replay,
        check_documentation,
        check_ui_authority,
        check_tests_alignment,
    ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run NovaRide architecture compliance checks.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to architecture validator config.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report output format.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a JSON compliance report artifact.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = run_checks(args.config)
    report = format_json_report(results) if args.format == "json" else format_text_report(results)
    if args.output:
        write_json_report(results, args.output)
    print(report)
    return 1 if any(not result.passed for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
