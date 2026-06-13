"""Subscription and invoice primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from afritech.afripay.exceptions import GuardViolation
from afritech.afripay.models import Invoice, new_id
from afritech.afripay.money import Money


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    customer_id: str
    plan_name: str
    recurring_amount: Money
    status: str
    next_billing_at: datetime


class BillingService:
    def create_subscription(
        self,
        *,
        customer_id: str,
        plan_name: str,
        recurring_amount: Money,
        billing_period_days: int = 30,
    ) -> Subscription:
        recurring_amount.require_positive()
        if not customer_id or not plan_name:
            raise GuardViolation("customer_id and plan_name are required")
        if billing_period_days <= 0:
            raise GuardViolation("billing_period_days must be positive")
        return Subscription(
            new_id("sub"),
            customer_id,
            plan_name,
            recurring_amount,
            "active",
            datetime.now(timezone.utc) + timedelta(days=billing_period_days),
        )

    def generate_invoice(self, subscription: Subscription) -> Invoice:
        if subscription.status != "active":
            raise GuardViolation("subscription is not active")
        return Invoice(
            new_id("invoice"),
            subscription.customer_id,
            subscription.recurring_amount,
            "open",
            subscription.next_billing_at,
        )


