"""Sandbox and partner provider adapters for external payment rails."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import base64
import os
from typing import Any, Protocol

import httpx

from afritech.afripay.events import canonical_hash
from afritech.afripay.exceptions import ProviderFailure
from afritech.afripay.models import PaymentRoute, ProviderQuote
from afritech.afripay.money import Money


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    external_reference: str
    status: str
    latency_ms: int
    raw: dict[str, Any]


class PaymentProvider(Protocol):
    name: str
    rail: str

    def quote(self, amount: Money) -> ProviderQuote:
        ...

    def send(self, route: PaymentRoute) -> ProviderResult:
        ...

    def verify(self, external_reference: str) -> ProviderResult:
        ...


@dataclass(frozen=True)
class SandboxResponse:
    provider: str
    payload: dict[str, Any]
    raw: dict[str, Any]


class _OAuthSandboxProvider:
    def __init__(
        self,
        *,
        name: str,
        rail: str,
        client_id: str,
        client_secret: str,
        token_url: str,
        api_base_url: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.name = name
        self.rail = rail
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.api_base_url = api_base_url.rstrip("/")
        self._transport = transport
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=15.0, transport=self._transport)

    def _get_access_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token
        if not self.client_id or not self.client_secret:
            raise ProviderFailure(f"{self.name} sandbox credentials not configured")
        token = self._fetch_token()
        self._access_token = token["access_token"]
        self._token_expires_at = now.replace(microsecond=0) + _seconds(token.get("expires_in", 600) - 60)
        return self._access_token

    def _fetch_token(self) -> dict[str, Any]:
        raise NotImplementedError

    def quote(self, amount: Money) -> ProviderQuote:
        raise NotImplementedError

    def send(self, route: PaymentRoute) -> ProviderResult:
        raise NotImplementedError

    def verify(self, external_reference: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            external_reference=external_reference,
            status="confirmed",
            latency_ms=0,
            raw={"mode": "sandbox_verify", "provider": self.name},
        )


class FlutterwaveSandboxProvider(_OAuthSandboxProvider):
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        api_base_url: str | None = None,
        token_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        super().__init__(
            name="flutterwave_sandbox",
            rail="bank",
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url or "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token",
            api_base_url=api_base_url or "https://api.flutterwave.com/v3",
            transport=transport,
        )

    def _fetch_token(self) -> dict[str, Any]:
        with self._client() as client:
            response = client.post(
                self.token_url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            )
        response.raise_for_status()
        payload = response.json()
        if "access_token" not in payload:
            raise ProviderFailure("flutterwave sandbox token missing access_token")
        return payload

    def quote(self, amount: Money) -> ProviderQuote:
        fee = Money.of((amount.amount * Decimal("0.005")) + Decimal("0.25"), amount.currency)
        return ProviderQuote(
            provider=self.name,
            rail=self.rail,
            amount=amount,
            fee=fee,
            estimated_latency_ms=2200,
            reliability=Decimal("0.96"),
        )

    def send(self, route: PaymentRoute) -> ProviderResult:
        token = self._get_access_token()
        payload = {
            "account_bank": os.environ.get("FLW_SANDBOX_ACCOUNT_BANK", "044"),
            "account_number": os.environ.get("FLW_SANDBOX_ACCOUNT_NUMBER", "1234567890"),
            "amount": str(route.amount.amount),
            "currency": route.amount.currency,
            "narration": os.environ.get("FLW_SANDBOX_NARRATION", "AfriPay sandbox transfer"),
            "reference": route.route_id,
        }
        with self._client() as client:
            response = client.post(
                f"{self.api_base_url}/transfers",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        raw = response.json()
        reference = str(raw.get("data", {}).get("id") or raw.get("data", {}).get("reference") or route.route_id)
        return ProviderResult(
            provider=self.name,
            external_reference=reference,
            status=str(raw.get("status", "confirmed")),
            latency_ms=2200,
            raw=raw,
        )


class MpesaSandboxProvider(_OAuthSandboxProvider):
    def __init__(
        self,
        *,
        consumer_key: str,
        consumer_secret: str,
        short_code: str,
        passkey: str,
        callback_url: str,
        api_base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
        msisdn: str | None = None,
    ) -> None:
        super().__init__(
            name="mpesa_sandbox",
            rail="mobile_money",
            client_id=consumer_key,
            client_secret=consumer_secret,
            token_url=(api_base_url or "https://sandbox.safaricom.co.ke").rstrip("/")
            + "/oauth/v1/generate?grant_type=client_credentials",
            api_base_url=api_base_url or "https://sandbox.safaricom.co.ke",
            transport=transport,
        )
        self.short_code = short_code
        self.passkey = passkey
        self.callback_url = callback_url
        self.msisdn = msisdn or os.environ.get("MPESA_SANDBOX_MSISDN", "254700000000")

    def _fetch_token(self) -> dict[str, Any]:
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        with self._client() as client:
            response = client.get(
                self.token_url,
                headers={"Authorization": f"Basic {basic}"},
            )
        response.raise_for_status()
        payload = response.json()
        if "access_token" not in payload:
            raise ProviderFailure("mpesa sandbox token missing access_token")
        return payload

    def quote(self, amount: Money) -> ProviderQuote:
        fee = Money.of((amount.amount * Decimal("0.008")) + Decimal("0.20"), amount.currency)
        return ProviderQuote(
            provider=self.name,
            rail=self.rail,
            amount=amount,
            fee=fee,
            estimated_latency_ms=1800,
            reliability=Decimal("0.97"),
            supports_offline_fallback=True,
        )

    def send(self, route: PaymentRoute) -> ProviderResult:
        token = self._get_access_token()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{self.short_code}{self.passkey}{timestamp}".encode("utf-8")).decode("ascii")
        payload = {
            "BusinessShortCode": self.short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": os.environ.get("MPESA_TRANSACTION_TYPE", "CustomerPayBillOnline"),
            "Amount": int(route.amount.amount),
            "PartyA": self.msisdn,
            "PartyB": self.short_code,
            "PhoneNumber": self.msisdn,
            "CallBackURL": self.callback_url,
            "AccountReference": route.route_id,
            "TransactionDesc": os.environ.get("MPESA_TRANSACTION_DESC", "AfriPay sandbox payment"),
        }
        with self._client() as client:
            response = client.post(
                f"{self.api_base_url.rstrip('/')}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        raw = response.json()
        reference = str(raw.get("CheckoutRequestID") or raw.get("MerchantRequestID") or route.route_id)
        return ProviderResult(
            provider=self.name,
            external_reference=reference,
            status=str(raw.get("ResponseCode", "0")),
            latency_ms=1800,
            raw=raw,
        )


class MfsAfricaProvider(_OAuthSandboxProvider):
    """Configurable MFS Africa / Onafriq mobile-money adapter.

    MFS Africa rebranded as Onafriq, and commercial API contracts are commonly
    partner-specific. The base URL and endpoint paths are therefore configured
    by environment while the adapter enforces the invariant NovaPay owns:
    OAuth, idempotent reference propagation, and fail-closed credentials.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        api_base_url: str | None = None,
        token_url: str | None = None,
        transfer_path: str | None = None,
        verify_path: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        base_url = api_base_url or os.environ.get("MFS_AFRICA_API_BASE_URL", "https://api.onafriq.com")
        super().__init__(
            name="mfs_africa",
            rail="mobile_money",
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url
            or os.environ.get("MFS_AFRICA_TOKEN_URL")
            or f"{base_url.rstrip('/')}/oauth/token",
            api_base_url=base_url,
            transport=transport,
        )
        self.transfer_path = transfer_path or os.environ.get("MFS_AFRICA_TRANSFER_PATH", "/v1/transfers")
        self.verify_path = verify_path or os.environ.get("MFS_AFRICA_VERIFY_PATH", "/v1/transfers/{reference}")

    def _fetch_token(self) -> dict[str, Any]:
        with self._client() as client:
            response = client.post(
                self.token_url,
                headers={"Content-Type": "application/json"},
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": os.environ.get("MFS_AFRICA_GRANT_TYPE", "client_credentials"),
                },
            )
        response.raise_for_status()
        payload = response.json()
        if "access_token" not in payload:
            raise ProviderFailure("mfs_africa token missing access_token")
        return payload

    def quote(self, amount: Money) -> ProviderQuote:
        fee = Money.of((amount.amount * Decimal("0.009")) + Decimal("0.35"), amount.currency)
        return ProviderQuote(
            provider=self.name,
            rail=self.rail,
            amount=amount,
            fee=fee,
            estimated_latency_ms=1600,
            reliability=Decimal("0.965"),
            supports_offline_fallback=True,
        )

    def send(self, route: PaymentRoute) -> ProviderResult:
        token = self._get_access_token()
        payload = {
            "reference": route.route_id,
            "amount": str(route.amount.amount),
            "currency": route.amount.currency,
            "rail": route.rail,
            "provider": self.name,
            "metadata": {
                "transaction_id": route.transaction_id,
                "idempotency_key": route.route_id,
            },
        }
        with self._client() as client:
            response = client.post(
                f"{self.api_base_url}{self.transfer_path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": route.route_id,
                },
            )
        response.raise_for_status()
        raw = response.json()
        data = raw.get("data", {}) if isinstance(raw.get("data"), dict) else {}
        reference = str(
            data.get("id")
            or data.get("reference")
            or raw.get("id")
            or raw.get("reference")
            or route.route_id
        )
        return ProviderResult(
            provider=self.name,
            external_reference=reference,
            status=str(data.get("status") or raw.get("status") or "submitted"),
            latency_ms=1600,
            raw=raw,
        )

    def verify(self, external_reference: str) -> ProviderResult:
        if not external_reference:
            raise ProviderFailure("external_reference is required")
        token = self._get_access_token()
        path = self.verify_path.format(reference=external_reference)
        with self._client() as client:
            response = client.get(
                f"{self.api_base_url}{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        raw = response.json()
        data = raw.get("data", {}) if isinstance(raw.get("data"), dict) else {}
        return ProviderResult(
            provider=self.name,
            external_reference=external_reference,
            status=str(data.get("status") or raw.get("status") or "confirmed"),
            latency_ms=800,
            raw=raw,
        )


def sandbox_provider_set() -> tuple[PaymentProvider, ...]:
    provider_mode = os.environ.get("AFRIPAY_SANDBOX_PROVIDER", "").strip().lower()
    if provider_mode in {"mfs", "mfs_africa", "onafriq"}:
        return (
            MfsAfricaProvider(
                client_id=os.environ.get("MFS_AFRICA_CLIENT_ID", ""),
                client_secret=os.environ.get("MFS_AFRICA_CLIENT_SECRET", ""),
            ),
        )
    flutterwave = FlutterwaveSandboxProvider(
        client_id=os.environ.get("FLW_CLIENT_ID", ""),
        client_secret=os.environ.get("FLW_CLIENT_SECRET", ""),
    )
    mpesa = MpesaSandboxProvider(
        consumer_key=os.environ.get("MPESA_CONSUMER_KEY", ""),
        consumer_secret=os.environ.get("MPESA_CONSUMER_SECRET", ""),
        short_code=os.environ.get("MPESA_SHORT_CODE", ""),
        passkey=os.environ.get("MPESA_PASSKEY", ""),
        callback_url=os.environ.get("MPESA_CALLBACK_URL", "https://example.com/mpesa/callback"),
    )
    return (mpesa, flutterwave)


def _seconds(value: int) -> timedelta:
    return timedelta(seconds=max(0, int(value)))
