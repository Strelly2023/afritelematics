# Logout model

Selected logout revokes the session and active refresh families transactionally, then publishes shared revocation. Repeated logout returns a deterministic no-op. Logout-all revokes all active identity sessions/families and increments security version. API mounting and refresh race verification remain incomplete.
