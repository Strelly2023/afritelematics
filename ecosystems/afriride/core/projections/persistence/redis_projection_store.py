import json
import redis
from typing import Any, Dict, Optional, Iterable


class RedisProjectionStore:
    """
    Persistent projection storage using Redis.

    Responsibilities:
    - Store projection state (key-value)
    - Provide fast read access
    - Support scanning for queries
    - Support full reset (replay rebuild)

    Notes:
    - Uses JSON serialization
    - Keys should be namespaced by projection (e.g., "ride:", "driver:")
    """

    def __init__(self, url: str = "redis://localhost:6379/0", decode_responses: bool = True):
        self.client = redis.from_url(url, decode_responses=decode_responses)

    # --------------------------------------------------
    # CORE OPERATIONS
    # --------------------------------------------------
    def upsert(self, key: str, value: Dict[str, Any]) -> None:
        """
        Insert or update projection data.
        """
        try:
            self.client.set(key, json.dumps(value))
        except Exception as e:
            self._handle_error("UPSERT", key, e)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve projection data.
        """
        try:
            raw = self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            self._handle_error("GET", key, e)
            return None

    def delete(self, key: str) -> None:
        """
        Delete projection entry.
        """
        try:
            self.client.delete(key)
        except Exception as e:
            self._handle_error("DELETE", key, e)

    # --------------------------------------------------
    # OPTIONAL OPERATIONS (USED BY PROJECTIONS)
    # --------------------------------------------------
    def scan(self, pattern: str) -> Iterable[str]:
        """
        Iterate over keys matching a pattern.

        Example:
            scan("ride:*")
        """
        try:
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor=cursor, match=pattern)
                for key in keys:
                    yield key
                if cursor == 0:
                    break
        except Exception as e:
            self._handle_error("SCAN", pattern, e)
            return []

    def clear(self) -> None:
        """
        Clear all projection data.

        WARNING:
        This clears the entire Redis database.
        Use only in controlled environments (replay/testing).
        """
        try:
            self.client.flushdb()
        except Exception as e:
            self._handle_error("CLEAR", "*", e)

    # --------------------------------------------------
    # OPTIONAL: BULK UPSERT (PERFORMANCE)
    # --------------------------------------------------
    def upsert_many(self, items: Dict[str, Dict[str, Any]]) -> None:
        """
        Bulk insert/update using Redis pipeline.
        Useful for replay performance.
        """
        try:
            pipe = self.client.pipeline()

            for key, value in items.items():
                pipe.set(key, json.dumps(value))

            pipe.execute()
        except Exception as e:
            self._handle_error("BULK_UPSERT", "MULTI", e)

    # --------------------------------------------------
    # INTERNAL ERROR HANDLING
    # --------------------------------------------------
    def _handle_error(self, operation: str, key: str, error: Exception):
        """
        Centralized error handler.

        Replace with logging/monitoring later.
        """
        print(
            f"[RedisProjectionStore ERROR] "
            f"operation={operation} key={key} error={str(error)}"
        )