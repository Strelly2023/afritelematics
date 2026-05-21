from __future__ import annotations


class FailureInjector:
    def kill_workers(
        self,
        workers: tuple[str, ...],
        *,
        percentage: float,
    ) -> tuple[str, ...]:
        if not 0 <= percentage < 1:
            raise ValueError("percentage must be greater than or equal to 0 and less than 1")
        survivors = max(1, int(len(workers) * (1 - percentage)))
        return tuple(workers[:survivors])
