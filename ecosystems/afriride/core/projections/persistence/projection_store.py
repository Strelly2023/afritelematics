from typing import Protocol, Optional, Dict, Any, Iterable


class ProjectionStore(Protocol):
    """
    Abstract persistence layer for projections.

    Responsibilities:
    - Store projection state (key-value)
    - Provide fast read access
    - Support replay (clear/reset)
    - Be backend-agnostic (Redis, Postgres, etc.)

    Guarantees:
    - No business logic
    - No domain awareness
    - Only handles persistence
    """

    # --------------------------------------------------
    # CORE OPERATIONS
    # --------------------------------------------------
    def upsert(self, key: str, value: Dict[str, Any]) -> None:
        """
        Insert or update a projection record.
        """
        ...

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a projection record by key.
        """
        ...

    def delete(self, key: str) -> None:
        """
        Delete a projection record.
        """
        ...

    # --------------------------------------------------
    # OPTIONAL OPERATIONS (RECOMMENDED)
    # --------------------------------------------------
    def scan(self, pattern: str) -> Iterable[str]:
        """
        Iterate over keys matching a pattern.

        Example:
            scan("ride:*") → ["ride:1", "ride:2"]

        Used for:
        - listing projections
        - filtering
        - debugging
        """
        ...

    def clear(self) -> None:
        """
        Remove ALL projection data.

        Used for:
        - replay rebuild
        - testing reset
        - migration workflows
        """
        ...