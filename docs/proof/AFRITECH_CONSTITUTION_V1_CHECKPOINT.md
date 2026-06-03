# AfriTech Constitution v1.0 Checkpoint

## Status

Checkpoint status: PASSED

Constitution status: documented, parseable, validated, and preserved inside a green governance/runtime system.

This checkpoint records the first verified state where AfriTech Constitution v1.0 exists as non-binding doctrine and the repository validation surface is green.

## Checkpoint Metadata

| Field | Value |
| --- | --- |
| Date UTC | 2026-05-28T21:47:22Z |
| Git HEAD | ff8181a |
| Worktree state | contains uncommitted changes |
| Constitution doctrine | afritech/constitution/AFRITECH_CONSTITUTION_V1.md |
| Constitution machine spec | afritech/constitution/AFRITECH_CONSTITUTION_V1.yaml |
| Constitution validator | afritech/ci/afritech_constitution_v1_validator.py |

Git HEAD is recorded as the local ancestry anchor. Because the worktree contains uncommitted changes, this checkpoint is an evidence snapshot of the current workspace state, not a clean release tag.

## Verification Results

| Verification Surface | Command | Result |
| --- | --- | --- |
| Full test suite | `python3 -m pytest` | 1378 passed |
| Constitutional pipeline | `python3 -m afritech.ci.constitutional_pipeline` | Constitutional closure achieved |
| Validator sweep | all `afritech/ci/*validator.py` modules | 98 passed, 0 failed |
| Constitution v1 validator | `python3 -m afritech.ci.afritech_constitution_v1_validator` | PASSED |

## Known Warnings

The full test suite reports two warnings from `afritech/api/contracts/validator.py`:

- `jsonschema.RefResolver` is deprecated.
- The warning is non-blocking and does not affect Constitution v1.0 validation, runtime closure, or governance validator status.

## What Changed

- Added AfriTech Constitution v1.0 as human-readable doctrine.
- Added a machine-readable Constitution v1.0 YAML source.
- Added a non-binding Constitution v1.0 validator.
- Restored compatibility between legacy `afritech.api.auth` and package-style `afritech.api.auth.jwt_device_auth` imports.
- Added a composed implementation registry loader for the split registry model.
- Updated registry-facing tests to consume the composed registry.
- Filled reserved ADR placeholders so YAML gap validation is closed.
- Adjusted semantic coverage validation to accept both runtime invariant IDs and governance invariant IDs.
- Added cross-system proof Merkle/signature compatibility helpers and a valid sample proof test.
- Updated CI filename, identity, partial/planned audit, and YAML gap surfaces until the validator sweep passed.

## What Was Not Changed

- AfriTech Constitution v1.0 was not bound into active runtime enforcement.
- Existing constitutional runtime authority was not replaced.
- Existing canonical registry authority was not redefined by the Constitution v1.0 artifact.
- AfriProgramming, AfriCPPT, AfriTPPS, and AFRIPower were not promoted to executable surfaces by this checkpoint.
- The Constitution remains validated doctrine, not an enforcement-bound source of runtime truth.

## Interpretation

This checkpoint preserves the distinction between doctrine and enforcement:

```text
Constitution v1.0
  -> documented
  -> parseable
  -> structurally validated
  -> test-preserved
  -> pipeline-preserved
  -> validator-preserved
  -> not yet runtime-bound
```

The repository is therefore in an admissible state for the next governance step.

## Next Admissible Step

Bind AfriTech Constitution v1.0 to declared executable surfaces.

The binding step should be separate from this checkpoint and should introduce explicit governance artifacts before runtime enforcement, for example:

```text
ADR -> INVARIANT -> RULE -> BINDING -> GUARD -> CI
```

No future binding should bypass AfriCPPT governance or silently promote Constitution v1.0 doctrine into runtime truth.
