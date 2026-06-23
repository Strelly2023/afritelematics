"""Enterprise audit compliance report for NovaTech core platform packets."""

from __future__ import annotations

from typing import Any, Mapping

from afritech.core_platform.signing import sign_packet


def build_enterprise_audit_report(packet: Mapping[str, Any]) -> dict[str, object]:
    signature = sign_packet(packet)
    controls = [
        {
            "framework": "ISO 27001",
            "control": "A.5.15 Access control",
            "status": "mapped",
            "evidence": "NovaID identity and NovaPower authority decision",
        },
        {
            "framework": "ISO 27001",
            "control": "A.8.15 Logging",
            "status": "mapped",
            "evidence": "NovaTrust replayable proof packet",
        },
        {
            "framework": "SOC 2",
            "control": "Security CC6",
            "status": "mapped",
            "evidence": "Tenant-bound action and role/scope checks",
        },
        {
            "framework": "Regulator",
            "control": "Payment traceability",
            "status": "mapped",
            "evidence": "NovaPay receipt and provider reference",
        },
    ]
    return {
        "report": "NovaTech Enterprise Audit Compliance Report",
        "classification": "ISO_SOC2_REGULATOR_READY_PACKET",
        "controls": controls,
        "signature": signature.canonical(),
        "tamper_evident": True,
        "execution_authority": False,
        "ga_boundary": [
            "Requires production signing key custody",
            "Requires managed PostgreSQL backups",
            "Requires external auditor acceptance workflow",
        ],
    }
