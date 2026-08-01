# NovaID authentication flow

Tenant and normalized identifier resolve an active identity, membership, and credential. Password verification produces only a `PENDING_MFA` session. Correct purpose-bound OTP consumption activates it and issues one plaintext refresh token while persisting only its domain-separated hash. External failures remain generic.
