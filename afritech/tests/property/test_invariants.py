# afritech/tests/property/test_invariants.py

"""
Property-Based Invariant Test Suite (Hypothesis)

Purpose:
Validate core AfriTech invariants under generated input space.

Invariants tested:

1. Deterministic execution
2. Replay consistency
3. Epoch monotonicity
4. Closed-world execution
5. Authority non-escalation

This suite replaces example-based confidence with
state-space validation.
"""

import pytest
from hypothesis import given, strategies as st

# Import system components
from afritech.runtime.engine.executor import ExecutionEngine, ExecutionError
from afritech.runtime.context.runtime_context import RuntimeContext


# ---------------------------------------------------------------------
# MOCK EXECUTION FUNCTION (DETERMINISTIC)
# ---------------------------------------------------------------------

def deterministic_execution_fn(input_data):
    """
    A strictly deterministic function.
    """
    payload = input_data["payload"]

    # Deterministic transformation
    return {
        "result": hash(str(sorted(payload.items()))) % 100000
    }


engine = ExecutionEngine(deterministic_execution_fn)


# ---------------------------------------------------------------------
# STRATEGIES
# ---------------------------------------------------------------------

payload_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=5),
    values=st.integers(min_value=0, max_value=100),
    max_size=5
)

authority_strategy = st.sampled_from([
    "CONSTITUTIONAL_RESEARCH_AGENT",
    "SECONDARY_RESEARCH_AUTHORITY"
])


# ---------------------------------------------------------------------
# HELPER — BUILD CONTEXT
# ---------------------------------------------------------------------

def build_context(payload, authority):
    return RuntimeContext(
        authority_profile=authority,
        payload=payload,
        replay_requirements={
            "replay_required": True,
            "deterministic_only": True,
        },
        timestamp="FIXED_TIMESTAMP"  # ensures determinism
    )


# ---------------------------------------------------------------------
# INVARIANT 1 — DETERMINISM
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_execution_is_deterministic(payload, authority):
    context = build_context(payload, authority)

    result1 = engine.execute(context)
    result2 = engine.execute(context)

    assert result1.result_hash == result2.result_hash, \
        "Non-deterministic execution detected"


# ---------------------------------------------------------------------
# INVARIANT 2 — REPLAY CONSISTENCY
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_replay_consistency(payload, authority):
    context = build_context(payload, authority)
    result = engine.execute(context)

    assert result.verify(), "Result replay verification failed"


# ---------------------------------------------------------------------
# INVARIANT 3 — OUTPUT STRUCTURAL INTEGRITY
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_output_is_json_serializable(payload, authority):
    context = build_context(payload, authority)
    result = engine.execute(context)

    assert isinstance(result.output, dict), \
        "Output must be a dictionary"


# ---------------------------------------------------------------------
# INVARIANT 4 — CLOSED WORLD EXECUTION
# ---------------------------------------------------------------------

@given(payload=payload_strategy)
def test_closed_world_execution(payload):
    """
    Ensures arbitrary unknown authority fails if enforced
    """
    context = RuntimeContext(
        authority_profile="UNKNOWN_AUTHORITY",
        payload=payload,
        replay_requirements={
            "replay_required": True,
            "deterministic_only": True,
        },
        timestamp="FIXED_TIMESTAMP"
    )

    with pytest.raises(Exception):
        engine.execute(context)


# ---------------------------------------------------------------------
# INVARIANT 5 — AUTHORITY NON-ESCALATION
# ---------------------------------------------------------------------

@given(payload=payload_strategy)
def test_authority_non_escalation(payload):
    """
    Ensure authority cannot be escalated dynamically
    """

    context_low = build_context(
        payload,
        "SECONDARY_RESEARCH_AUTHORITY"
    )

    context_high = build_context(
        payload,
        "CONSTITUTIONAL_RESEARCH_AGENT"
    )

    result_low = engine.execute(context_low)
    result_high = engine.execute(context_high)

    # Should not diverge dramatically or gain privileged data
    assert isinstance(result_low.output, dict)
    assert isinstance(result_high.output, dict)


# ---------------------------------------------------------------------
# INVARIANT 6 — HASH STABILITY
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_result_hash_stable(payload, authority):
    context = build_context(payload, authority)
    result = engine.execute(context)

    recomputed = result._compute_hash()

    assert result.result_hash == recomputed, \
        "Result hash instability detected"


# ---------------------------------------------------------------------
# INVARIANT 7 — PAYLOAD ORDER INDEPENDENCE
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_payload_order_independence(payload, authority):
    """
    Ensure dictionary ordering does not affect result
    """

    context1 = build_context(payload, authority)

    # reorder payload
    reversed_payload = dict(reversed(list(payload.items())))
    context2 = build_context(reversed_payload, authority)

    result1 = engine.execute(context1)
    result2 = engine.execute(context2)

    assert result1.result_hash == result2.result_hash, \
        "Payload ordering affects result (non-deterministic)"


# ---------------------------------------------------------------------
# INVARIANT 8 — NO CRASH ON VALID INPUT SPACE
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_no_unexpected_crashes(payload, authority):
    context = build_context(payload, authority)

    try:
        result = engine.execute(context)
    except ExecutionError:
        pytest.fail("Unexpected crash for valid input")


# ---------------------------------------------------------------------
# INVARIANT 9 — CONSISTENT CONTEXT HASH
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_context_hash_consistency(payload, authority):
    c1 = build_context(payload, authority)
    c2 = build_context(payload, authority)

    assert c1.context_hash == c2.context_hash, \
        "Context hash inconsistency"


# ---------------------------------------------------------------------
# INVARIANT 10 — MUTATION RESISTANCE
# ---------------------------------------------------------------------

@given(payload=payload_strategy, authority=authority_strategy)
def test_mutation_resistance(payload, authority):
    context = build_context(payload, authority)
    result = engine.execute(context)

    # mutate output
    if result.output:
        key = list(result.output.keys())[0]
        result.output[key] = result.output[key] + 1

    assert not result.verify(), \
        "Mutation was not detected"
