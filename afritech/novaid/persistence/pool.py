"""Small bounded psycopg pool used when psycopg-pool is unavailable."""

from __future__ import annotations

from contextlib import contextmanager
from queue import Empty, Full, LifoQueue
from threading import Lock
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row


class PoolExhausted(RuntimeError):
    pass


class NovaIDPostgresPool:
    def __init__(
        self, dsn: str, *, minimum_size: int = 1, maximum_size: int = 8, timeout: float = 5.0
    ):
        if minimum_size < 0 or maximum_size < 1 or minimum_size > maximum_size:
            raise ValueError("invalid_postgres_pool_configuration")
        self.dsn, self.maximum_size, self.timeout = dsn, maximum_size, timeout
        self._available: LifoQueue[Any] = LifoQueue(maximum_size)
        self._lock, self._created, self._closed = Lock(), 0, False
        for _ in range(minimum_size):
            self._available.put(self._new_connection())

    def _new_connection(self):
        connection = psycopg.connect(self.dsn, autocommit=False, row_factory=dict_row)
        with self._lock:
            self._created += 1
        return connection

    def acquire(self):
        if self._closed:
            raise RuntimeError("postgres_pool_closed")
        try:
            connection = self._available.get_nowait()
        except Empty:
            with self._lock:
                create = self._created < self.maximum_size
            if create:
                return self._new_connection()
            try:
                connection = self._available.get(timeout=self.timeout)
            except Empty as exc:
                raise PoolExhausted("postgres_pool_exhausted") from exc
        if connection.closed:
            with self._lock:
                self._created -= 1
            return self._new_connection()
        return connection

    def release(self, connection: Any) -> None:
        if connection.info.transaction_status.value != 0:
            connection.rollback()
        if self._closed or connection.closed:
            if not connection.closed:
                connection.close()
            with self._lock:
                self._created -= 1
            return
        try:
            self._available.put_nowait(connection)
        except Full:
            connection.close()
            with self._lock:
                self._created -= 1

    @contextmanager
    def connection(self) -> Iterator[Any]:
        connection = self.acquire()
        try:
            yield connection
        finally:
            self.release(connection)

    @property
    def created(self) -> int:
        return self._created

    @property
    def available(self) -> int:
        return self._available.qsize()

    def check(self) -> bool:
        with self.connection() as connection:
            return connection.execute("SELECT 1").fetchone() is not None

    def close(self) -> None:
        self._closed = True
        while True:
            try:
                connection = self._available.get_nowait()
            except Empty:
                break
            connection.close()
            with self._lock:
                self._created -= 1
