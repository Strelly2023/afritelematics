"""Production-oriented Django API views for AfriPay."""

from __future__ import annotations

from base64 import b64decode
from hashlib import sha256
import json
import os
from typing import Any

from django.http import HttpResponse
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.afripay.exceptions import ProviderFailure
from afritech.afripay.money import Money
from afritech.afripay.models import PaymentRoute as DomainPaymentRoute
from afritech.afripay.proofs import build_transaction_inclusion_proofs, build_transaction_zk_attestations
from afritech.afripay.protocol import (
    build_recursive_global_proof,
    export_signed_proof_evidence,
    proof_artifact_download_payload,
    render_audit_pdf,
    sign_recursive_proof_bundle,
)
from afritech.chain.anchor_publisher import publish_anchor
from afritech.afripay.providers_sandbox import FlutterwaveSandboxProvider, MpesaSandboxProvider
from afritech.afripay.tasks import enqueue_payment_processing, enqueue_webhook_processing
from afritech.afripay.reconciliation import (
    GlobalLedgerReconciliationEngine,
    LedgerReconciliationEngine,
    validate_global_ledger_integrity,
)
from afriride_system.django_app.apps.afripay.models import (
    APIKeyCredential,
    Escrow,
    EventRecord,
    IdempotencyKey,
    LiquidityPool,
    OAuthClient,
    PaymentRoute,
    PayoutBatch,
    PayoutItem,
    ProviderTransaction,
    Transaction,
    Wallet,
)
from afriride_system.django_app.apps.afripay.monitoring import build_snapshot, prometheus_text
from afriride_system.django_app.apps.afripay.security import (
    APIKeyService,
    OAuth2TokenService,
    SecurityPrincipal,
    send_auth_alert,
    verify_oauth_client_credentials,
)
from afriride_system.django_app.apps.afripay.serializers import (
    APIKeyIssueSerializer,
    EscrowCreateSerializer,
    EscrowReleaseSerializer,
    EscrowSerializer,
    EventRecordSerializer,
    FXQuoteSerializer,
    LiquidityPoolSerializer,
    MoneyInputSerializer,
    OAuthTokenSerializer,
    PaymentCreateSerializer,
    PayoutCreateSerializer,
    TransactionSerializer,
    WalletSerializer,
)
from afritech.afripay.persistence import PersistentIdempotencyStore, PersistentTreasuryStore
from afritech.afripay.api import AfriPayService
from afritech.afripay.operations import (
    append_event as _append_event,
    create_payment_sync as _create_payment_sync,
    ensure_pool as _ensure_pool,
    party as _party,
)


OAUTH = OAuth2TokenService()
API_KEYS = APIKeyService()


def _principal(request) -> SecurityPrincipal | None:
    return getattr(request, "afripay_principal", None)


def _require_scope_response(request, scope: str) -> Response | None:
    principal = _principal(request)
    if principal is None:
        return Response({"detail": "authentication required"}, status=401)
    scopes = set(getattr(request, "afripay_scopes", set()))
    if scope not in scopes:
        return Response({"detail": f"missing scope: {scope}"}, status=403)
    return None


def _extract_client_credentials(request, data: dict[str, Any]) -> tuple[str | None, str | None]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = b64decode(auth.removeprefix("Basic ").strip()).decode("utf-8")
            if ":" in decoded:
                return tuple(decoded.split(":", 1))  # type: ignore[return-value]
        except Exception:
            return None, None
    client_id = data.get("client_id") or request.headers.get("X-Client-Id")
    client_secret = data.get("client_secret") or request.headers.get("X-Client-Secret")
    return (client_id or None, client_secret or None)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


@api_view(["POST"])
def oauth_token_view(request) -> Response:
    serializer = OAuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if data["grant_type"] != "client_credentials":
        return Response({"detail": "unsupported grant_type"}, status=400)
    client_id, client_secret = _extract_client_credentials(request, data)
    if not client_id or not client_secret:
        return Response({"detail": "client credentials required"}, status=400)
    try:
        client = verify_oauth_client_credentials(client_id, client_secret, data.get("scope"))
    except ValueError as exc:
        send_auth_alert("AFRIPAY_OAUTH_TOKEN_FAILURE", {"client_id": client_id, "reason": str(exc)})
        return Response({"detail": str(exc)}, status=401 if "invalid" in str(exc) else 403)

    requested = [scope for scope in (data.get("scope") or "").split() if scope]
    scopes = requested or list(client.scopes)
    token = OAUTH.issue_access_token(client, scopes)
    return Response(
        {
            "access_token": token["access_token"],
            "expires_in": token["expires_in"],
            "scope": token["scope"],
            "token_type": token["token_type"],
        }
    )


