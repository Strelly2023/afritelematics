from afritech.audit.hash_engine import HashEngine


class ChainValidationError(Exception):
    pass


class ChainValidator:
    """
    Enforces audit chain integrity according to ADR‑0013.

    Guarantees:
    - deterministic hash correctness
    - forward-only linkage
    - immutable history verification
    - replay-safe validation
    """

    # =====================================================
    # ✅ FULL CHAIN VALIDATION
    # =====================================================

    @staticmethod
    def validate_chain(audit_logs):
        """
        Validates the entire audit log chain.

        Rules enforced:
        - Each entry_hash must match recomputed hash
        - Each previous_hash must match prior entry's hash
        - Genesis entry must have no previous_hash
        - No broken links allowed
        """

        if not audit_logs:
            return True

        previous_entry = None

        for index, entry in enumerate(audit_logs):

            # -------------------------------------------------
            # ✅ 1. GENESIS VALIDATION
            # -------------------------------------------------
            if previous_entry is None:
                if entry.previous_hash is not None:
                    raise ChainValidationError(
                        f"INVALID_GENESIS_ENTRY at index={index}, entry_id={entry.id}"
                    )

            # -------------------------------------------------
            # ✅ 2. LINK VALIDATION
            # -------------------------------------------------
            if previous_entry is not None:
                if entry.previous_hash != previous_entry.entry_hash:
                    raise ChainValidationError(
                        f"BROKEN_CHAIN at index={index}, entry_id={entry.id}"
                    )

            # -------------------------------------------------
            # ✅ 3. HASH RECOMPUTATION (CRITICAL)
            # -------------------------------------------------
            expected_hash = HashEngine.compute_hash(
                previous_hash=entry.previous_hash,
                payload=entry.payload
            )

            if entry.entry_hash != expected_hash:
                raise ChainValidationError(
                    f"HASH_MISMATCH at index={index}, entry_id={entry.id}"
                )

            # -------------------------------------------------
            # ✅ 4. OPTIONAL STATUS FILTER (if used)
            # -------------------------------------------------
            if hasattr(entry, "status") and entry.status != "VALID":
                raise ChainValidationError(
                    f"INVALID_ENTRY_STATUS at index={index}, entry_id={entry.id}"
                )

            previous_entry = entry

        return True

    # =====================================================
    # ✅ APPEND VALIDATION (WRITE-TIME)
    # =====================================================

    @staticmethod
    def validate_append(previous_entry, new_entry):
        """
        Validates a new entry before insertion.

        Ensures:
        - correct previous_hash linkage
        - valid deterministic entry_hash
        """

        # -------------------------------------------------
        # ✅ 1. EXPECTED PREVIOUS HASH
        # -------------------------------------------------
        expected_previous_hash = (
            previous_entry.entry_hash if previous_entry else None
        )

        if new_entry.previous_hash != expected_previous_hash:
            raise ChainValidationError("INVALID_PREVIOUS_HASH")

        # -------------------------------------------------
        # ✅ 2. HASH VALIDATION
        # -------------------------------------------------
        expected_hash = HashEngine.compute_hash(
            previous_hash=new_entry.previous_hash,
            payload=new_entry.payload
        )

        if new_entry.entry_hash != expected_hash:
            raise ChainValidationError("INVALID_ENTRY_HASH")

        return True
