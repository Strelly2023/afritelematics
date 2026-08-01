# NovaID FIDO2 credential model

Credentials use unique binary IDs and COSE public keys verified by the standards library. Active, suspended, revoked, compromised, and deleted states are represented. Terminal states cannot return to active. Tenant ownership is checked on every lookup and transition.
