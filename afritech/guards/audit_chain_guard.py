from afritech.audit.chain_validator import ChainValidationError
from afritech.runtime.replay.audit_log import AuditLog


class AuditChainGuard:

    @staticmethod
    def validate_pre_insert(entry, previous_entry):
        """
        Guard-level enforcement (ADR-0004 + ADR-0013)

        IMPORTANT:
        - Must NOT mutate state
        - Only validates preconditions
        """

        # ✅ Forward-only chain enforcement
        if previous_entry:
            if entry.previous_hash != previous_entry.entry_hash:
                raise ChainValidationError("FORWARD_LINK_BROKEN")

        # ✅ Entry must be valid
        if entry.status != "VALID":
            raise ChainValidationError("INVALID_STATUS")

        # ✅ Epoch must be monotonic (ADR-0002)
        if previous_entry:
            if entry.epoch < previous_entry.epoch:
                raise ChainValidationError("NON_MONOTONIC_EPOCH")

        return True


# =====================================================
# ✅ TEMPORAL VALIDATION UTILITIES (PHASE 3)
# =====================================================

def detect_temporal_violations(audit_logs):
    """
    Detects violations of temporal determinism:
    - epoch monotonicity
    - timestamp ordering
    """

    violations = []

    prev_epoch = None
    prev_timestamp = None

    for entry in audit_logs:

        # ✅ Epoch check (strictly increasing)
        if prev_epoch is not None and entry.epoch <= prev_epoch:
            violations.append({
                "entry_id": entry.id,
                "reason": "NON_MONOTONIC_EPOCH"
            })

        # ✅ Timestamp ordering check
        if prev_timestamp is not None and entry.timestamp < prev_timestamp:
            violations.append({
                "entry_id": entry.id,
                "reason": "TIMESTAMP_REGRESSION"
            })

        prev_epoch = entry.epoch
        prev_timestamp = entry.timestamp

    return violations


# =====================================================
# ✅ NORMALIZATION / REPAIR UTILITIES
# =====================================================

def recompute_epochs(audit_logs, save=True):
    """
    Recomputes epoch sequence based on timestamp ordering.

    ✅ Deterministic
    ✅ Used ONLY for repair (not runtime)
    """

    sorted_logs = sorted(audit_logs, key=lambda x: (x.timestamp, x.id))

    for i, entry in enumerate(sorted_logs):
        entry.epoch = i + 1

        if save:
            entry.save(update_fields=["epoch"])

    return sorted_logs


def invalidate_entries(audit_logs, violations):
    """
    Marks invalid entries without deleting data.

    ✅ Preferred over deletion
    ✅ Preserves audit history (ADR‑0013 principle)
    """

    violation_map = {v["entry_id"]: v["reason"] for v in violations}

    for entry in audit_logs:
        if entry.id in violation_map:
            entry.status = "INVALIDATED"
            entry.invalid_reason = violation_map[entry.id]
            entry.save(update_fields=["status", "invalid_reason"])


# =====================================================
# ✅ OPTIONAL: LOAD + VALIDATE FULL CHAIN
# =====================================================

def load_and_detect_violations(queryset=None):
    """
    Utility to load logs and detect temporal issues.

    Example usage:
        violations = load_and_detect_violations()
    """

    if queryset is None:
        queryset = AuditLog.objects.all()

    logs = list(queryset.order_by("timestamp", "id"))
    return detect_temporal_violations(logs)
