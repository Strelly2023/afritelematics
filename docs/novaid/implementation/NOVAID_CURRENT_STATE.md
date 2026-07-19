# NovaID current state

Baseline: `c03f9f8d7de992402663e7a24c7c2f1b214fca91` on `feature/novacodepro-unified-platform` (2026-07-18).

The repository contains a SQLite-backed NovaID ecosystem service, FastAPI routes, five React Native applications, public-web presentation, tests, Android build outputs, identity SDK types, monitoring material, and release manifests. Existing methods cover identity records, consent, devices, sessions, passkey metadata, KYC/KYB abstractions, risk summaries, OAuth client metadata, SAML metadata, and role checks.

This is not evidence of a production IAM implementation. In particular, metadata registration is not WebAuthn ceremony verification; generic records are not a normalized identity database; deterministic KYC decisions are not external-provider certification; and an APK's presence is not mobile security or store certification.

This execution added isolated, testable password, purpose-bound OTP, rotating refresh-family, reuse-detection, and session-revocation primitives. They are reference in-process adapters pending transactional PostgreSQL/Redis integration.

Unrelated pre-existing working-tree changes were preserved.
