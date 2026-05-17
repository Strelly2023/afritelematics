# ============================================================
# AUTO-GENERATED — DO NOT EDIT
# ============================================================

from __future__ import annotations


# ============================================================
# SCHEMA
# ============================================================

SCHEMA_VERSION = "afritech.constitution.invariants.index.v3"
IR_SCHEMA = "afritech.constitution.invariants.ir.v3"
PROJECTION_MODEL = "runtime_subset_projection"

DETERMINISTIC = True
REPLAY_SAFE = True
CLOSED_WORLD_ALIGNED = True


# ============================================================
# RUNTIME INVARIANTS (STRICT PROJECTION OF IR)
# ============================================================

I1_EXPLICIT_INPUT_BOUNDARY = "I1_EXPLICIT_INPUT_BOUNDARY"
I2_EXPLICIT_OUTPUT_BOUNDARY = "I2_EXPLICIT_OUTPUT_BOUNDARY"
I3_NO_SILENT_MUTATION = "I3_NO_SILENT_MUTATION"
I4_DETERMINISTIC_EXECUTION = "I4_DETERMINISTIC_EXECUTION"
I5_REPLAY_REQUIRED = "I5_REPLAY_REQUIRED"
I9_CLOSED_WORLD = "I9_CLOSED_WORLD"


# ============================================================
# CANONICAL RUNTIME PROJECTION (ORDERED)
# ============================================================

RUNTIME_INVARIANT_IDS = [
    I1_EXPLICIT_INPUT_BOUNDARY,
    I2_EXPLICIT_OUTPUT_BOUNDARY,
    I3_NO_SILENT_MUTATION,
    I4_DETERMINISTIC_EXECUTION,
    I5_REPLAY_REQUIRED,
    I9_CLOSED_WORLD,
]


# ============================================================
# VALIDATION GUARANTEES
# ============================================================

INVARIANT_COUNT = len(RUNTIME_INVARIANT_IDS)

# ✅ exact count
assert INVARIANT_COUNT == 6, "Invalid runtime invariant count"

# ✅ uniqueness
assert len(set(RUNTIME_INVARIANT_IDS)) == INVARIANT_COUNT, \
    "Duplicate runtime invariant IDs detected"

# ✅ deterministic ordering
assert sorted(RUNTIME_INVARIANT_IDS) == RUNTIME_INVARIANT_IDS, \
    "Runtime invariants must be sorted"

# ✅ structural guarantees
assert DETERMINISTIC is True
assert REPLAY_SAFE is True
assert CLOSED_WORLD_ALIGNED is True


# ============================================================
# HELPERS (SAFE RUNTIME USE)
# ============================================================

def list_runtime() -> list[str]:
    return list(RUNTIME_INVARIANT_IDS)


def is_valid(invariant_id: str) -> bool:
    return invariant_id in RUNTIME_INVARIANT_IDS


def validate(invariant_id: str) -> None:
    if invariant_id not in RUNTIME_INVARIANT_IDS:
        raise ValueError(f"Invalid runtime invariant: {invariant_id}")


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "SCHEMA_VERSION",
    "IR_SCHEMA",
    "PROJECTION_MODEL",
    "DETERMINISTIC",
    "REPLAY_SAFE",
    "CLOSED_WORLD_ALIGNED",
    "INVARIANT_COUNT",
    "RUNTIME_INVARIANT_IDS",
    "list_runtime",
    "is_valid",
    "validate",
    "I1_EXPLICIT_INPUT_BOUNDARY",
    "I2_EXPLICIT_OUTPUT_BOUNDARY",
    "I3_NO_SILENT_MUTATION",
    "I4_DETERMINISTIC_EXECUTION",
    "I5_REPLAY_REQUIRED",
    "I9_CLOSED_WORLD",
]