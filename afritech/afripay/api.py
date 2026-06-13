"""Framework-neutral AfriPay API facade."""

from __future__ import annotations

from afritech.afripay.fx import FXEngine, default_fx_engine
from afritech.afripay.money import Money
from afritech.afripay.orchestration import PaymentOrchestrator


class AfriPayService:
    def __init__(
        self,
        orchestrator: PaymentOrchestrator | None = None,
        fx_engine: FXEngine | None = None,
    ) -> None:
        self.orchestrator = orchestrator or PaymentOrchestrator()
        self.fx_engine = fx_engine or default_fx_engine()

    def create_payment(self, payload: dict[str, object]) -> dict[str, object]:
        result = self.orchestrator.process_payment(
            payer_id=str(payload["payer_id"]),
            payee_id=str(payload["payee_id"]),
            amount=Money.of(str(payload["amount"]), str(payload["currency"])),
            reference=str(payload["reference"]),
            preference=str(payload.get("preference", "balanced")),
            metadata=dict(payload.get("metadata", {})),
        )
        return {
            "event_count": result.event_count,
            "journal_reference": result.journal_reference,
            "metrics": self.orchestrator.metrics.snapshot(),
            "reference": result.transaction.reference,
            "routes": [
                {
                    "amount": route.amount.canonical(),
                    "external_reference": route.external_reference,
                    "provider": route.provider,
                    "rail": route.rail,
                    "status": route.status.value,
                }
                for route in result.routes
            ],
            "status": result.transaction.status.value,
            "transaction_id": result.transaction.transaction_id,
        }

    def quote_fx(self, amount: str, from_currency: str, to_currency: str) -> dict[str, object]:
        conversion = self.fx_engine.convert(
            transaction_id="quote",
            amount=Money.of(amount, from_currency),
            to_currency=to_currency,
        )
        return {
            "amount_in": conversion.amount_in.canonical(),
            "amount_out": conversion.amount_out.canonical(),
            "locked_reference": conversion.rate.locked_reference,
            "rate": str(conversion.rate.rate),
        }

