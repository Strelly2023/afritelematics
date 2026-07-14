"""In-process API contract metrics with Prometheus text export."""

from __future__ import annotations

from collections import Counter


_contract_validations: Counter[tuple[str, str]] = Counter()
_breaking_changes: Counter[str] = Counter()
_signature_failures: Counter[str] = Counter()


def record_contract_validation(*, operation_id: str, result: str) -> None:
    _contract_validations[(operation_id, result)] += 1


def record_breaking_change(*, domain: str) -> None:
    _breaking_changes[domain] += 1


def record_signature_failure(*, domain: str) -> None:
    _signature_failures[domain] += 1


def prometheus_metrics() -> str:
    lines = [
        "# HELP novatech_api_contract_validations_total API response contract validations.",
        "# TYPE novatech_api_contract_validations_total counter",
    ]
    for (operation_id, result), count in sorted(_contract_validations.items()):
        lines.append(f'novatech_api_contract_validations_total{{operation_id="{operation_id}",result="{result}"}} {count}')
    lines.extend(
        [
            "# HELP novatech_api_breaking_changes_total API breaking changes detected.",
            "# TYPE novatech_api_breaking_changes_total counter",
        ]
    )
    for domain, count in sorted(_breaking_changes.items()):
        lines.append(f'novatech_api_breaking_changes_total{{domain="{domain}"}} {count}')
    lines.extend(
        [
            "# HELP novatech_api_signature_failures_total API publication signature failures.",
            "# TYPE novatech_api_signature_failures_total counter",
        ]
    )
    for domain, count in sorted(_signature_failures.items()):
        lines.append(f'novatech_api_signature_failures_total{{domain="{domain}"}} {count}')
    static_zero_metrics = (
        "novatech_api_contract_violations_total",
        "novatech_api_deprecated_calls_total",
        "novatech_api_publication_verifications_total",
        "novatech_sdk_generation_failures_total",
        "novatech_partner_certification_failures_total",
    )
    for metric in static_zero_metrics:
        lines.append(f"# TYPE {metric} counter")
        lines.append(f'{metric}{{result="none"}} 0')
    return "\n".join(lines) + "\n"
