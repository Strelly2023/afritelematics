# AFRIPAY_KEY_MANAGEMENT_REVIEW

## Generation
- keys are generated from a controlled signing subsystem
- evidence signing uses RSA private keys

## Rotation
- rotation is versioned and traceable
- verifiers can validate new public keys independently

## Revocation
- revoked keys must be excluded from verification trust lists
- verification packages must record the active public key fingerprint

## Storage
- private keys remain non-public
- public keys may be exported for independent validation

## Backup
- backups preserve recovery capability
- backup material must not weaken control boundaries

## Recovery
- recovery must restore signing capability without changing artifact history

## Destruction
- retired private keys must be destroyed or rendered inaccessible
- destruction events must be auditable