@api_view(["POST"])
def api_key_issue_view(request) -> Response:
    scope_error = _require_scope_response(request, "api_keys:write")
    if scope_error is not None:
        return scope_error
    serializer = APIKeyIssueSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    credential, raw_key = API_KEYS.issue_key(data["name"], list(data.get("scopes", [])))
    return Response(
        {
            "key_id": credential.key_id,
            "name": credential.name,
            "prefix": credential.prefix,
            "scopes": credential.scopes,
            "api_key": raw_key,
        },
        status=201,
    )


@api_view(["POST"])
def payment_create_view(request) -> Response:
    scope_error = _require_scope_response(request, "payments:write")
    if scope_error is not None:
        return scope_error
    serializer = PaymentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = dict(serializer.validated_data)
    idempotency_key = request.headers.get("Idempotency-Key") or data["reference"]
    idempotency = PersistentIdempotencyStore()
    existing = idempotency.get_existing_response(idempotency_key)
    if existing is not None:
        return Response(existing, status=200)
    with db_transaction.atomic():
        claim, created = idempotency.claim(idempotency_key, data)
    if not created:
        if claim.status == "completed" and claim.response:
            return Response(claim.response, status=200)
        return Response({"detail": "idempotency key already claimed"}, status=409)
    if data.pop("async_processing", False):
        task = enqueue_payment_processing(data, idempotency_key=idempotency_key)
        response = {"status": "queued", "reference": data["reference"], "task_id": task["task_id"]}
        idempotency.store_response(idempotency_key, response)
        return Response(response, status=202)
    response = _create_payment_sync(data)
    idempotency.store_response(idempotency_key, response)
    return Response(response, status=201)


@api_view(["GET"])
def payment_detail_view(request, reference: str) -> Response:
    scope_error = _require_scope_response(request, "payments:read")
    if scope_error is not None:
        return scope_error
    tx = Transaction.objects.prefetch_related("routes").get(reference=reference)
    return Response(TransactionSerializer(tx).data)


@api_view(["POST"])
def fx_quote_view(request) -> Response:
    scope_error = _require_scope_response(request, "fx:read")
    if scope_error is not None:
        return scope_error
    serializer = FXQuoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    return Response(
        AfriPayService().quote_fx(
            str(data["amount"]),
            data["from_currency"],
            data["to_currency"],
        )
    )


@api_view(["GET"])
def wallet_detail_view(request, wallet_id: str) -> Response:
    scope_error = _require_scope_response(request, "wallets:read")
    if scope_error is not None:
        return scope_error
    wallet = Wallet.objects.prefetch_related("currency_accounts").get(wallet_id=wallet_id)
    return Response(WalletSerializer(wallet).data)


@api_view(["GET"])
def treasury_pools_view(request) -> Response:
    scope_error = _require_scope_response(request, "treasury:read")
    if scope_error is not None:
        return scope_error
    pools = LiquidityPool.objects.order_by("provider", "currency")
    return Response({"pools": LiquidityPoolSerializer(pools, many=True).data})


@api_view(["GET"])
def event_replay_view(request, aggregate_id: str) -> Response:
    scope_error = _require_scope_response(request, "events:read")
    if scope_error is not None:
        return scope_error
    events = EventRecord.objects.filter(aggregate_id=aggregate_id).order_by("created_at", "id")
    return Response({"events": EventRecordSerializer(events, many=True).data})


@api_view(["POST"])
def escrow_create_view(request) -> Response:
    scope_error = _require_scope_response(request, "escrows:write")
    if scope_error is not None:
        return scope_error
    serializer = EscrowCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    tx = Transaction.objects.get(reference=data["transaction_reference"])
    escrow = Escrow.objects.create(
        escrow_id="escrow." + tx.transaction_id,
        transaction=tx,
        payer=tx.payer,
        payee=tx.payee,
        total=tx.amount,
        currency=tx.currency,
        release_condition=data["release_condition"],
        expires_at=data.get("expires_at"),
    )
    _append_event("afripay.escrow.locked", tx.reference, {"escrow_id": escrow.escrow_id})
    return Response(EscrowSerializer(escrow).data, status=201)


