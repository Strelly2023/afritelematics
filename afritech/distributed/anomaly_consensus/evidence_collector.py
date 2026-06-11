from __future__ import annotations

from afritech.distributed.anomaly_consensus.trust_verifier import verify_report


def collect_evidence(
    reports: tuple[dict[str, object], ...],
) -> dict[str, object]:
    verified = tuple(report for report in reports if verify_report(report))
    rejected = tuple(report for report in reports if not verify_report(report))
    return {
        "verified_reports": verified,
        "rejected_reports": rejected,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


__all__ = ["collect_evidence"]
