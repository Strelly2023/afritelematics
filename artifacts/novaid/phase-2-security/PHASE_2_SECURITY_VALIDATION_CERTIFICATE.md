# NovaID Phase 2 Security Validation Certificate

**Decision:** PASS
**Certification time:** 2026-07-30 05:53 AEST
**Source baseline:** `9cbb1d8b656119c39bbd047e6f9c299de51e0f61` plus the working-tree remediations listed below
**Severity gate:** HIGH and CRITICAL

## Executive conclusion

The Phase 2 security gate is complete within the declared scope. Cryptographic
key rotation is enforced in production, dependency and container scans were
produced and reviewed, targeted penetration tests passed, and every HIGH or
CRITICAL finding discovered by these scans was remediated and revalidated.

This certificate does not claim an external third-party penetration test or
coverage of LOW/MEDIUM findings. It certifies the repository's targeted,
architecture-led adversarial validation and the HIGH/CRITICAL release gate.

## 1. Cryptographic key management

Production startup now requires a versioned signing-key registry and an explicit
active key identifier. A legacy single signing key is rejected in production.
Issued JWTs carry a `kid`; validators select only registered keys and reject
unknown or retired identifiers. Rotation supports a controlled overlap window:
old and new tokens validate while both keys remain registered, and tokens signed
by the retired key fail immediately after removal.

Additional parser controls reject algorithm substitution, malformed encoding,
oversized tokens, invalid claim types, unsupported token versions, and invalid
key material.

## 2. Dependency and configuration scanning

Trivy 0.72.0 found five HIGH GitPython advisories and one HIGH Starlette
advisory in the pinned Python environment. GitPython was upgraded to 3.1.57 and
Starlette to 1.3.1, with secure minimums applied to all dependency declarations.
Three HIGH Dockerfile configuration findings were also corrected by enforcing
non-root execution and removing the unsafe package-install pattern.

The final dependency/configuration rescan reports **0 HIGH/CRITICAL
vulnerabilities** and **0 HIGH/CRITICAL misconfigurations**.

## 3. Container scanning

The original production image contained **113 HIGH/CRITICAL findings**. The
production Dockerfile was converted to a multi-stage Alpine build, build tools
were excluded from the runtime image, vulnerable packaging tools were removed,
and runtime execution was assigned to UID/GID `10001:10001`.

Final image:

- Tag: `production-afritech-api:phase2-remediated`
- Image ID: `sha256:f384097ee185f7d3918fee29bca45dcef22d795dbb82efc27cb4e08232458e65`
- HIGH/CRITICAL findings, including unfixed: **0**
- Embedded secret findings: **0**
- Non-root runtime/import smoke test: **PASS**

## 4. Penetration testing

The targeted adversarial regression suite executed 57 tests with 57 passing.
Coverage includes key rotation and retirement attacks, unknown-key selection,
JWT algorithm substitution, malformed and oversized tokens, claim type
confusion, token-version downgrade, cross-tenant access, authorization bypass,
startup fail-closed behavior, and WebAuthn boundary abuse.

## 5. Remediation verification

| Gate | Before | After | Result |
|---|---:|---:|---|
| Dependency HIGH/CRITICAL | 6 | 0 | PASS |
| Docker configuration HIGH/CRITICAL | 3 | 0 | PASS |
| Container HIGH/CRITICAL | 113 | 0 | PASS |
| Container secrets | 0 | 0 | PASS |
| Adversarial tests | — | 57/57 | PASS |
| Focused Ruff | — | clean | PASS |
| Diff integrity | — | clean | PASS |

Machine-readable results and evidence hashes are recorded in
`phase-2-security-results.json`; raw scanner reports are retained under `raw/`.

## Architecture approval

**Phase 2 – Security Validation: APPROVED**

The working-tree remediation is eligible for review and commit. Deployment
approval remains subject to the normal release process, environment-specific
secret provisioning, and operational change control.