@api_view(["POST"])
def escrow_release_view(request, escrow_id: str) -> Response:
    scope_error = _require_scope_response(request, "escrows:write")
    if scope_error is not None:
        return scope_error
    serializer = EscrowReleaseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    escrow = Escrow.objects.select_for_update().get(escrow_id=escrow_id)
    if escrow.expires_at is not None and escrow.expires_at < timezone.now():
        return Response({"detail": "escrow expired"}, status=409)
    if escrow.status != "locked":
        return Response({"detail": "escrow is not locked"}, status=409)
    if serializer.validated_data["evidence"] != escrow.release_condition:
        return Response({"detail": "release evidence mismatch"}, status=400)
    escrow.status = "released"
    escrow.save(update_fields=["status", "updated_at"])
    _append_event("afripay.escrow.released", escrow.transaction.reference, {"escrow_id": escrow_id})
    return Response(EscrowSerializer(escrow).data)


@api_view(["POST"])
def payout_create_view(request) -> Response:
    scope_error = _require_scope_response(request, "payouts:write")
    if scope_error is not None:
        return scope_error
    serializer = PayoutCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    items = data["items"]
    if not items:
        return Response({"detail": "payout requires items"}, status=400)
    currencies = {item["currency"].upper() for item in items}
    if len(currencies) != 1:
        return Response({"detail": "payout items must share currency"}, status=400)
    currency = next(iter(currencies))
    total = sum((item["amount"] for item in items), Decimal("0.00"))
    with db_transaction.atomic():
        initiator = _party(data["initiated_by"], data["initiated_by_country"], 2)
        batch = PayoutBatch.objects.create(
            payout_id="payout." + canonical_hash({"initiated_by": initiator.party_id, "items": items})[:24],
            initiated_by=initiator,
            total=total,
            currency=currency,
        )
        for item in items:
            recipient = _party(item["recipient_id"], item["recipient_country"], 1)
            PayoutItem.objects.create(
                payout=batch,
                recipient=recipient,
                amount=item["amount"],
                currency=item["currency"].upper(),
                reference=item["reference"],
            )
        _append_event("afripay.payout.created", batch.payout_id, {"payout_id": batch.payout_id, "total": str(total)})
    return Response({"payout_id": batch.payout_id, "status": batch.status, "total": str(batch.total)}, status=201)


@api_view(["POST"])
def webhook_view(request, provider: str) -> Response:
    expected = os.environ.get(f"AFRIPAY_{provider.upper()}_WEBHOOK_SECRET") or os.environ.get(
        "AFRIPAY_WEBHOOK_SECRET"
    )
    if expected:
        supplied = request.headers.get("X-Webhook-Secret", "")
        if supplied != expected:
            send_auth_alert(
                "AFRIPAY_WEBHOOK_AUTH_FAILURE",
                {"provider": provider, "reason": "invalid_shared_secret"},
            )
            return Response({"detail": "invalid webhook secret"}, status=401)
    task = enqueue_webhook_processing(provider, dict(request.data))
    return Response({"status": "queued", "task_id": task["task_id"]}, status=202)


@api_view(["POST"])
def flutterwave_sandbox_transfer_view(request) -> Response:
    scope_error = _require_scope_response(request, "providers:sandbox")
    if scope_error is not None:
        return scope_error
    serializer = MoneyInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    route = DomainPaymentRoute(
        route_id=request.data.get(
            "reference",
            "flw." + canonical_hash({"amount": str(data["amount"]), "currency": data["currency"]})[:24],
        ),
        transaction_id=request.data.get("transaction_id", "sandbox.tx.flutterwave"),
        provider="flutterwave_sandbox",
        rail="bank",
        amount=Money.of(data["amount"], data["currency"]),
        fee=Money.of("0.00", data["currency"]),
        external_reference=None,
    )
    try:
        provider = FlutterwaveSandboxProvider(
            client_id=os.environ.get("FLW_CLIENT_ID", ""),
            client_secret=os.environ.get("FLW_CLIENT_SECRET", ""),
        )
        result = provider.send(route)
    except ProviderFailure as exc:
        return Response({"detail": str(exc)}, status=503)
    except Exception as exc:  # noqa: BLE001
        return Response({"detail": f"sandbox transfer failed: {exc}"}, status=502)
    return Response(
        {
            "provider": result.provider,
            "external_reference": result.external_reference,
            "status": result.status,
            "latency_ms": result.latency_ms,
            "raw": result.raw,
        }
    )


