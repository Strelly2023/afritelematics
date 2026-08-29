"""NovaRide-local production payment boundary for NovaPay.

R18-I3-WP109-A1.

NovaPay remains authoritative for money movement, provider execution,
ledger posting, settlement and receipts.  NovaRide owns only this narrow
integration contract and its error mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable


class NovaPayIntegrationError(RuntimeError):
    """Base NovaRide payment-integration failure."""


class NovaPayConfigurationError(NovaPayIntegrationError):
    """Required production payment configuration is unavailable."""


class NovaPayProviderUnavailable(NovaPayIntegrationError):
    """The payment provider could not be reached."""


class NovaPayProviderRejected(NovaPayIntegrationError):
    """The payment provider rejected an operation."""


class NovaPayInvalidResponse(NovaPayIntegrationError):
    """The payment provider returned invalid authoritative data."""


@dataclass(frozen=True, slots=True)
class PaymentRequest:
    amount: Decimal
    currency: str
    tenant_id: str
    organization_id: str
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("payment_amount_must_be_positive")

        currency = self.currency.strip().upper()
        if len(currency) != 3:
            raise ValueError("payment_currency_invalid")

        for field in (
            "tenant_id",
            "organization_id",
            "correlation_id",
            "idempotency_key",
        ):
            if not str(getattr(self, field)).strip():
                raise ValueError(
                    f"payment_{field}_required"
                )

        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class PaymentResult:
    payment_id: str
    status: str
    provider: str
    receipt_id: str | None = None

    def __post_init__(self) -> None:
        if not self.payment_id.strip():
            raise ValueError(
                "payment_result_payment_id_required"
            )

        if not self.status.strip():
            raise ValueError(
                "payment_result_status_required"
            )

        if not self.provider.strip():
            raise ValueError(
                "payment_result_provider_required"
            )


@dataclass(frozen=True, slots=True)
class RefundResult:
    refund_id: str
    payment_id: str
    status: str

    def __post_init__(self) -> None:
        if not self.refund_id.strip():
            raise ValueError("refund_id_required")
        if not self.payment_id.strip():
            raise ValueError("refund_payment_id_required")
        if not self.status.strip():
            raise ValueError("refund_status_required")


@runtime_checkable
class NovaPayProductionProvider(Protocol):
    """NovaRide-facing production money-provider protocol."""

    def authorize(
        self,
        request: PaymentRequest,
    ) -> PaymentResult:
        ...

    def capture(
        self,
        *,
        payment_id: str,
        idempotency_key: str,
    ) -> PaymentResult:
        ...

    def refund(
        self,
        *,
        payment_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> RefundResult:
        ...

    def status(
        self,
        *,
        payment_id: str,
    ) -> PaymentResult:
        ...


class NovaPayProductionAdapter:
    """Fail-closed NovaRide adapter around an approved provider."""

    __slots__ = (
        "_provider",
        "_real_payments_enabled",
    )

    def __init__(
        self,
        provider: NovaPayProductionProvider | None,
        *,
        real_payments_enabled: bool,
    ) -> None:
        self._provider = provider
        self._real_payments_enabled = bool(
            real_payments_enabled
        )

    def _provider_or_fail(
        self,
    ) -> NovaPayProductionProvider:
        if not self._real_payments_enabled:
            raise NovaPayConfigurationError(
                "real_payments_not_enabled"
            )

        if self._provider is None:
            raise NovaPayConfigurationError(
                "novapay_production_provider_required"
            )

        return self._provider

    @staticmethod
    def _validate_payment_result(
        result: object,
    ) -> PaymentResult:
        if not isinstance(result, PaymentResult):
            raise NovaPayInvalidResponse(
                "novapay_payment_result_invalid"
            )

        if result.provider != "NovaPay":
            raise NovaPayInvalidResponse(
                "novapay_provider_authority_mismatch"
            )

        return result

    def authorize(
        self,
        request: PaymentRequest,
    ) -> PaymentResult:
        provider = self._provider_or_fail()

        try:
            result = provider.authorize(request)
        except NovaPayIntegrationError:
            raise
        except TimeoutError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_timeout"
            ) from exc
        except ConnectionError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_unavailable"
            ) from exc
        except Exception as exc:
            raise NovaPayProviderRejected(
                "novapay_authorization_failed"
            ) from exc

        return self._validate_payment_result(
            result
        )

    def capture(
        self,
        *,
        payment_id: str,
        idempotency_key: str,
    ) -> PaymentResult:
        provider = self._provider_or_fail()

        if not payment_id.strip():
            raise ValueError(
                "payment_id_required"
            )

        if not idempotency_key.strip():
            raise ValueError(
                "payment_idempotency_key_required"
            )

        try:
            result = provider.capture(
                payment_id=payment_id,
                idempotency_key=idempotency_key,
            )
        except TimeoutError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_timeout"
            ) from exc
        except ConnectionError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_unavailable"
            ) from exc
        except Exception as exc:
            raise NovaPayProviderRejected(
                "novapay_capture_failed"
            ) from exc

        return self._validate_payment_result(
            result
        )

    def refund(
        self,
        *,
        payment_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> RefundResult:
        provider = self._provider_or_fail()

        if not payment_id.strip():
            raise ValueError(
                "payment_id_required"
            )

        if amount <= Decimal("0"):
            raise ValueError(
                "refund_amount_must_be_positive"
            )

        if len(currency.strip()) != 3:
            raise ValueError(
                "refund_currency_invalid"
            )

        if not idempotency_key.strip():
            raise ValueError(
                "refund_idempotency_key_required"
            )

        try:
            result = provider.refund(
                payment_id=payment_id,
                amount=amount,
                currency=currency.upper(),
                idempotency_key=idempotency_key,
            )
        except TimeoutError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_timeout"
            ) from exc
        except ConnectionError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_unavailable"
            ) from exc
        except Exception as exc:
            raise NovaPayProviderRejected(
                "novapay_refund_failed"
            ) from exc

        if not isinstance(result, RefundResult):
            raise NovaPayInvalidResponse(
                "novapay_refund_result_invalid"
            )

        if result.payment_id != payment_id:
            raise NovaPayInvalidResponse(
                "novapay_refund_payment_mismatch"
            )

        return result

    def status(
        self,
        *,
        payment_id: str,
    ) -> PaymentResult:
        provider = self._provider_or_fail()

        if not payment_id.strip():
            raise ValueError(
                "payment_id_required"
            )

        try:
            result = provider.status(
                payment_id=payment_id
            )
        except TimeoutError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_timeout"
            ) from exc
        except ConnectionError as exc:
            raise NovaPayProviderUnavailable(
                "novapay_provider_unavailable"
            ) from exc
        except Exception as exc:
            raise NovaPayProviderRejected(
                "novapay_status_failed"
            ) from exc

        result = self._validate_payment_result(
            result
        )

        if result.payment_id != payment_id:
            raise NovaPayInvalidResponse(
                "novapay_status_payment_mismatch"
            )

        return result
