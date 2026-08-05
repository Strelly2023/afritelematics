# NL-001 blocker — runtime boundary governance artifact drift

Resolution status: recovery procedure authorized. Nine unrelated untracked Python modules must be checksum-preserved outside the scan scope while the governed artifact is regenerated and the NL-001 commit is created.

## Failing command

`git commit -m "feat(novalogistics): establish logistics domain foundation"`

Exit result: non-zero; the commit was rejected by the repository pre-commit architecture pipeline.

Relevant error:

```text
Running guard_runtime_boundary_governance...
RuntimeBoundaryGovernanceGuardError: runtime boundary scan artifact drift detected
FAILURE: guard_runtime_boundary_governance: non-zero exit code: 1
Commit blocked: canonical constitutional pipeline violation
```

## State and affected files

The NL-001 additions under `afritech/novalogistics`, `afritech/tests/novalogistics`, and `artifacts/novalogistics` remain uncommitted. They are isolated from the dirty-tree files recorded in the baseline. No NL-002 work has begun.

Focused tests pass (11), broader Python logistics compatibility tests pass (50), public-web compatibility tests pass (5), compilation passes, and `git diff --check` passes. The failing gate is the generated runtime-boundary scan consistency check.

## Safe remediation options

1. Run the repository's documented runtime-boundary scan artifact generator, inspect its exact diff, and include only the NovaLogistics-derived governance update after confirming it does not absorb pre-existing dirty changes.
2. If the drift originates from pre-existing changes in `afritech/architecture/anchor_indexer.py` or `services/administration/app_registry.py`, complete or isolate that work first, then rerun the NL-001 commit gate.
3. Have the repository governance owner regenerate and certify the runtime-boundary artifact, then resume NL-001 from the existing focused-test checkpoint.

No bypass (`--no-verify`) was used because the program forbids disabling policy gates.