@api_view(["POST"])
def mpesa_sandbox_stk_push_view(request) -> Response:
    scope_error = _require_scope_response(request, "providers:sandbox")
    if scope_error is not None:
        return scope_error
    serializer = MoneyInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    route = DomainPaymentRoute(
        route_id=request.data.get(
            "reference",
            "mpesa." + canonical_hash({"amount": str(data["amount"]), "currency": data["currency"]})[:24],
        ),
        transaction_id=request.data.get("transaction_id", "sandbox.tx.mpesa"),
        provider="mpesa_sandbox",
        rail="mobile_money",
        amount=Money.of(data["amount"], data["currency"]),
        fee=Money.of("0.00", data["currency"]),
        external_reference=None,
    )
    try:
        provider = MpesaSandboxProvider(
            consumer_key=os.environ.get("MPESA_CONSUMER_KEY", ""),
            consumer_secret=os.environ.get("MPESA_CONSUMER_SECRET", ""),
            short_code=os.environ.get("MPESA_SHORT_CODE", ""),
            passkey=os.environ.get("MPESA_PASSKEY", ""),
            callback_url=os.environ.get("MPESA_CALLBACK_URL", "https://example.com/mpesa/callback"),
        )
        result = provider.send(route)
    except ProviderFailure as exc:
        return Response({"detail": str(exc)}, status=503)
    except Exception as exc:  # noqa: BLE001
        return Response({"detail": f"sandbox stk push failed: {exc}"}, status=502)
    return Response(
        {
            "provider": result.provider,
            "external_reference": result.external_reference,
            "status": result.status,
            "latency_ms": result.latency_ms,
            "raw": result.raw,
        }
    )


@api_view(["GET"])
def metrics_json_view(request) -> Response:
    scope_error = _require_scope_response(request, "monitoring:read")
    if scope_error is not None:
        return scope_error
    snapshot = build_snapshot()
    return Response(
        {
            "counters": snapshot.counters,
            "histograms": snapshot.histograms,
            "alerts": list(snapshot.alerts),
        }
    )


@api_view(["GET"])
def metrics_prometheus_view(request) -> Response:
    return Response(prometheus_text(), content_type="text/plain; version=0.0.4; charset=utf-8")


@api_view(["GET"])
def alerts_view(request) -> Response:
    scope_error = _require_scope_response(request, "monitoring:read")
    if scope_error is not None:
        return scope_error
    snapshot = build_snapshot()
    return Response({"alerts": list(snapshot.alerts)})


@api_view(["GET"])
def proof_export_view(request) -> Response:
    scope_error = _require_scope_response(request, "proofs:read")
    if scope_error is not None:
        return scope_error

    reference = request.query_params.get("reference")
    anchor_network = (request.query_params.get("anchor_network") or "external_log").lower()

    if reference:
        report = LedgerReconciliationEngine().reconcile_transaction(reference)
        inclusion_proofs = build_transaction_inclusion_proofs((report,))
        zk_attestations = build_transaction_zk_attestations(
            inclusion_proofs,
            audit_merkle_root=report.report_hash(),
            transaction_count=1,
        )
        payload = {
            "scope": "transaction",
            "reference": reference,
            "report": report.canonical_dict(),
            "transaction_report_hash": report.report_hash(),
            "transaction_inclusion_proof": (
                inclusion_proofs[0].canonical_dict() if inclusion_proofs else None
            ),
            "transaction_zk_attestation": (
                zk_attestations[0].canonical_dict() if zk_attestations else None
            ),
        }
        payload["proof_hash"] = _canonical_hash(payload)
        return Response(payload)

    if anchor_network == "mainnet":
        report = GlobalLedgerReconciliationEngine(
            anchor_mode="blockchain",
            anchor_profile_name="mainnet",
        ).reconcile_all()
    elif anchor_network == "blockchain":
        report = GlobalLedgerReconciliationEngine(anchor_mode="blockchain").reconcile_all()
    else:
        report = validate_global_ledger_integrity(anchor_mode="external_log")

    payload = {
        "scope": "global",
        "anchor_network": anchor_network,
        "report": report.canonical_dict(),
        "global_proof_hash": report.global_proof_hash,
        "audit_merkle_root": report.audit_merkle_root,
        "ledger_merkle_root": report.ledger_merkle_root,
        "provider_merkle_root": report.provider_merkle_root,
        "event_merkle_root": report.event_merkle_root,
        "treasury_merkle_root": report.treasury_merkle_root,
        "chain_receipt": report.chain_receipt.canonical_dict() if report.chain_receipt is not None else None,
        "external_anchor_commitment": (
            report.external_anchor_commitment.canonical_dict()
            if report.external_anchor_commitment is not None
            else None
        ),
    }
    payload["proof_hash"] = _canonical_hash(payload)
    return Response(payload)


