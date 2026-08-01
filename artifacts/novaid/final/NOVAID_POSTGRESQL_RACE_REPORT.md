# PostgreSQL race report

Real row locking, optimistic conflict and rollback are verified. The complete multi-worker registration, OTP, refresh, reset, logout and lockout race matrix was not executed, so concurrency remains PARTIAL.
