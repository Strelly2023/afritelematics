# RC Freeze Blockers

Current release-baseline state:

- Branch: `feature/product-factory-enterprise-sdlc`
- Current tested commit: `5f451f2d8b1363b977603d76509389c35b60cb2e`
- Baseline validator: `LOCAL_BASELINE_PASS`
- SBOM bundle: generated and verified
- Checksums: generated and verified
- Reproducibility report: `IDENTICAL` for `novacodepro_portal`

No immutable RC tag has been created on this pass.

## Blocker 1

- Blocker ID: `production_signing_material_unavailable`
- Requirement: signed immutable release candidate
- Observed state: the release manifest is intentionally marked `signature_status: EXTERNALLY_BLOCKED`; no approved production signing material is available in this environment.
- Evidence:
  - `artifacts/ga-readiness/release/manifests/release-manifest.json`
  - `artifacts/ga-readiness/release/baseline/validation-report.json`
  - `scripts/release/generate_release_manifest.py`
- Owner type: external approval / security operations
- Required input:
  - approved production signing identity
  - secure key custody location
  - operator authorization to sign the release manifest
- Exact command:

```bash
uvicorn afritech.api.novacodepro_platform_api:app --host 127.0.0.1 --port 8000
curl -sS -X POST \
  http://127.0.0.1:8000/releases/novatech-2026.1.0/sign \
  -H 'Content-Type: application/json' \
  -d '{"signature":"<approved-production-signature>"}'
```

- Acceptance criteria:
  - release signing request succeeds using approved production credentials
  - release manifest records a real signature
  - signature verification succeeds
  - immutable RC tag is created only after the signed manifest is validated

## Decision

RC freeze remains blocked until the signing input above is available and verified.