@api_view(["POST"])
def proof_anchor_view(request) -> Response:
    scope_error = _require_scope_response(request, "proofs:write")
    if scope_error is not None:
        return scope_error

    proof_hash = str(request.data.get("proof_hash") or "").strip()
    if not proof_hash:
        return Response({"detail": "proof_hash is required"}, status=400)

    profile_name = str(request.data.get("profile_name") or "sepolia").strip().lower()
    if profile_name not in {"sepolia", "mainnet"}:
        return Response({"detail": "unsupported profile_name"}, status=400)

    require_live = bool(request.data.get("require_live", profile_name == "mainnet"))
    try:
        receipt = publish_anchor(
            proof_hash,
            profile_name=profile_name,
            require_live=require_live,
        )
    except Exception as exc:  # noqa: BLE001
        return Response({"detail": str(exc)}, status=503)

    return Response(
        {
            "status": "anchored" if receipt.is_live() else "prepared",
            "profile_name": profile_name,
            "require_live": require_live,
            "proof_hash": proof_hash,
            "chain_receipt": receipt.canonical_dict(),
        }
    )


@api_view(["GET"])
def proof_artifacts_view(request):
    scope_error = _require_scope_response(request, "proofs:read")
    if scope_error is not None:
        return scope_error

    artifact_format = (
        request.query_params.get("download_format")
        or request.query_params.get("artifact_format")
        or "json"
    ).lower()
    output_dir = request.query_params.get("output_dir")
    reference = request.query_params.get("reference")

    if reference:
        report = LedgerReconciliationEngine().reconcile_transaction(reference)
        transaction_proofs = build_transaction_inclusion_proofs((report,))
        zk_attestations = build_transaction_zk_attestations(
            transaction_proofs,
            audit_merkle_root=report.report_hash(),
            transaction_count=1,
        )
        payload = {
            "scope": "transaction",
            "reference": reference,
            "report": report.canonical_dict(),
            "transaction_report_hash": report.report_hash(),
            "transaction_inclusion_proof": transaction_proofs[0].canonical_dict() if transaction_proofs else None,
            "transaction_zk_attestation": zk_attestations[0].canonical_dict() if zk_attestations else None,
        }
        payload["proof_hash"] = _canonical_hash(payload)
        response_payload = payload
        if artifact_format == "pdf":
            return _download_pdf_response(
                render_audit_pdf(
                    sign_recursive_proof_bundle(
                        build_recursive_global_proof(
                            validate_global_ledger_integrity(anchor_mode="external_log")
                        )
                    )
                ),
                filename="afripay_transaction_evidence.pdf",
            )
        return _download_json_response(response_payload, filename="afripay_transaction_evidence.json")

    report = validate_global_ledger_integrity(anchor_mode="external_log")
    bundle = build_recursive_global_proof(report)
    signed = sign_recursive_proof_bundle(bundle)
    payload = proof_artifact_download_payload(signed)
    if output_dir:
        export_signed_proof_evidence(signed, output_dir)
    if artifact_format == "pdf":
        return _download_pdf_response(render_audit_pdf(signed), filename="afripay_proof_bundle.pdf")
    return _download_json_response(payload, filename="afripay_proof_bundle.json")


def _download_json_response(payload: dict[str, Any], *, filename: str) -> HttpResponse:
    response = HttpResponse(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _download_pdf_response(pdf_bytes: bytes, *, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
