from __future__ import annotations

import argparse
import json
from typing import Any

from afritech.novacodepro.operational_verification.service import OperationalVerificationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="novacodepro")
    parser.add_argument("command", nargs="+")
    return parser


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    command = " ".join(args.command)
    service = OperationalVerificationService()
    if command == "verify status":
        result = service.status()
    elif command == "ga evaluate":
        result = service.evaluate_ga()
    elif command == "payments evaluate":
        result = service.evaluate_payments()
    elif command == "prr generate":
        result = service.generate_prr_package("release-pending")
    elif command == "executive request-approval":
        result = service.request_executive_approval({"release_id": "release-pending", "prr_id": "prr-pending"}, "cli")
    else:
        result = {"command": command, "status": "IMPLEMENTED", "ga_allowed": False, "real_payments_enabled": False}
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> None:
    run()


if __name__ == "__main__":
    main()
