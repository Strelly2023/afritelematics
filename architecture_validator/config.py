from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("architecture_validator/config.yaml")


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1]
    return value


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load the validator's simple YAML config.

    The repository already depends on PyYAML, but this parser intentionally
    supports only the small key/list shape used by the validator so CI can run
    without importing optional runtime dependencies.
    """

    config_path = Path(path)
    data: dict[str, Any] = {}
    current_list: str | None = None

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise ValueError(f"list item without key in {config_path}: {line}")
            data.setdefault(current_list, []).append(_parse_scalar(line[4:]))
            continue
        if ":" not in line:
            raise ValueError(f"unsupported config line in {config_path}: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = []
            current_list = key
        else:
            data[key] = _parse_scalar(value)
            current_list = None

    return data
