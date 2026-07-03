from __future__ import annotations

from architecture_validator.remediation.model import AutoFix


class AutoFixEngine:
    """Generate bounded remediation plans from validator issues.

    The engine is deterministic by design. It does not call external AI services
    or modify source directly; execution safety is handled by FixExecutor.
    """

    def generate_fix(self, rule: str, issue: str) -> AutoFix:
        normalized = issue.lower()

        if "removed endpoint" in normalized or "removed method" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="api_fix",
                action="restore_or_version_endpoint",
                risk="high",
                safe_to_apply=False,
                detail="Restore the removed API surface or publish a major-version migration.",
            )

        if "removed field" in normalized or "type changed" in normalized or "removed schema" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="api_fix",
                action="restore_schema_compatibility",
                risk="high",
                safe_to_apply=False,
                detail="Restore the removed schema contract or move the breaking change to a major version.",
            )

        if "forbidden authority call" in normalized or "typescript authority violation" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="code_fix",
                action="route_through_novapower_policy",
                risk="high",
                safe_to_apply=False,
                detail="Replace direct authority access with a NovaPower-authorized backend request.",
            )

        if "solidity insecure pattern" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="contract_fix",
                action="remove_insecure_solidity_pattern",
                risk="high",
                safe_to_apply=False,
                detail="Remove unsafe Solidity constructs and re-run contract tests.",
            )

        if "missing required section" in normalized or "missing required normative fragment" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="doc_fix",
                action="prepare_architecture_doc_patch",
                risk="medium",
                safe_to_apply=False,
                detail="Prepare a documentation patch that preserves normative architecture wording.",
            )

        if "missing replay" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="replay_fix",
                action="restore_replay_validation_signal",
                risk="high",
                safe_to_apply=False,
                detail="Restore replay validation in the critical flow before execution can proceed.",
            )

        if "missing architectureanchorv2" in normalized or "anchorv2" in normalized:
            return AutoFix(
                rule=rule,
                issue=issue,
                fix_type="trust_fix",
                action="restore_anchor_v2_contract_stack",
                risk="high",
                safe_to_apply=False,
                detail="Restore ArchitectureAnchorV2 contract, ABI, and verification client wiring.",
            )

        return AutoFix(
            rule=rule,
            issue=issue,
            fix_type="manual_review",
            action="request_human_architecture_review",
            risk="manual",
            safe_to_apply=False,
            detail="Human approval required before remediation.",
        )
