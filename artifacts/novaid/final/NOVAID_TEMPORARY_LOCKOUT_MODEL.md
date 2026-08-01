# Temporary lockout model

Failures within the configured window increment a tenant-bound counter. Threshold creates a bounded temporary lock checked before password verification. Reset removes applicable state. External errors remain generic; another tenant is unaffected.
