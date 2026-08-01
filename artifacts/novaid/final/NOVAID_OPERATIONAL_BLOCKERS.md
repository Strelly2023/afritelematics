# NovaID operational blockers

- PostgreSQL now runs locally, but direct service SQL and incomplete repository contracts prevent production certification.
- No production secrets/KMS, HA, restoration, failover, load/soak, penetration, or compliance evidence exists.

- Production PostgreSQL/Redis transactional adapters and migrations are not integrated.
- Production signing/encryption key providers and rotation evidence are unavailable.
- KYC/KYB, document, biometric, email, SMS, enterprise directory, SIEM, and federation credentials/test tenants are external blockers.
- WebAuthn has no certified ceremony implementation or physical-device evidence.
- Tenant-isolation, revocation propagation, PAM, federation, recovery, privacy fulfillment, DR, and resilience evidence is incomplete.
- Mobile signing inputs and store-review evidence are unavailable and must not be invented.
