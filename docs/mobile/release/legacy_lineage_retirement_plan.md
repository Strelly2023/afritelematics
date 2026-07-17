# NovaRide Legacy Android Lineage Retirement Plan

This plan applies only if the historical signing credentials for the legacy
NovaRide Android release lineage cannot be recovered.

Legacy fingerprint:

```text
117f77e5e461c6a111ae83d7b32cf84aa76f5be3287692795f54a229bccd12cc
```

## Decision Gate

Before retiring the legacy lineage, complete and record one final recovery
cycle against:

- GitHub Actions Secrets
- Historical CI/CD environments
- 1Password, Bitwarden, Apple Passwords, or other password managers
- Encrypted backups
- Previous developer machines
- Original build workstation
- Release runbooks outside Git

If recovery fails, update `release_lineage.yaml`:

- Set `legacy.active=false`
- Set `legacy.status=retired-unrecoverable`
- Set `v2.active=true`
- Replace `v2.certificate_sha256` with the generated v2 fingerprint
- Set `v2.status=production`
- Set `v2.custody_status=escrowed`

Current v2 fingerprint:

```text
5bd809c088bb1634af02f2880fba44d13f732635fcb2eff74aa49ca8f47f9d61
```

## Pilot User Migration

Message:

```text
NovaRide requires a one-time reinstall due to Android signing key migration.
```

Steps:

1. Back up any local records that are not already server-synced.
2. Uninstall the legacy APK.
3. Install the NovaRide v2 APK.
4. Sign in again.
5. Confirm driver availability or rider account status.

## Google Play Recommendation

For future store deployment, enable Google Play App Signing. Treat the local
keystore as an upload key where possible so upload credentials can be rotated
without losing the store signing lineage.
