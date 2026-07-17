# NovaRide Android Signing Credential Recovery

NovaRide Android release signing requires the historical certificate recorded in
`docs/mobile/release/release_lineage.yaml`.

Required runtime secrets:

- `AFRIRIDE_ANDROID_KEYSTORE_PATH`
- `AFRIRIDE_ANDROID_KEYSTORE_PASSWORD`
- `AFRIRIDE_ANDROID_KEY_ALIAS`
- `AFRIRIDE_ANDROID_KEY_PASSWORD`
- `SIGNING_SECRET_PROVIDER`

Approved secret providers:

- GitHub Actions Secrets
- 1Password
- Bitwarden
- AWS Secrets Manager
- Vault
- macOS Keychain

Current local v2 escrow services:

- `AFRIRIDE_ANDROID_KEYSTORE_PATH_V2`
- `AFRIRIDE_ANDROID_KEYSTORE_PASSWORD_V2`
- `AFRIRIDE_ANDROID_KEY_ALIAS_V2`
- `AFRIRIDE_ANDROID_KEY_PASSWORD_V2`

To run a local release command with the Keychain-backed v2 credentials:

```bash
scripts/mobile/run_with_keychain_android_signing.sh scripts/mobile/release_health_check.sh
```

Do not store Android signing passwords in Git, plaintext `.env` files,
`key.properties`, shell history, or release artifact directories.

Recovery order:

1. Check the primary password manager entry.
2. Check GitHub Actions or the active CI secret store.
3. Check encrypted machine backups for the original keystore and password record.
4. Contact the person who generated the keystore.
5. If the original key cannot be recovered, follow `emergency_release.md`.

Before any release build, run:

```bash
scripts/mobile/release_health_check.sh
```

The health check must verify the certificate SHA-256:

```text
5bd809c088bb1634af02f2880fba44d13f732635fcb2eff74aa49ca8f47f9d61
```
