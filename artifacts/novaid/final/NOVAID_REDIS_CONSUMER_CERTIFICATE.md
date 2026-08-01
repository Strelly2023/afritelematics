# NovaID Redis consumer certificate

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

Schema validation, duplicate/stale/malformed isolation, version application, background start/stop, reconnect accounting, and database reconstruction are implemented and focused-tested. Consumer reconnect count in executed real recovery probe: 0 because the probe restarted Redis between publisher phases.
