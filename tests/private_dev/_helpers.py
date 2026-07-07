from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def read_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def assert_contains_all(source: str, labels: list[str], *, context: str) -> None:
    missing = [label for label in labels if label not in source]
    assert not missing, f"{context} missing labels: {missing}"

