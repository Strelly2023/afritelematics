"""Circuit breaker for downstream runtime protection."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
import time


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_time: float = 30.0
    failures: int = field(default=0)
    last_failure: float | None = field(default=None)
    state: str = field(default="closed")
    _lock: Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.failure_threshold = max(1, int(self.failure_threshold))
        self.recovery_time = max(0.0, float(self.recovery_time))
        self._lock = Lock()

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            self.last_failure = time.monotonic()
            if self.failures >= self.failure_threshold:
                self.state = "open"

    def allow_request(self) -> bool:
        with self._lock:
            if self.state == "closed":
                return True
            if self.state == "open":
                if self.last_failure is None:
                    return False
                if time.monotonic() - self.last_failure >= self.recovery_time:
                    self.state = "half-open"
                    return True
                return False
            return True

    def reset(self) -> None:
        with self._lock:
            self.failures = 0
            self.last_failure = None
            self.state = "closed"
