"""Command-line adapter for the AfriRide replay-governed proof core.

The CLI is an operability surface. It reads declared JSON bundles, calls the
same deterministic proof functions used by the HTTP adapter, and prints
canonical JSON results. It does not persist state or define truth.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, TextIO

from fastapi import HTTPException

from ecosystems.afriride.core.application.adapters.http.proof_api import (
    _execution_steps_from_payload,
    _pricing_config_from_payload,
    _ride_from_payload,
    build_audit_report,
    build_replay_report,
    explain_audit_report,
)
from ecosystems.afriride.domain.evidence.evidence_store import (
    EvidenceStoreViolation,
    InMemoryRideEvidenceStore,
    RideEvidenceBundle,
)
from ecosystems.afriride.domain.optimization.deterministic_matching import match_driver
from ecosystems.afriride.domain.optimization.deterministic_pricing import compute_price
from ecosystems.afriride.domain.optimization.deterministic_routing import compute_route
from ecosystems.afriride.domain.trace.ride_execution_trace import (
    build_ride_execution_trace,
)


def main(argv: list[str] | None = None) -> int:
    """Run the AfriRide proof CLI."""

    return run(argv or sys.argv[1:], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)


def run(
    argv: list[str],
    *,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run a proof command and return a process-style exit code."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        payload = _load_json(args.bundle, stdin)
        if args.command == "audit":
            result = build_audit_report(payload)
            exit_code = 0 if result["replay"]["replay_valid"] else 1
        elif args.command == "replay":
            result = build_replay_report(payload)
            exit_code = 0 if result["replay_valid"] else 1
        elif args.command == "explain":
            result = explain_audit_report(payload)
            exit_code = 0 if result["replay_valid"] else 1
        elif args.command == "verify-store":
            result = _verify_store(payload)
            exit_code = 0 if result["replay_valid"] else 1
        else:
            parser.error(f"unknown command: {args.command}")
    except (EvidenceStoreViolation, HTTPException, KeyError, ValueError) as exc:
        _print_json({"error": _error_message(exc), "ok": False}, stderr)
        return 1

    _print_json(result, stdout)
    return exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="afriride-proof",
        description="Operate AfriRide proof bundles without weakening replay authority.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("audit", "replay", "explain", "verify-store"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument(
            "bundle",
            help="Path to a declared JSON bundle, or '-' to read from stdin.",
        )
    return parser


def _load_json(path: str, stdin: TextIO) -> dict[str, Any]:
    raw = stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("proof bundle must be a JSON object")
    return data


def _verify_store(payload: dict[str, Any]) -> dict[str, Any]:
    store = InMemoryRideEvidenceStore()
    bundle = _evidence_bundle_from_payload(payload)
    trace_hash = store.store(bundle)
    verified = store.get(trace_hash)
    return {
        "evidence": verified.bundle.canonical_summary(),
        "replay": {
            "assignment_hash_match": verified.replay_report.assignment_hash_match,
            "dag_hash_match": verified.replay_report.dag_hash_match,
            "execution_steps_hash_match": (
                verified.replay_report.execution_steps_hash_match
            ),
            "original_trace_hash": verified.replay_report.original_trace_hash,
            "price_hash_match": verified.replay_report.price_hash_match,
            "replay_valid": verified.replay_report.replay_valid,
            "replayed_trace_hash": verified.replay_report.replayed_trace_hash,
            "ride_hash_match": verified.replay_report.ride_hash_match,
            "route_hash_match": verified.replay_report.route_hash_match,
        },
        "replay_valid": verified.replay_report.replay_valid,
        "trace_hash": trace_hash,
    }


def _evidence_bundle_from_payload(payload: dict[str, Any]) -> RideEvidenceBundle:
    ride = _ride_from_payload(payload["ride"])
    assignment = match_driver(
        ride,
        payload.get("drivers", ()),
        allow_cross_partition=bool(payload.get("allow_cross_partition", False)),
    )
    if assignment is None:
        raise ValueError("No admissible driver assignment")
    route = compute_route(ride, payload["map_graph"])
    pricing_config = _pricing_config_from_payload(payload["pricing_config"])
    price = compute_price(ride, assignment, route, pricing_config)
    steps = _execution_steps_from_payload(ride, payload.get("execution_requests", ()))
    trace = build_ride_execution_trace(
        ride,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=steps,
    )
    return RideEvidenceBundle(
        ride=ride,
        trace=trace,
        drivers=tuple(payload.get("drivers", ())),
        map_graph=payload["map_graph"],
        pricing_config=pricing_config,
        assignment=assignment,
        route=route,
        price=price,
        execution_steps=steps,
    )


def _print_json(result: dict[str, Any], stream: TextIO) -> None:
    stream.write(json.dumps(result, indent=2, sort_keys=True))
    stream.write("\n")


def _error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    if isinstance(exc, KeyError):
        return f"missing required field: {exc.args[0]}"
    return str(exc)


if __name__ == "__main__":
    raise SystemExit(main())
