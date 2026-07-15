# Database Primary Failure Runbook

Detection: writable primary readiness failure or replication alert.
Immediate actions: enter read-only degradation, confirm managed failover, pause non-critical writes, keep SOS path active.
Verification: transaction test, migration status, outbox availability, replica lag.
Evidence: failover event, RTO/RPO measurement, database logs.
