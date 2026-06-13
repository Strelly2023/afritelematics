"""Validate AfriPay ledger reconciliation and audit-grade financial proof."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from django.conf import settings
import django

from afritech.afripay.operations import create_payment_sync
from afritech.afripay.reconciliation import (
    FinancialIntegrityError,
    LedgerReconciliationEngine,
    ReconciliationSnapshot,
)


SAMPLE_REFERENCE = "proof.financial.integrity.001"


def validate() -> ReconciliationSnapshot:
    report = run_financial_integrity_proof()
    if not report.verified:
        raise FinancialIntegrityError(report.mismatches)
    return report


def run_financial_integrity_proof() -> ReconciliationSnapshot:
    models = _afripay_models()
    if not models.Transaction.objects.filter(reference=SAMPLE_REFERENCE).exists():
        create_payment_sync(
            {
                "payer_id": "proof.payer",
                "payer_country": "AU",
                "payer_kyc_level": 2,
                "payee_id": "proof.payee",
                "payee_country": "BI",
                "payee_kyc_level": 2,
                "amount": "60.00",
                "currency": "AUD",
                "reference": SAMPLE_REFERENCE,
                "preference": "balanced",
            }
        )
    return LedgerReconciliationEngine().reconcile_transaction(SAMPLE_REFERENCE)


def main() -> int:
    try:
        report = validate()
    except FinancialIntegrityError as exc:
        print(f"AfriPay financial integrity validation FAILED: {exc}")
        return 1
    print(
        "AfriPay financial integrity validation PASSED: "
        f"report_hash={report.report_hash()} ledger_hash={report.ledger_hash}"
    )
    return 0


def _afripay_models():
    from importlib import import_module

    if not settings.configured:
        base_dir = Path(__file__).resolve().parents[2]
        django_app_dir = base_dir / "afriride_system" / "django_app"
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        if str(django_app_dir) not in sys.path:
            sys.path.insert(0, str(django_app_dir))
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            "afriride_system.django_app.config.settings",
        )
        django.setup()
    return import_module("afriride_system.django_app.apps.afripay.models")


if __name__ == "__main__":
    raise SystemExit(main())
