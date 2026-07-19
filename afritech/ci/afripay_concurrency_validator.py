"""Validate AfriPay concurrency resilience under financial contention."""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from threading import Barrier
from importlib import import_module

from django.db import close_old_connections
from django.conf import settings
import django
import httpx

from afritech.afripay.money import Money
from afritech.afripay.persistence import PersistentIdempotencyStore, PersistentTreasuryStore
from afritech.afripay.tasks import process_provider_webhook_task
from afritech.afripay.providers_sandbox import FlutterwaveSandboxProvider, MpesaSandboxProvider
from afritech.afripay.models import PaymentRoute as DomainPaymentRoute


VALIDATOR_NAME = "AFRIPAY_CONCURRENCY_VALIDATOR"
IDEMPOTENCY_WORKERS = 20
TREASURY_WORKERS = 20
WEBHOOK_WORKERS = 20
PROVIDER_WORKERS = 20


@dataclass(frozen=True)
class ConcurrencyValidationReport:
    idempotency_winners: int
    treasury_successes: int
    webhook_event_ids: tuple[str, ...]
    flutterwave_references: tuple[str, ...]
    mpesa_references: tuple[str, ...]
    mismatches: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return not self.mismatches

    def canonical_dict(self) -> dict[str, object]:
        return {
            "validator": VALIDATOR_NAME,
            "idempotency_winners": self.idempotency_winners,
            "treasury_successes": self.treasury_successes,
            "webhook_event_ids": list(self.webhook_event_ids),
            "flutterwave_references": list(self.flutterwave_references),
            "mpesa_references": list(self.mpesa_references),
            "mismatches": list(self.mismatches),
            "verified": self.verified,
        }


def validate() -> ConcurrencyValidationReport:
    _afripay_models()
    mismatches: list[str] = []

    idempotency_winners = _idempotency_race()
    if idempotency_winners != 1:
        mismatches.append(f"idempotency winners expected 1, got {idempotency_winners}")

    treasury_successes = _treasury_race()
    if treasury_successes != TREASURY_WORKERS:
        mismatches.append(
            f"treasury successes expected {TREASURY_WORKERS}, got {treasury_successes}"
        )

    webhook_event_ids = _duplicate_webhook_storm()
    if len(set(webhook_event_ids)) != 1:
        mismatches.append("duplicate webhook storm produced inconsistent event ids")

    flutterwave_references, mpesa_references = _provider_retry_storm()
    if len(set(flutterwave_references)) != 1:
        mismatches.append("flutterwave retry storm produced inconsistent external references")
    if len(set(mpesa_references)) != 1:
        mismatches.append("mpesa retry storm produced inconsistent external references")

    report = ConcurrencyValidationReport(
        idempotency_winners=idempotency_winners,
        treasury_successes=treasury_successes,
        webhook_event_ids=tuple(webhook_event_ids),
        flutterwave_references=tuple(flutterwave_references),
        mpesa_references=tuple(mpesa_references),
        mismatches=tuple(mismatches),
    )
    if not report.verified:
        raise RuntimeError(", ".join(report.mismatches))
    return report


def main() -> int:
    try:
        report = validate()
    except Exception as exc:  # noqa: BLE001
        print(f"{VALIDATOR_NAME}: FAILED: {exc}")
        return 1
    print(
        f"{VALIDATOR_NAME}: PASS "
        f"idempotency={report.idempotency_winners} "
        f"treasury={report.treasury_successes} "
        f"webhook_events={len(set(report.webhook_event_ids))} "
        f"flutterwave_refs={len(set(report.flutterwave_references))} "
        f"mpesa_refs={len(set(report.mpesa_references))}"
    )
    return 0


def _idempotency_race() -> int:
    store = PersistentIdempotencyStore()
    key = "concurrency.idempotency.001"
    payload = {"amount": 25, "currency": "USD", "reference": "concurrency.idempotency.001"}
    barrier = Barrier(IDEMPOTENCY_WORKERS)

    def worker() -> bool:
        close_old_connections()
        barrier.wait()
        try:
            _, created = store.claim(key, payload)
            return created
        finally:
            close_old_connections()

    return sum(_run_workers(worker, IDEMPOTENCY_WORKERS))


def _treasury_race() -> int:
    models = _afripay_models()
    models.LiquidityPool.objects.filter(provider="validator", currency="USD").delete()
    models.LiquidityPool.objects.create(
        pool_id="pool.validator.usd",
        provider="validator",
        currency="USD",
        balance=Decimal("100.00"),
        reserved=Decimal("0.00"),
        low_watermark=Decimal("10.00"),
    )

    store = PersistentTreasuryStore()
    barrier = Barrier(TREASURY_WORKERS)

    def worker() -> bool:
        close_old_connections()
        barrier.wait()
        try:
            store.reserve("validator", "USD", Decimal("5.00"))
            return True
        finally:
            close_old_connections()

    successes = sum(_run_workers(worker, TREASURY_WORKERS))
    pool = models.LiquidityPool.objects.get(provider="validator", currency="USD")
    if pool.reserved != Decimal("100.00") or pool.balance != Decimal("100.00"):
        raise RuntimeError("treasury final state is not fully reserved and conserved")
    return successes


