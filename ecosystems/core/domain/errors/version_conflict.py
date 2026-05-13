class VersionConflictError(Exception):
    """
    Raised when optimistic concurrency control fails.
    """

    def __init__(self, stream_id, expected, actual):
        super().__init__(
            f"Version conflict on {stream_id}: "
            f"expected {expected}, got {actual}"
        )

        self.stream_id = stream_id
        self.expected = expected
        self.actual = actual