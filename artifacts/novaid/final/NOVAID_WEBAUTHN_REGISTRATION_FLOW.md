# NovaID WebAuthn registration flow

An authenticated identity requests options; the service persists a hashed challenge and returns RP, user, algorithm, authenticator-selection, timeout, attestation, and exclusion data. Verification atomically consumes the challenge, validates the response, and persists credential/authenticator/binding/attestation records. Invalid responses receive a generic ceremony error.
