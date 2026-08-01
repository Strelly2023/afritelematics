# NovaID two-process final certificate

LOCAL VERIFICATION ONLY — NOT PRODUCTION CERTIFICATION — NOT GA CERTIFICATION.

Processes on 58101 and 58102 shared PostgreSQL/Redis with distinct memory, pools, clients, and IDs. Cross-process register/verify/auth/MFA, validation, refresh, logout, and access/refresh rejection passed. The expanded step-up/password/reset/restart sequence remains incomplete.
