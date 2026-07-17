"""Celery app for AfriPay async processing.

The module imports cleanly without Celery installed so local deterministic tests
can still run. Production containers install Celery and execute the same task
functions through the worker command.
"""

from __future__ import annotations

import os
from typing import Any, Callable


try:
    from celery import Celery
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    Celery = None  # type: ignore[assignment]


class LocalTask:
    def __init__(self, fn: Callable[..., Any]) -> None:
        self.fn = fn

    def delay(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)


if Celery is not None:
    always_eager = os.environ.get("AFRIPAY_CELERY_ALWAYS_EAGER", "0").lower() in {
        "1", "true", "yes", "on"
    }
    app = Celery(
        "afripay",
        broker=os.environ.get("CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0")),
        backend=os.environ.get("CELERY_RESULT_BACKEND", os.environ.get("REDIS_URL", "redis://localhost:6379/1")),
    )
    app.conf.update(
        task_default_queue="afripay",
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_time_limit=120,
        result_expires=3600,
        task_always_eager=always_eager,
        task_store_eager_result=False,
    )
else:
    app = None


def shared_task(*task_args: Any, **task_kwargs: Any):
    def decorator(fn: Callable[..., Any]):
        if app is None:
            return LocalTask(fn)
        return app.task(*task_args, **task_kwargs)(fn)

    return decorator
