"""
AfriTech Runtime Guards

PURPOSE:
--------
Enforce strict separation between:
- Operational Runtime (adaptive, async, orchestration, locality)
- Constitutional Core (replay, admissibility, identity, witnesses)

CORE LAW:
---------
Operational layers MAY optimize execution.
Operational layers MAY NOT define or mutate truth.

This module acts as:
- semantic firewall
- execution boundary validator
- runtime integrity enforcement layer
"""

# ============================================================
# 🚫 FORBIDDEN AUTHORITY FIELDS
# ============================================================

FORBIDDEN_AUTHORITY_FIELDS = {
    "replay_semantics",
    "admissibility",
    "identity",
    "witness",
    "ontology",
    "invariant_semantics",
}

# ============================================================
# ✅ ALLOWED RUNTIME FIELDS
# ============================================================

ALLOWED_RUNTIME_FIELDS = {
    "retry_limit",
    "batch_size",
    "timeout",
    "transport_mode",
    "observability_level",
    "routing_hint",
}


# ============================================================
# ✅ POLICY GUARD
# ============================================================

def enforce_policy_boundary(policy: dict):
    """
    Ensures runtime policies do NOT attempt to modify
    constitutional truth definitions.
    """

    if not isinstance(policy, dict):
        raise TypeError("Policy must be a dictionary")

    forbidden = FORBIDDEN_AUTHORITY_FIELDS.intersection(policy.keys())

    if forbidden:
        raise Exception(
            f"[GUARD VIOLATION] Illegal policy mutation: {forbidden}"
        )


# ============================================================
# ✅ RUNTIME SCOPE GUARD
# ============================================================

def enforce_runtime_scope(policy: dict):
    """
    Ensures runtime policies remain within allowed operational scope.
    """

    unknown = set(policy.keys()) - ALLOWED_RUNTIME_FIELDS - FORBIDDEN_AUTHORITY_FIELDS

    if unknown:
        raise Exception(
            f"[GUARD WARNING] Unknown runtime policy fields: {unknown}"
        )


# ============================================================
# ✅ EVENT INTEGRITY GUARD (STRICT MODE)
# ============================================================

def enforce_event_integrity(original_event: dict, processed_event: dict):
    """
    Ensures NO mutation occurred during runtime execution.

    STRICT MODE:
    - event must remain identical
    """

    if original_event != processed_event:
        raise Exception(
            "[GUARD VIOLATION] Event mutated during runtime execution"
        )


# ============================================================
# ✅ CANONICAL ENVELOPE GUARD
# ============================================================

REQUIRED_ENVELOPE_FIELDS = ("event_id", "payload", "timestamp")


def enforce_canonical_envelope(envelope: dict):
    """
    Ensures the event structure is canonical.
    """

    if not isinstance(envelope, dict):
        raise TypeError("Envelope must be a dictionary")

    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in envelope:
            raise Exception(
                f"[GUARD VIOLATION] Missing canonical field: {field}"
            )


# ============================================================
# ✅ SEMANTIC CONSISTENCY GUARD
# ============================================================

def enforce_semantic_consistency(before: dict, after: dict):
    """
    Ensures semantic meaning has not changed.
    """

    if before.get("payload") != after.get("payload"):
        raise Exception(
            "[GUARD VIOLATION] Payload semantic mutation detected"
        )

    if before.get("event_id") != after.get("event_id"):
        raise Exception(
            "[GUARD VIOLATION] Event identity mismatch"
        )


# ============================================================
# ✅ ASYNC SAFETY GUARD
# ============================================================

def enforce_async_safety(before: dict, after: dict):
    """
    Ensures async execution does not alter payload.
    """

    if before.get("payload") != after.get("payload"):
        raise Exception(
            "[GUARD VIOLATION] Async processing mutated payload"
        )


# ============================================================
# ✅ LOCALITY SAFETY GUARD
# ============================================================

