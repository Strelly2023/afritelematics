"""Retry helpers for the integration runtime."""

from __future__ import annotations

from dataclasses import dataclass
import asyncio
import random
from collections.abc import Awaitable, Callable


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    policy_id: str
    attempts: int
    delays_seconds: tuple[float, ...]
    jitter: float = 0.2
    maximum_elapsed_seconds: float = 60.0


async def retry_transient(operation: Callable[[], Awaitable], policy: RetryPolicy):
    last_error = None
    start = asyncio.get_event_loop().time()
    for attempt in range(max(1, policy.attempts)):
        try:
            return await operation()
        except Exception as error:  # pragma: no cover - thin retry helper
            last_error = error
            if attempt >= policy.attempts - 1:
                raise
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > policy.maximum_elapsed_seconds:
                raise
            delay = policy.delays_seconds[min(attempt, len(policy.delays_seconds) - 1)] if policy.delays_seconds else 0
            if policy.jitter:
                delay += random.uniform(0, policy.jitter)
            if delay > 0:
                await asyncio.sleep(delay)
    if last_error is not None:
        raise last_error

