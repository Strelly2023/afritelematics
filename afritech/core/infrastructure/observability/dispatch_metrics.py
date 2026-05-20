class DispatchMetrics:
    """
    Lightweight in-memory dispatch metrics collector.

    Responsibilities:
    - track dispatch offer attempts
    - track retry cycles
    - track successful assignments
    - provide immutable snapshots for observability

    Characteristics:
    - deterministic
    - side-effect free reads
    - replay-safe
    - test-friendly
    """

    def __init__(self):

        # ---------------------------------------------
        # ride_id -> offer attempts
        # ---------------------------------------------
        self.attempts = {}

        # ---------------------------------------------
        # ride_id -> retry count
        # ---------------------------------------------
        self.retries = {}

        # ---------------------------------------------
        # ride_id -> assignment state
        # ---------------------------------------------
        self.assignments = {}

    # ==================================================
    # WRITE OPERATIONS
    # ==================================================

    # --------------------------------------------------
    # TRACK OFFER ATTEMPT
    # --------------------------------------------------
    def record_attempt(self, ride_id):
        """
        Increment offer attempt count.
        """

        self.attempts[ride_id] = (
            self.attempts.get(ride_id, 0) + 1
        )

    # --------------------------------------------------
    # TRACK RETRY
    # --------------------------------------------------
    def record_retry(self, ride_id):
        """
        Increment retry count.
        """

        self.retries[ride_id] = (
            self.retries.get(ride_id, 0) + 1
        )

    # --------------------------------------------------
    # TRACK ASSIGNMENT SUCCESS
    # --------------------------------------------------
    def record_assignment(self, ride_id):
        """
        Mark ride as successfully assigned.
        """

        self.assignments[ride_id] = True

    # --------------------------------------------------
    # CLEAR ASSIGNMENT (OPTIONAL)
    # --------------------------------------------------
    def clear_assignment(self, ride_id):
        """
        Remove assignment marker.
        Useful for testing/reset scenarios.
        """

        if ride_id in self.assignments:
            del self.assignments[ride_id]

    # ==================================================
    # READ OPERATIONS
    # ==================================================

    # --------------------------------------------------
    # GET ATTEMPT COUNT
    # --------------------------------------------------
    def get_attempts(self, ride_id):
        return self.attempts.get(ride_id, 0)

    # --------------------------------------------------
    # GET RETRY COUNT
    # --------------------------------------------------
    def get_retries(self, ride_id):
        return self.retries.get(ride_id, 0)

    # --------------------------------------------------
    # CHECK ASSIGNMENT STATUS
    # --------------------------------------------------
    def is_assigned(self, ride_id):
        return self.assignments.get(ride_id, False)

    # ==================================================
    # SNAPSHOTS / REPORTING
    # ==================================================

    # --------------------------------------------------
    # IMMUTABLE SNAPSHOT
    # --------------------------------------------------
    def snapshot(self):
        """
        Return immutable metrics snapshot.
        """

        return {
            "attempts": dict(self.attempts),
            "retries": dict(self.retries),
            "assignments": dict(self.assignments),
        }

    # --------------------------------------------------
    # SINGLE RIDE SUMMARY
    # --------------------------------------------------
    def summary(self, ride_id):
        """
        Compact metrics summary for one ride.
        """

        return {
            "ride_id": ride_id,
            "attempts": self.get_attempts(ride_id),
            "retries": self.get_retries(ride_id),
            "assigned": self.is_assigned(ride_id),
        }

    # --------------------------------------------------
    # GLOBAL SUMMARY
    # --------------------------------------------------
    def global_summary(self):
        """
        Aggregate metrics across all rides.
        """

        total_rides = len(
            set(
                list(self.attempts.keys()) +
                list(self.retries.keys()) +
                list(self.assignments.keys())
            )
        )

        total_attempts = sum(self.attempts.values())
        total_retries = sum(self.retries.values())
        total_assignments = len(
            [r for r, assigned in self.assignments.items() if assigned]
        )

        return {
            "total_rides": total_rides,
            "total_attempts": total_attempts,
            "total_retries": total_retries,
            "total_assignments": total_assignments,
        }

    # ==================================================
    # RESET OPERATIONS
    # ==================================================

    # --------------------------------------------------
    # RESET ALL METRICS
    # --------------------------------------------------
    def reset(self):
        """
        Clear all metrics.

        Intended for:
        - tests
        - local debugging
        - isolated replay runs
        """

        self.attempts.clear()
        self.retries.clear()
        self.assignments.clear()

    # --------------------------------------------------
    # RESET SINGLE RIDE
    # --------------------------------------------------
    def reset_ride(self, ride_id):
        """
        Reset metrics for one ride only.
        """

        self.attempts.pop(ride_id, None)
        self.retries.pop(ride_id, None)
        self.assignments.pop(ride_id, None)

    # ==================================================
    # DEBUG / REPRESENTATION
    # ==================================================

    def __repr__(self):

        return (
            "DispatchMetrics("
            f"attempts={len(self.attempts)}, "
            f"retries={len(self.retries)}, "
            f"assignments={len(self.assignments)}"
            ")"
        )