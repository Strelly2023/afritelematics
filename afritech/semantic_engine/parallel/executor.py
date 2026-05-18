from collections.abc import Callable, Iterable
from typing import TypeVar


T = TypeVar("T")
R = TypeVar("R")


def execute_sequential(items: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    return [fn(item) for item in items]


def execute_deterministic(items: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    return execute_sequential(items, fn)
