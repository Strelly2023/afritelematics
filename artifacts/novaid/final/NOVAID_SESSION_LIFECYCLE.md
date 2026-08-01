# Session lifecycle

Password authentication creates `PENDING_MFA`; OTP upgrades it to `ACTIVE`; refresh replay moves it to `REVOKED`. Full idle expiry, step-up, compromise, listing, logout, and membership-wide revocation APIs remain incomplete.
