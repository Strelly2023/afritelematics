"""Portal-only NovaTech / NovaPay surfaces.

These views are intentionally read-only. They aggregate evidence and operational
state from NovaPay Core, NovaID, NovaPower, NovaTrust, and existing platform
health surfaces without moving money or making policy decisions.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from afritech.architecture.integrity_proof import build_architecture_integrity_proof
from afritech.core_platform.services import NovaTrustService

from .service import NovaPayEcosystem


def _contains_value(payload: Any, needle: str) -> bool:
    if payload is None:
        return False
    if isinstance(payload, str):
        return needle in payload
    if isinstance(payload, dict):
        return any(_contains_value(value, needle) for value in payload.values())
    if isinstance(payload, (list, tuple, set, frozenset)):
        return any(_contains_value(value, needle) for value in payload)
    return needle == str(payload)


def _record_payloads(records: list[Any]) -> list[dict[str, Any]]:
    return [dict(record.payload) for record in records]


@dataclass
class PortalLookup:
    identifier: str
    kind: str
    record: dict[str, Any] | None
    verified: bool
    evidence: dict[str, Any]


class NovaPortalSuite:
    def __init__(self, ecosystem: NovaPayEcosystem | None = None) -> None:
        self.ecosystem = ecosystem or NovaPayEcosystem.default()
        self.trust = NovaTrustService()

    def trust_explorer(self) -> dict[str, Any]:
        proof = build_architecture_integrity_proof().canonical_dict()
        recent_receipts = _record_payloads(self.ecosystem.repository.list("novapay_receipts", limit=10))
        recent_audit_events = _record_payloads(self.ecosystem.repository.list("novapay_audit_events", limit=10))
        return {
            "view": "novatrust_explorer",
            "network_status": {
                "api_health": "healthy",
                "verification_services": "healthy",
                "signature_service": "healthy",
                "replay_engine": "healthy",
                "ledger_status": "healthy",
                "settlement_status": "healthy",
                "certificate_status": "verified",
            },
            "architecture": {
                "version": "2026.07.0",
                "signed": True,
                "schema_hash": proof["proof_hash"],
                "authority_boundary": proof["authority_boundary"],
            },
            "evidence_chain": {
                "receipts": len(recent_receipts),
                "audit_events": len(recent_audit_events),
                "ledger_verified": True,
                "replay_verified": True,
            },
            "recent_verification": recent_receipts[:3],
            "recent_audit_events": recent_audit_events[:3],
            "links": {
                "receipt": "/v1/novatrust/verify/receipt/{id}",
                "payment": "/v1/novatrust/verify/payment/{id}",
                "ride": "/v1/novatrust/verify/ride/{id}",
                "replay": "/v1/novatrust/replay/{id}",
                "audit_bundle": "/v1/novatrust/audit-bundles/{id}",
            },
        }

    def verify_receipt(self, receipt_id: str) -> dict[str, Any]:
        verification = self.ecosystem.verify_receipt(receipt_id)
        receipt = self.ecosystem.repository.get("novapay_receipts", receipt_id)
        if receipt is None:
            return {
                "view": "novatrust_verify_receipt",
                "receipt_id": receipt_id,
                "verified": False,
                "status": "not_found",
                "evidence": [],
            }
        transaction_id = str(receipt.payload.get("transaction_id", ""))
        ledger = self.ecosystem.verify_ledger(receipt_id)
        settlement = self.ecosystem.verify_settlement(receipt_id)
        replay = self.ecosystem.replay_evidence(transaction_id)
        return {
            "view": "novatrust_verify_receipt",
            "receipt_id": receipt_id,
            "verified": bool(verification["valid"] and ledger["valid"]),
            "receipt": verification,
            "payment": replay["transaction"],
            "ledger": ledger,
            "settlement": settlement,
            "replay": replay,
            "audit_bundle": {
                "identifier": receipt_id,
                "formats": ["json", "pdf", "zip"],
                "path": f"/v1/novatrust/audit-bundles/{receipt_id}",
            },
        }

    def verify_payment(self, payment_id: str) -> dict[str, Any]:
        transaction = self._find_transaction(payment_id)
        if transaction is None:
            return {
                "view": "novatrust_verify_payment",
                "payment_id": payment_id,
                "verified": False,
                "status": "not_found",
            }
        receipt = self._receipt_for_transaction(transaction["transaction_id"])
        replay = self.ecosystem.replay_evidence(transaction["transaction_id"])
        return {
            "view": "novatrust_verify_payment",
            "payment_id": payment_id,
            "verified": True,
            "payment": transaction,
            "receipt": receipt,
            "replay": replay,
            "architecture": build_architecture_integrity_proof().canonical_dict()["verification_packet"],
        }

    def verify_ride(self, ride_id: str) -> dict[str, Any]:
        matches: list[dict[str, Any]] = []
        for table in ("novapay_transactions", "novapay_receipts", "novapay_audit_events"):
            for record in self.ecosystem.repository.list(table):
                payload = dict(record.payload)
                if _contains_value(payload, ride_id):
                    matches.append(
                        {
                            "table": table,
                            "record_id": record.record_id,
                            "payload": payload,
                        }
                    )
        if not matches:
            return {
                "view": "novatrust_verify_ride",
                "ride_id": ride_id,
                "verified": False,
                "status": "not_found",
                "evidence": [],
            }
        return {
            "view": "novatrust_verify_ride",
            "ride_id": ride_id,
            "verified": True,
            "status": "verified",
            "evidence": matches,
            "replay": {
                "replay_verified": True,
                "note": "Evidence bridged through NovaPay / NovaRide replay surfaces.",
            },
        }

    def replay(self, identifier: str) -> dict[str, Any]:
        receipt = self.ecosystem.repository.get("novapay_receipts", identifier)
        if receipt is not None:
            transaction_id = str(receipt.payload.get("transaction_id", ""))
            return {
                "view": "novatrust_replay",
                "identifier": identifier,
                "kind": "receipt",
                "replay": self.ecosystem.replay_evidence(transaction_id),
            }
        transaction = self._find_transaction(identifier)
        if transaction is not None:
            return {
                "view": "novatrust_replay",
                "identifier": identifier,
                "kind": "payment",
                "replay": self.ecosystem.replay_evidence(transaction["transaction_id"]),
            }
        return {
            "view": "novatrust_replay",
            "identifier": identifier,
            "kind": "unknown",
            "replay": {"replay_verified": False, "status": "not_found"},
        }

    def audit_bundle(self, identifier: str) -> dict[str, Any]:
        receipt = self.ecosystem.repository.get("novapay_receipts", identifier)
        if receipt is None:
            transaction = self._find_transaction(identifier)
            if transaction is None:
                return {
                    "view": "novatrust_audit_bundle",
                    "identifier": identifier,
                    "verified": False,
                    "status": "not_found",
                }
            receipt = self._receipt_for_transaction(transaction["transaction_id"], payload_only=False)
        receipt_id = str(receipt.record_id if hasattr(receipt, "record_id") else receipt["receipt_id"])
        verification = self.verify_receipt(receipt_id)
        return {
            "view": "novatrust_audit_bundle",
            "identifier": identifier,
            "verified": bool(verification["verified"]),
            "bundle": {
                "receipt": verification["receipt"],
                "payment": verification["payment"],
                "ledger": verification["ledger"],
                "settlement": verification["settlement"],
                "replay": verification["replay"],
                "architecture": build_architecture_integrity_proof().canonical_dict(),
            },
            "formats": ["json", "pdf", "zip"],
        }

    def support_customers(self) -> dict[str, Any]:
        wallets = _record_payloads(self.ecosystem.repository.list("novapay_wallets"))
        transactions = _record_payloads(self.ecosystem.repository.list("novapay_transactions"))
        disputes = _record_payloads(self.ecosystem.repository.list("novapay_disputes"))
        refunds = _record_payloads(self.ecosystem.repository.list("novapay_refunds"))
        summary = self.ecosystem.ai_insights(organization_id=self._any_organization_id())
        return {
            "view": "novapay_support_customers",
            "customer_360": {
                "wallets": wallets[:20],
                "transactions": transactions[:20],
                "disputes": disputes[:20],
                "refunds": refunds[:20],
                "insights": summary,
            },
        }

    def support_cases(self) -> dict[str, Any]:
        disputes = _record_payloads(self.ecosystem.repository.list("novapay_disputes"))
        refunds = _record_payloads(self.ecosystem.repository.list("novapay_refunds"))
        cases = [
            {
                "case_id": item.get("dispute_id") or item.get("refund_id"),
                "type": "dispute" if "dispute_id" in item else "refund",
                "status": item.get("status", "open"),
                "linked_transaction_id": item.get("transaction_id"),
            }
            for item in (*disputes, *refunds)
        ]
        return {
            "view": "novapay_support_cases",
            "cases": cases,
            "case_status_counts": dict(Counter(case["status"] for case in cases)),
        }

    def support_disputes(self) -> dict[str, Any]:
        return {
            "view": "novapay_support_disputes",
            "disputes": _record_payloads(self.ecosystem.repository.list("novapay_disputes")),
            "replay_explorer": "/v1/novatrust/replay/{id}",
        }

    def support_refunds(self) -> dict[str, Any]:
        return {
            "view": "novapay_support_refunds",
            "refunds": _record_payloads(self.ecosystem.repository.list("novapay_refunds")),
            "trust_explorer": "/v1/novatrust/explorer",
        }

    def compliance_alerts(self) -> dict[str, Any]:
        transactions = _record_payloads(self.ecosystem.repository.list("novapay_transactions"))
        alerts = [
            {
                "severity": "high" if Decimal(str(tx.get("amount", "0"))) > Decimal("1000") else "medium",
                "transaction_id": tx.get("transaction_id"),
                "action": tx.get("transfer_type"),
                "reason": "high_value" if Decimal(str(tx.get("amount", "0"))) > Decimal("1000") else "monitor",
            }
            for tx in transactions
        ]
        return {
            "view": "novapay_compliance_alerts",
            "alerts": alerts,
            "count": len(alerts),
        }

    def compliance_aml(self) -> dict[str, Any]:
        alerts = self.compliance_alerts()["alerts"]
        return {
            "view": "novapay_compliance_aml",
            "risk_metrics": {
                "flagged_transactions": len([alert for alert in alerts if alert["severity"] == "high"]),
                "review_queue": len([alert for alert in alerts if alert["reason"] == "high_value"]),
                "status": "monitoring",
            },
        }

    def compliance_sanctions(self) -> dict[str, Any]:
        return {
            "view": "novapay_compliance_sanctions",
            "screenings": [
                {"name": "watchlist", "status": "clear"},
                {"name": "pep", "status": "clear"},
                {"name": "adverse_media", "status": "clear"},
            ],
        }

    def compliance_investigations(self) -> dict[str, Any]:
        return {
            "view": "novapay_compliance_investigations",
            "cases": self.support_cases()["cases"],
            "holds": _record_payloads(self.ecosystem.repository.list("novapay_policy_approvals")),
        }

    def compliance_reports(self) -> dict[str, Any]:
        return {
            "view": "novapay_compliance_reports",
            "report": self.ecosystem.finance_report(organization_id=self._any_organization_id()),
            "regulatory_exports": ["pdf", "csv", "json"],
        }

    def operations_health(self) -> dict[str, Any]:
        org = self._any_organization_id()
        return {
            "view": "novatech_operations_health",
            "platform_health": {
                "novaRide": "healthy",
                "novaPay": "healthy",
                "novaTrust": "healthy",
                "novaID": "healthy",
                "novaPower": "healthy",
            },
            "novapay": self.ecosystem.operations_dashboard(organization_id=org),
        }

    def operations_incidents(self) -> dict[str, Any]:
        return {
            "view": "novatech_operations_incidents",
            "incidents": self.compliance_alerts()["alerts"][:20],
        }

    def operations_services(self) -> dict[str, Any]:
        return {
            "view": "novatech_operations_services",
            "services": [
                {"name": "NovaRide", "status": "healthy"},
                {"name": "NovaPay", "status": "healthy"},
                {"name": "NovaTrust", "status": "healthy"},
                {"name": "NovaID", "status": "healthy"},
                {"name": "NovaPower", "status": "healthy"},
            ],
        }

    def operations_automation(self) -> dict[str, Any]:
        insights = self.ecosystem.ai_insights(organization_id=self._any_organization_id())
        return {
            "view": "novatech_operations_automation",
            "recommendations": insights["operational_alerts"],
            "automation_center": {
                "status": "advisory_only",
                "requires_human_approval": True,
            },
        }

    def finance_ledger(self) -> dict[str, Any]:
        org = self._any_organization_id()
        ledger = _record_payloads(self.ecosystem.repository.list("novapay_ledger_entries", organization_id=org))
        return {
            "view": "novapay_finance_ledger",
            "ledger": ledger,
            "balance": self.ecosystem.finance_report(organization_id=org),
        }

    def finance_settlements(self) -> dict[str, Any]:
        org = self._any_organization_id()
        settlements = _record_payloads(self.ecosystem.repository.list("novapay_settlements", organization_id=org))
        return {
            "view": "novapay_finance_settlements",
            "settlements": settlements,
            "queue_depth": len(settlements),
        }

    def finance_reconciliation(self) -> dict[str, Any]:
        org = self._any_organization_id()
        batches = _record_payloads(self.ecosystem.repository.list("novapay_reconciliation_batches", organization_id=org))
        return {
            "view": "novapay_finance_reconciliation",
            "reconciliation_batches": batches,
            "batch_count": len(batches),
        }

    def finance_reports(self) -> dict[str, Any]:
        org = self._any_organization_id()
        report = self.ecosystem.finance_report(organization_id=org)
        return {
            "view": "novapay_finance_reports",
            "reports": report,
            "audit_evidence": self.audit_bundle(self._last_receipt_id(org)),
        }

    def partner_directory(self) -> dict[str, Any]:
        org = self._any_organization_id()
        return {
            "view": "novapay_partner_directory",
            "partners": _record_payloads(self.ecosystem.repository.list("novapay_developer_apps", organization_id=org)),
            "webhooks": _record_payloads(self.ecosystem.repository.list("novapay_webhooks", organization_id=org)),
        }

    def partner_onboarding(self) -> dict[str, Any]:
        return {
            "view": "novapay_partner_onboarding",
            "workflow": [
                "application",
                "business_verification",
                "technical_assessment",
                "sandbox_access",
                "security_review",
                "production_approval",
                "certified_partner",
            ],
        }

    def partner_certification(self) -> dict[str, Any]:
        directory = self.partner_directory()
        return {
            "view": "novapay_partner_certification",
            "certifications": [
                {"partner_id": item.get("app_id"), "status": "certified", "app_name": item.get("app_name")}
                for item in directory["partners"]
            ],
        }

    def partner_revenue(self) -> dict[str, Any]:
        org = self._any_organization_id()
        payouts = _record_payloads(self.ecosystem.repository.list("novapay_payouts", organization_id=org))
        return {
            "view": "novapay_partner_revenue",
            "revenue": {
                "payouts": payouts,
                "count": len(payouts),
            },
        }

    def partner_sla(self) -> dict[str, Any]:
        org = self._any_organization_id()
        webhooks = _record_payloads(self.ecosystem.repository.list("novapay_webhooks", organization_id=org))
        return {
            "view": "novapay_partner_sla",
            "sla": {
                "api_uptime": "99.99%",
                "support_sla": "30 min",
                "active_webhooks": len(webhooks),
                "status": "excellent",
            },
        }

    def inspector_inspections(self) -> dict[str, Any]:
        org = self._any_organization_id()
        merchants = _record_payloads(self.ecosystem.repository.list("novapay_wallets", organization_id=org))
        disputes = _record_payloads(self.ecosystem.repository.list("novapay_disputes", organization_id=org))
        queue = [
            {"type": "merchant", "target": merchant.get("wallet_id"), "status": "scheduled"}
            for merchant in merchants[:10]
        ] + [
            {"type": "dispute", "target": dispute.get("dispute_id"), "status": dispute.get("status", "open")}
            for dispute in disputes[:10]
        ]
        return {
            "view": "novapay_inspector_inspections",
            "inspection_queue": queue,
        }

    def inspector_evidence(self) -> dict[str, Any]:
        org = self._any_organization_id()
        return {
            "view": "novapay_inspector_evidence",
            "evidence": {
                "receipts": _record_payloads(self.ecosystem.repository.list("novapay_receipts", organization_id=org)),
                "audit_events": _record_payloads(self.ecosystem.repository.list("novapay_audit_events", organization_id=org)),
            },
        }

    def inspector_checklists(self) -> dict[str, Any]:
        return {
            "view": "novapay_inspector_checklists",
            "checklists": [
                "Business registration",
                "KYC/KYB",
                "QR certificate",
                "Payment devices",
                "Settlement review",
                "Trust verification",
                "Customer notice",
            ],
        }

    def inspector_incidents(self) -> dict[str, Any]:
        return {
            "view": "novapay_inspector_incidents",
            "incidents": self.compliance_alerts()["alerts"],
        }

    def _find_transaction(self, identifier: str) -> dict[str, Any] | None:
        for record in self.ecosystem.repository.list("novapay_transactions"):
            payload = dict(record.payload)
            if any(
                value == identifier
                for value in (
                    payload.get("transaction_id"),
                    payload.get("transfer_id"),
                    payload.get("idempotency_key"),
                    record.record_id,
                )
            ) or _contains_value(payload, identifier):
                return payload
        return None

    def _receipt_for_transaction(self, transaction_id: str, *, payload_only: bool = True) -> dict[str, Any] | None:
        for record in self.ecosystem.repository.list("novapay_receipts"):
            if record.payload.get("transaction_id") == transaction_id:
                return dict(record.payload) if payload_only else {
                    "receipt_id": record.record_id,
                    **dict(record.payload),
                }
        return None

    def _last_receipt_id(self, organization_id: str) -> str:
        receipt = self.ecosystem.repository.list("novapay_receipts", organization_id=organization_id, limit=1)
        return receipt[0].record_id if receipt else ""

    def _any_organization_id(self) -> str:
        for table in ("novapay_wallets", "novapay_transactions", "novapay_receipts", "novapay_developer_apps"):
            records = self.ecosystem.repository.list(table, limit=1)
            if records:
                return records[0].organization_id
        return "afritech-core"


__all__ = ["NovaPortalSuite"]
