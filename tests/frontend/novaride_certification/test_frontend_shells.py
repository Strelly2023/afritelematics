from __future__ import annotations

import json
from pathlib import Path


def test_new_frontend_shells_have_required_certification_metadata() -> None:
    for path in Path("apps").glob("novaride-*/app.json"):
        payload = json.loads(path.read_text())
        assert payload["route_shell"] is True
        assert payload["auth_guard"] == "NovaID"
        assert payload["api_sdk"] == "@novaride/api-sdk"
        assert payload["error_boundary"] is True
        assert payload["health_diagnostics"] is True
