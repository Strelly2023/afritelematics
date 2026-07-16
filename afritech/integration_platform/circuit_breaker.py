"""Circuit breaker state for provider failover."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import time


class CircuitBreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    DISABLED = "DISABLED"


@dataclass(slots=True)
class CircuitBreaker:
    policy_id: str
    failure_threshold: int = 5
    reset_timeout_seconds: int = 60
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    opened_at: float | None = None

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.opened_at = time()

    def allow_request(self) -> bool:
        if self.state == CircuitBreakerState.DISABLED:
            return True
        if self.state == CircuitBreakerState.OPEN:
            if self.opened_at is None:
                return False
            if time() - self.opened_at >= self.reset_timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        return True