def enforce_locality_safety(event: dict, selected_node: str):
    """
    Ensures locality decisions do not alter data.
    """

    if not isinstance(selected_node, str):
        raise Exception(
            "[GUARD VIOLATION] Invalid node selection"
        )

    if "payload" not in event:
        raise Exception(
            "[GUARD VIOLATION] Event missing payload"
        )


# ============================================================
# ✅ ORCHESTRATION SAFETY GUARD
# ============================================================

FORBIDDEN_ORCHESTRATION_ACTIONS = {
    "modify_payload",
    "rewrite_event",
    "mutate_event",
}


def enforce_orchestration_safety(event: dict, decisions: dict):
    """
    Ensures orchestration does NOT mutate events.
    """

    if not isinstance(decisions, dict):
        raise TypeError("Orchestration decisions must be dict")

    violations = FORBIDDEN_ORCHESTRATION_ACTIONS.intersection(decisions.keys())

    if violations:
        raise Exception(
            f"[GUARD VIOLATION] Illegal orchestration action: {violations}"
        )


# ============================================================
# ✅ ADAPTIVE BOUNDARY GUARD
# ============================================================

def enforce_adaptive_limits(adaptation: dict):
    """
    Ensures adaptive output does NOT cross into truth domain.
    """

    if not isinstance(adaptation, dict):
        raise TypeError("Adaptation must be a dictionary")

    forbidden = FORBIDDEN_AUTHORITY_FIELDS.intersection(adaptation.keys())

    if forbidden:
        raise Exception(
            f"[GUARD VIOLATION] Adaptive mutation forbidden: {forbidden}"
        )


# ============================================================
# ✅ EXECUTION ISOLATION GUARD
# ============================================================

FORBIDDEN_TARGETS = {
    "replay_engine",
    "validators",
    "identity_core",
}


def prevent_truth_layer_access(caller: str, target: str):
    """
    Prevent runtime layers from accessing constitutional core directly.
    """

    if target in FORBIDDEN_TARGETS:
        raise Exception(
            f"[GUARD VIOLATION] {caller} cannot access {target}"
        )


# ============================================================
# ✅ REPLAY DETERMINISM GUARD
# ============================================================

def enforce_replay_determinism(outputs: list):
    """
    Ensures identical outputs across runs.
    """

    if not outputs:
        return

    baseline = outputs[0]

    for output in outputs[1:]:
        if output != baseline:
            raise Exception(
                "[GUARD VIOLATION] Replay determinism violated"
            )


# ============================================================
# ✅ MASTER GUARD (PIPELINE ENTRY POINT)
# ============================================================

def enforce_runtime_integrity(
    original_event: dict,
    processed_event: dict,
    policy: dict,
    adaptation: dict = None,
):
    """
    Master guard checkpoint for runtime pipeline.
    """

    enforce_policy_boundary(policy)
    enforce_runtime_scope(policy)

    enforce_event_integrity(original_event, processed_event)
    enforce_semantic_consistency(original_event, processed_event)
    enforce_async_safety(original_event, processed_event)

    if adaptation:
        enforce_adaptive_limits(adaptation)

    return True


# ============================================================
# ✅ DEBUG / TRACE
# ============================================================

def debug_guard_log(message: str):
    """
    Lightweight debug logging.
    """

    print(f"[AFRITECH-GUARD] {message}")
# ============================================================
# ✅ EXECUTION ISOLATION GUARD (IMPROVED)
# ============================================================

RUNTIME_LAYERS = {
    "adaptive",
    "orchestration",
    "async_runtime",
    "locality",
}

CONSTITUTIONAL_COMPONENTS = {
    "replay_engine",
    "validators",
    "identity_core",
    "admissibility",
    "ontology",
}


def prevent_truth_layer_access(caller: str, target: str):
    """
    Prevent runtime layers from accessing constitutional core.

    RULE:
    runtime → core = forbidden
    """

    if caller in RUNTIME_LAYERS and target in CONSTITUTIONAL_COMPONENTS:
        raise Exception(
            f"[GUARD VIOLATION] Runtime layer '{caller}' "
            f"cannot access constitutional component '{target}'"
        )