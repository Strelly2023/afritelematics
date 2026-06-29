"""Token-bucket rate limiting for governed partner traffic."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
import time


@dataclass
class TokenBucket:
    capacity: int
    refill_rate: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.capacity = max(1, int(self.capacity))
        self.refill_rate = max(0.0, float(self.refill_rate))
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()
        self._lock = Lock()

    def configure(self, *, capacity: int, refill_rate: float) -> None:
        with self._lock:
            self.capacity = max(1, int(capacity))
            self.refill_rate = max(0.0, float(refill_rate))
            self.tokens = min(self.tokens, float(self.capacity))

    def consume(self, tokens: int = 1) -> bool:
        amount = max(1, int(tokens))
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            if elapsed > 0 and self.refill_rate > 0:
                self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))
            self.last_refill = now
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False
