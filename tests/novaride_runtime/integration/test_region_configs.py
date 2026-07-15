from __future__ import annotations

import json
from pathlib import Path


def test_region_configs_preserve_pilot_and_payment_guards() -> None:
    paths = sorted(Path("config/novaride/regions").glob("*.json"))
    assert len(paths) >= 16
    for path in paths:
        payload = json.loads(path.read_text())
        assert payload["region_code"]
        assert payload["currencies"]
        assert payload["languages"]
        assert payload["emergency_numbers"]
        assert payload["payment_mode"] == "sandbox"
        assert payload["pilot_mode"] is True
        assert payload["feature_flags"]["REAL_PAYMENTS_ENABLED"] is False
        assert payload["feature_flags"]["GA_ALLOWED"] is False