def _duplicate_webhook_storm() -> tuple[str, ...]:
    models = _afripay_models()
    aggregate_id = "webhook.storm.001"
    models.EventRecord.objects.filter(aggregate_id=aggregate_id).delete()
    payload = {"reference": aggregate_id, "status": "COMPLETED", "amount": "10.00"}
    barrier = Barrier(WEBHOOK_WORKERS)

    def worker() -> str:
        close_old_connections()
        barrier.wait()
        try:
            # Execute the task body directly: the validator owns its worker
            # threads and must not depend on Celery's thread-local request stack.
            return str(process_provider_webhook_task("flutterwave", payload)["event_id"])
        finally:
            close_old_connections()

    event_ids = _run_workers(worker, WEBHOOK_WORKERS)
    stored = models.EventRecord.objects.filter(aggregate_id=aggregate_id)
    if stored.count() != 1:
        raise RuntimeError("duplicate webhook storm did not collapse to a single event")
    return tuple(event_ids)


def _provider_retry_storm() -> tuple[tuple[str, ...], tuple[str, ...]]:
    route = DomainPaymentRoute(
        route_id="route.retry.001",
        transaction_id="tx.retry.001",
        provider="flutterwave_sandbox",
        rail="bank",
        amount=Money.of("5.00", "USD"),
        fee=Money.of("0.00", "USD"),
    )
    transport = httpx.MockTransport(_flutterwave_mock_handler)
    provider = FlutterwaveSandboxProvider(
        client_id="client",
        client_secret="secret",
        transport=transport,
    )
    barrier = Barrier(PROVIDER_WORKERS)

    def worker() -> str:
        close_old_connections()
        barrier.wait()
        try:
            return str(provider.send(route).external_reference)
        finally:
            close_old_connections()

    flutterwave_refs = _run_workers(worker, PROVIDER_WORKERS)

    mpesa_route = DomainPaymentRoute(
        route_id="route.retry.002",
        transaction_id="tx.retry.002",
        provider="mpesa_sandbox",
        rail="mobile_money",
        amount=Money.of("5.00", "KES"),
        fee=Money.of("0.00", "KES"),
    )
    mpesa_transport = httpx.MockTransport(_mpesa_mock_handler)
    mpesa_provider = MpesaSandboxProvider(
        consumer_key="consumer",
        consumer_secret="secret",
        short_code="600000",
        passkey="passkey",
        callback_url="https://example.com/mpesa/callback",
        transport=mpesa_transport,
    )
    mpesa_barrier = Barrier(PROVIDER_WORKERS)

    def mpesa_worker() -> str:
        close_old_connections()
        mpesa_barrier.wait()
        try:
            return str(mpesa_provider.send(mpesa_route).external_reference)
        finally:
            close_old_connections()

    mpesa_refs = _run_workers(mpesa_worker, PROVIDER_WORKERS)
    if len(set(flutterwave_refs)) != 1 or len(set(mpesa_refs)) != 1:
        raise RuntimeError("provider retry storm produced inconsistent references")
    return tuple(flutterwave_refs), tuple(mpesa_refs)


def _flutterwave_mock_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/protocol/openid-connect/token"):
        return httpx.Response(200, json={"access_token": "flw.token.001", "expires_in": 3600})
    if request.url.path.endswith("/transfers"):
        return httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "id": "flw.transfer.001",
                    "reference": "route.retry.001",
                },
            },
        )
    return httpx.Response(404, json={"detail": "unexpected flutterwave request"})


def _mpesa_mock_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path.endswith("/oauth/v1/generate"):
        return httpx.Response(200, json={"access_token": "mpesa.token.001", "expires_in": 3600})
    if request.method == "POST" and request.url.path.endswith("/processrequest"):
        return httpx.Response(
            200,
            json={
                "ResponseCode": "0",
                "CheckoutRequestID": "mpesa.checkout.001",
            },
        )
    return httpx.Response(404, json={"detail": "unexpected mpesa request"})


def _run_workers(worker, worker_count: int) -> list[str | bool]:
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        return list(executor.map(lambda _: worker(), range(worker_count)))


def _afripay_models():
    if not settings.configured:
        base_dir = Path(__file__).resolve().parents[2]
        django_app_dir = base_dir / "afriride_system" / "django_app"
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        if str(django_app_dir) not in sys.path:
            sys.path.insert(0, str(django_app_dir))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "afriride_system.django_app.config.settings")
        django.setup()
    return import_module("afriride_system.django_app.apps.afripay.models")


if __name__ == "__main__":
    raise SystemExit(main())
