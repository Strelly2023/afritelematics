# Session administration model

Users can list only tenant-and-identity-bound sessions, revoke a selected own session idempotently, and logout all. Revocation updates durable sessions/families before publishing to the configured revocation store. Logout-all increments durable security version.
