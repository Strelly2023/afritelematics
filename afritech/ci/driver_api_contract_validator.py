"""Validate strict AfriRide driver API route contracts."""

from __future__ import annotations

import ast
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DJANGO_URLS = ROOT / "afriride_system/django_app/config/urls.py"
API_URLS = ROOT / "afritech/api/urls.py"
DRIVER_VIEWS = ROOT / "afritech/api/afriride_driver_views.py"
CONTRACT_TESTS = ROOT / "afritech/tests/api/test_afriride_driver_views.py"
CONTRACT_SNAPSHOT = ROOT / "afritech/ci/contracts/driver_routes.json"


class DriverApiContractViolation(RuntimeError):
    """Raised when driver API route semantics drift."""


def validate() -> bool:
    _require_files()
    _validate_contract_snapshot()
    _validate_declared_routes()
    _validate_view_methods()
    _validate_contract_tests()
    return True


def _require_files() -> None:
    missing = [
        path
        for path in (
            DJANGO_URLS,
            API_URLS,
            DRIVER_VIEWS,
            CONTRACT_TESTS,
            CONTRACT_SNAPSHOT,
        )
        if not path.exists()
    ]
    if missing:
        raise DriverApiContractViolation(
            "missing driver API contract files: " + ", ".join(map(str, missing))
        )


def _load_snapshot() -> dict[str, object]:
    payload = json.loads(CONTRACT_SNAPSHOT.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DriverApiContractViolation("driver route contract snapshot must be a mapping")
    return payload


def _validate_contract_snapshot() -> None:
    payload = _load_snapshot()
    if payload.get("schema") != "afritech.driver_api_contract.v1":
        raise DriverApiContractViolation("driver route contract schema mismatch")
    if payload.get("status") != "CONTROLLED_PILOT_API_CONTRACT":
        raise DriverApiContractViolation("driver route contract status mismatch")
    truth_boundary = payload.get("truth_boundary")
    if not isinstance(truth_boundary, dict):
        raise DriverApiContractViolation("driver route contract truth boundary missing")
    for key in ("live_pilot_authorized", "production_proven", "economic_activation"):
        if truth_boundary.get(key) is not False:
            raise DriverApiContractViolation(f"truth boundary must remain false: {key}")

    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes:
        raise DriverApiContractViolation("driver route contract routes missing")
    seen: set[tuple[str, str]] = set()
    for route in routes:
        if not isinstance(route, dict):
            raise DriverApiContractViolation("driver route entries must be mappings")
        method = _text(route.get("method"), "route method")
        path = _text(route.get("path"), "route path")
        view = _text(route.get("view"), "route view")
        if not path.startswith("/"):
            raise DriverApiContractViolation(f"route path must be absolute: {path}")
        if path.endswith("/"):
            raise DriverApiContractViolation(f"trailing slash route alias forbidden: {path}")
        if method not in {"GET", "POST"}:
            raise DriverApiContractViolation(f"unsupported route method: {method}")
        if not _view_exists(view):
            raise DriverApiContractViolation(f"route references missing view: {view}")
        key = (method, path)
        if key in seen:
            raise DriverApiContractViolation(f"duplicate route contract entry: {method} {path}")
        seen.add(key)

    invalid_examples = payload.get("invalid_examples")
    if not isinstance(invalid_examples, list) or not invalid_examples:
        raise DriverApiContractViolation("invalid route examples missing")
    expected_invalid = {
        ("GET", "/driver/availability", 405),
        ("POST", "/api/driver/availability/", 404),
    }
    actual_invalid = {
        (
            _text(example.get("method"), "invalid method"),
            _text(example.get("path"), "invalid path"),
            example.get("expected_status"),
        )
        for example in invalid_examples
        if isinstance(example, dict)
    }
    if not expected_invalid.issubset(actual_invalid):
        raise DriverApiContractViolation("invalid route examples do not cover known edge cases")


def _validate_declared_routes() -> None:
    django_urls = DJANGO_URLS.read_text(encoding="utf-8")
    api_urls = API_URLS.read_text(encoding="utf-8")
    for source, route in (
        (django_urls, 'path("driver/availability", driver_availability)'),
        (django_urls, 'path("driver/status", driver_status)'),
        (django_urls, 'path("driver/<str:driver_id>/queue", driver_queue)'),
        (django_urls, 'path("ride/<str:ride_id>/complete", ride_complete)'),
        (api_urls, 'path("driver/availability", driver_availability)'),
        (api_urls, 'path("driver/status", driver_status)'),
    ):
        if route not in source:
            raise DriverApiContractViolation(f"missing strict route declaration: {route}")
    if 'path("driver/availability/"' in django_urls + api_urls:
        raise DriverApiContractViolation("driver availability trailing slash alias forbidden")


def _validate_view_methods() -> None:
    tree = ast.parse(DRIVER_VIEWS.read_text(encoding="utf-8"), filename=str(DRIVER_VIEWS))
    methods_by_view: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Name) or decorator.func.id != "api_view":
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.List):
                continue
            methods_by_view[node.name] = tuple(
                elt.value
                for elt in decorator.args[0].elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            )
    expected = {
        "driver_availability": ("POST",),
        "driver_status": ("POST",),
        "driver_queue": ("GET",),
        "driver_earnings": ("GET",),
        "driver_replay_history": ("GET",),
        "ride_accept": ("POST",),
        "ride_start": ("POST",),
        "ride_complete": ("POST",),
    }
    for view, methods in expected.items():
        if methods_by_view.get(view) != methods:
            raise DriverApiContractViolation(f"{view} method contract drifted")


def _validate_contract_tests() -> None:
    source = CONTRACT_TESTS.read_text(encoding="utf-8")
    for needle in (
        "test_driver_availability_post_is_valid_on_root_driver_route",
        "test_driver_availability_post_is_valid_on_declared_api_prefix",
        "test_driver_availability_get_is_method_rejected_not_silent_write",
        "test_driver_availability_trailing_slash_is_not_implicit_alias",
    ):
        if needle not in source:
            raise DriverApiContractViolation(f"missing route contract test: {needle}")


def _view_exists(view_name: str) -> bool:
    tree = ast.parse(DRIVER_VIEWS.read_text(encoding="utf-8"), filename=str(DRIVER_VIEWS))
    return any(isinstance(node, ast.FunctionDef) and node.name == view_name for node in tree.body)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DriverApiContractViolation(f"{label} is required")
    return value.strip()


def explain() -> str:
    payload = _load_snapshot()
    lines = [
        "Driver API contract explanation",
        f"schema={payload['schema']} status={payload['status']}",
        "valid routes:",
    ]
    for route in payload["routes"]:
        lines.append(f"✅ {route['method']} {route['path']} -> {route['view']}")
    lines.append("invalid examples:")
    for example in payload["invalid_examples"]:
        lines.append(
            f"❌ {example['method']} {example['path']} -> "
            f"{example['expected_status']} ({example['reason']})"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()
    try:
        validate()
    except DriverApiContractViolation as exc:
        print(f"Driver API contract validation FAILED: {exc}")
        return 1
    if args.explain:
        print(explain())
        return 0
    print("Driver API contract validation PASSED")
    print("Strict method/path routing preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
