# NovaRide Emergency Android Release Procedure

Use this only when the Android release signing credentials are missing or
suspected compromised.

## Path A: Recover Original Credentials

Recover the original keystore and passwords, then run:

```bash
scripts/mobile/release_health_check.sh
```

The release may continue only if the certificate fingerprint matches the
NovaRide release lineage registry.

## Path B: Recover Original Keystore From Backup

If `.secrets/novaride-release-keystore.jks` is not the historical keystore,
restore the historical keystore from encrypted backup and verify it before use.

## Path C: Create New Signing Lineage

Create a new keystore only after explicit release approval.

Use:

```bash
NOVARIDE_CONFIRM_NEW_LINEAGE=retire-legacy-and-create-v2 \
NOVARIDE_V2_KEYSTORE_PASSWORD=... \
NOVARIDE_V2_KEY_PASSWORD=... \
SIGNING_SECRET_PROVIDER=1password \
scripts/mobile/create_new_signing_lineage_v2.sh
```

Impact:

- Existing v2026.1.2 installs cannot upgrade to APKs signed by the new key.
- Public pilot users must reinstall.
- Play Store continuity may be broken for the existing package.
- The release lineage registry must record the new certificate as a separate
  lineage, not as a continuation of the old one.

Do not publish replacement APKs under the existing v2026.1.x update lineage
unless the historical fingerprint is verified.

Current NovaRide v2 lineage fingerprint:

```text
5bd809c088bb1634af02f2880fba44d13f732635fcb2eff74aa49ca8f47f9d61
```
