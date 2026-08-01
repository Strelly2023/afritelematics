# Tenant policy distribution certificate

LOCAL VERIFICATION ONLY — NOT PHYSICAL-DEVICE CERTIFICATION — NOT FIDO CERTIFICATION — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

Policy updates transactionally create distributed events; consumers invalidate the versioned Redis key. Read-through caching exists. Full cross-process staleness re-evaluation is partial.
