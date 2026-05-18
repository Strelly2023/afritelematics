from dataclasses import dataclass, field
from typing import Any

from afritech.shared.types import stable_hash


@dataclass
class GlobalStateRegistry:
    _state: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._state)

    def state_hash(self) -> str:
        return stable_hash(self._state)
