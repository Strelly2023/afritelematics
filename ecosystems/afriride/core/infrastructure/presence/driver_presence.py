class DriverPresenceService:
    """
    Tracks live driver availability.

    Responsibilities:
    - online/offline state
    - availability filtering
    - busy state (assignment lifecycle)
    """

    def __init__(self):
        self.online = set()
        self.busy = set()

    # --------------------------------------------------
    # ONLINE / OFFLINE
    # --------------------------------------------------
    def mark_online(self, driver_id):
        self.online.add(driver_id)
        self.busy.discard(driver_id)

    def mark_offline(self, driver_id):
        self.online.discard(driver_id)
        self.busy.discard(driver_id)

    # --------------------------------------------------
    # BUSY / AVAILABLE
    # --------------------------------------------------
    def mark_busy(self, driver_id):
        if driver_id in self.online:
            self.busy.add(driver_id)

    def mark_available(self, driver_id):
        self.busy.discard(driver_id)

    # --------------------------------------------------
    # ✅ COMPATIBILITY ALIASES (IMPORTANT)
    # --------------------------------------------------
    def set_busy(self, driver_id):
        """
        Alias for mark_busy (for usecase compatibility)
        """
        self.mark_busy(driver_id)

    def set_available(self, driver_id):
        """
        Alias for mark_available
        """
        self.mark_available(driver_id)

    # --------------------------------------------------
    # AVAILABILITY CHECK
    # --------------------------------------------------
    def is_available(self, driver_id):
        return driver_id in self.online and driver_id not in self.busy

    # --------------------------------------------------
    # DEBUG SNAPSHOT
    # --------------------------------------------------
    def snapshot(self):
        return {
            "online": list(self.online),
            "busy": list(self.busy),
        }