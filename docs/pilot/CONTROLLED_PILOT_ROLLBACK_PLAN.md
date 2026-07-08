# Controlled Pilot Rollback Plan

Rollback is required for any blocking issue that affects safety, trust, payment integrity, or release governance.

## Triggers

- Payment-safety regression.
- Unauthorized access.
- Evidence or receipt corruption.
- Reconciliation failure.
- Severe monitoring outage.

## Rollback actions

1. Disable controlled-pilot access.
2. Disable pilot payment approvals.
3. Revoke affected devices.
4. Pause APK distribution.
5. Preserve logs and evidence.
6. Notify support and operations.

## Recovery

- Restore only after root cause is identified and fixed.
- Re-run the controlled pilot validation set before resuming.
