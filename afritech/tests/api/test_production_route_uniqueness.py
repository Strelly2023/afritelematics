from __future__ import annotations

from collections import defaultdict
import os
import warnings


os.environ.setdefault("NOVATECH_RUNTIME_CONTROL_SQLITE_PATH", "/tmp/afritech-route-test.sqlite3")
os.environ.setdefault("NOVATECH_EVIDENCE_ROOT", "/tmp/afritech-route-test-evidence")

from afritech.api.app import app  # noqa: E402


def test_production_routes_are_unique() -> None:
    owners: dict[tuple[str, str], list[dict[str, str | None]]] = defaultdict(list)
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or set()
        if not path:
            continue
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            owners[(method, path)].append(
                {
                    "name": getattr(route, "name", None),
                    "endpoint": getattr(getattr(route, "endpoint", None), "__module__", None),
                }
            )
    duplicates = {key: value for key, value in owners.items() if len(value) > 1}
    assert not duplicates, duplicates


def test_openapi_operation_ids_are_unique_without_duplicate_warnings() -> None:
    app.openapi_schema = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        schema = app.openapi()
    duplicate_warnings = [warning for warning in caught if "Duplicate Operation ID" in str(warning.message)]
    assert not duplicate_warnings, [str(warning.message) for warning in duplicate_warnings]

    operation_ids: dict[str, tuple[str, str]] = {}
    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            operation_id = operation.get("operationId")
            assert operation_id, (method, path)
            assert operation_id not in operation_ids, {
                "operation_id": operation_id,
                "first": operation_ids.get(operation_id),
                "second": (method, path),
            }
            operation_ids[operation_id] = (method, path)
