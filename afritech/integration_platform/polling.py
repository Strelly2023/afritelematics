"""Polling definitions and runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time

from .contracts import PollingDefinition


@dataclass(slots=True)
class PollingJob:
    definition: PollingDefinition
    last_run_at: float | None = None
    last_error: str | None = None
    run_count: int = 0


@dataclass(slots=True)
class PollingRuntime:
    jobs: dict[str, PollingJob] = field(default_factory=dict)

    def register(self, definition: PollingDefinition) -> PollingJob:
        job = PollingJob(definition=definition)
        self.jobs[definition.polling_id] = job
        return job

    def mark_run(self, polling_id: str, *, error: str | None = None) -> PollingJob:
        job = self.jobs[polling_id]
        job.last_run_at = time()
        job.run_count += 1
        job.last_error = error
        return job

