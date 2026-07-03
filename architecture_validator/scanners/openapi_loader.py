from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_openapi(path: str | Path) -> dict[str, Any]:
    contract_path = Path(path)
    text = contract_path.read_text(encoding="utf-8")
    if contract_path.suffix == ".json":
        payload = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - dependency exists in project env
            raise RuntimeError("PyYAML is required to load YAML OpenAPI documents") from exc
        payload = yaml.safe_load(text)

    if not isinstance(payload, dict):
        raise ValueError(f"OpenAPI document must be an object: {contract_path}")
    return payload
