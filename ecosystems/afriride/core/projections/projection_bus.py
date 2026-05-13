class ProjectionBus:
    """
    Fan-out dispatcher for projections.

    Guarantees:
    - Deterministic event propagation (same order as event store)
    - Each projection processes every event
    - No side-effects outside projections
    - Replay-safe

    Notes:
    - Synchronous by design (single-node consistency)
    - Can be replaced by async event bus later
    """

    def __init__(self, projections):
        self.projections = projections

    # --------------------------------------------------
    # PUBLISH EVENT (LIVE FLOW)
    # --------------------------------------------------
    def publish(self, event):
        """
        Send a single event to all projections.

        Fail-soft strategy:
        - One projection failure should not break others
        - Errors should be logged/handled externally
        """

        for projection in self.projections:
            try:
                projection.apply(event)
            except Exception as e:
                # Fail-soft: isolate projection failure
                self._handle_error(projection, event, e)

    # --------------------------------------------------
    # REPLAY (FULL REBUILD)
    # --------------------------------------------------
    def replay(self, events):
        """
        Replays a list of events in order.

        Guarantees:
        - Same result as live system
        - Deterministic rebuild
        """

        for event in events:
            self.publish(event)

    # --------------------------------------------------
    # RESET (OPTIONAL)
    # --------------------------------------------------
    def reset(self):
        """
        Reset all projections before replay.

        Requires projection store support.
        """

        for projection in self.projections:
            if hasattr(projection, "store") and hasattr(projection.store, "clear"):
                try:
                    projection.store.clear()
                except Exception as e:
                    self._handle_error(projection, None, e)

    # --------------------------------------------------
    # INTERNAL ERROR HANDLER
    # --------------------------------------------------
    def _handle_error(self, projection, event, error):
        """
        Centralized error handling hook.

        Default strategy:
        - Print error (safe default)
        - Can be replaced with logging/monitoring
        """

        print(
            f"[ProjectionBus ERROR] "
            f"projection={projection.__class__.__name__} "
            f"event={getattr(event, 'type', None)} "
            f"error={str(error)}"
        )
