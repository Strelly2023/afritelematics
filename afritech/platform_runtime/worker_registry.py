"""Worker registry for NovaTech product runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ProductContractViolation
from .models import WorkerDefinition


class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[tuple[str, str], WorkerDefinition] = {}

    def register(self, definition: WorkerDefinition) -> None:
        key = (definition.product_code.lower(), definition.name.lower())
        if key in self._workers:
            raise ProductContractViolation("duplicate_worker")
        if definition.dead_letter_queue == "" and definition.required:
            raise ProductContractViolation("required_worker_needs_dlq")
        if definition.concurrency <= 0:
            raise ProductContractViolation("invalid_worker_concurrency")
        if not definition.queue.startswith(definition.product_code):
            raise ProductContractViolation("worker_queue_namespace_mismatch")
        self._workers[key] = definition

    def unregister_product(self, product_code: str) -> None:
        key = product_code.lower()
        self._workers = {k: v for k, v in self._workers.items() if k[0] != key}

    def get(self, product_code: str, worker_name: str) -> WorkerDefinition:
        key = (product_code.lower(), worker_name.lower())
        if key not in self._workers:
            raise KeyError(f"unknown worker: {product_code}:{worker_name}")
        return self._workers[key]

    def list_product_workers(self, product_code: str) -> tuple[WorkerDefinition, ...]:
        key = product_code.lower()
        return tuple(defn for (product, _), defn in self._workers.items() if product == key)

    def snapshot(self) -> dict[str, Any]:
        return {
            "workers": [
                {
                    "product_code": worker.product_code,
                    "name": worker.name,
                    "queue": worker.queue,
                    "concurrency": worker.concurrency,
                    "timeout_seconds": worker.timeout_seconds,
                    "max_attempts": worker.max_attempts,
                    "dead_letter_queue": worker.dead_letter_queue,
                    "required": worker.required,
                }
                for worker in self._workers.values()
            ]
        }


__all__ = ["WorkerRegistry"]
