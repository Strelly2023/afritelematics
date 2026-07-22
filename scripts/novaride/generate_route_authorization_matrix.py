"""Generate the exact mounted NovaRide HTTP route authorization matrix."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.routing import APIRoute

from afriride_system.api.auth import authorization_policy
from afriride_system.api.main import app


OUTPUT = ROOT / "config" / "novaride" / "route_authorization_matrix.json"


def generate() -> list[dict[str, object]]:
    matrix: list[dict[str, object]] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or set()):
            if method in {"HEAD", "OPTIONS"}:
                continue
            policy = authorization_policy(method, route.path)
            test_key = f"{method.lower()}_{route.path.strip('/').replace('/', '_').replace('{', '').replace('}', '') or 'root'}"
            matrix.append(
                {
                    "method": method,
                    "path": route.path,
                    "router": (route.tags or ["untagged"])[0],
                    **policy,
                    "negative_test_id": f"SEC-NEG-{test_key}",
                    "positive_test_id": f"SEC-POS-{test_key}",
                }
            )
    return sorted(matrix, key=lambda item: (str(item["path"]), str(item["method"])))


def main() -> int:
    payload = {
        "schema_version": 1,
        "generator": "scripts/novaride/generate_route_authorization_matrix.py",
        "default_policy": "AUTHENTICATED_FAIL_CLOSED",
        "routes": generate(),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['routes'])} route policies to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
