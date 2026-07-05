# NovaPay Agent App Pilot 002 Release Notes

This is a controlled pilot release package. It is not public production release readiness.

## Release identity

- App: NovaPay Agent App
- Release channel: controlled pilot
- Artifact class: Android APK
- Pilot identifier: `live_pilot_002`
- Target URL: `http://192.168.20.14:8765/novapay-agent-live_pilot_002-release.apk`
- SHA256: `94106a69870c8603b6b751459c14a17318e60def9d4c05a75b0d9c3a9b4a1043`

## App contract

- Surface only: yes
- NovaID authority: identity, authentication, KYC, device trust
- NovaPower authority: authorization, limits, compliance holds
- NovaTrust authority: receipts, signatures, replay, evidence
- NovaAI: advisory only
- NovaPay Core: money movement authority

## Required artifact

- `docs/mobile/release/novapay_agent_app_release_manifest.json`

## Validation status

Repository validation must pass before the APK is promoted for pilot use.

Required checks:

- `npm --prefix novapay_agent_app run typecheck`
- `npm --prefix novapay_agent_app test`
- `python -m compileall afritech afriride_system`
- `pytest -q -k "novapay and agent"`
- `python -m afritech.ci.four_gate_validator`
- `python -m afritech.guards.guard_runtime_boundary_governance --fail-on-drift`
- `python -m afritech.ci.secret_scan`
- `python -m afritech.ci.docs_link_validator`
- `git diff --check`

## Known operational dependencies

- Android release build must be generated from the NovaPay Agent App package.
- The APK must be published to the file server root that serves the `8765` endpoint.
- Production payment activation remains an external readiness requirement.
- App Store / Play Store production publication remains separate from controlled pilot release distribution.

## Pilot acceptance checklist

- [ ] NovaPay Agent App opens to the controlled-pilot home screen
- [ ] Primary actions render
- [ ] Send / receive / cash-in / cash-out remain governed previews
- [ ] Offline queue and sync status are visible
- [ ] Receipt signature state is visible
- [ ] Device trust is visible
- [ ] NovaAI is advisory only
- [ ] No payment execution logic exists in the UI

## Release classification

NovaPay Agent App UI/UX:

```text
Controlled Pilot Ready
```

Commercial cash operations:

```text
Pending operational approval
```

Live payment provider activation:

```text
External operational readiness requirement
```

Full production certification:

```text
Not achieved until all governance, security, runtime-boundary, and full validation gates pass.
```
