# afritech/runtime/invariant_enforcement.py

from afritech.constitution.compiled.invariants_index import (
    I1_EXPLICIT_INPUT_BOUNDARY,
    I2_EXPLICIT_OUTPUT_BOUNDARY,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_EXECUTION,
    I5_REPLAY_REQUIRED,
    I9_CLOSED_WORLD,
)

# ✅ explicit declaration for verifier
ENFORCED_INVARIANTS = {
    I1_EXPLICIT_INPUT_BOUNDARY,
    I2_EXPLICIT_OUTPUT_BOUNDARY,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_EXECUTION,
    I5_REPLAY_REQUIRED,
    I9_CLOSED_WORLD,
}