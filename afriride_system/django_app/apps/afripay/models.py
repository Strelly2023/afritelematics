"""Django ORM models for AfriPay GA Elite."""

from __future__ import annotations

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AfriPayParty(TimeStampedModel):
    party_id = models.CharField(max_length=120, unique=True)
    country = models.CharField(max_length=8)
    kyc_level = models.PositiveSmallIntegerField(default=0)
    risk_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    def __str__(self) -> str:
        return self.party_id


class Wallet(TimeStampedModel):
    WALLET_TYPES = (
        ("personal", "Personal"),
        ("business", "Business"),
        ("community", "Community"),
        ("savings", "Savings"),
    )

    wallet_id = models.CharField(max_length=120, unique=True)
    owner = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="wallets")
    wallet_type = models.CharField(max_length=24, choices=WALLET_TYPES)
    home_country = models.CharField(max_length=8)
    is_active = models.BooleanField(default=True)


class CurrencyAccount(TimeStampedModel):
    account_id = models.CharField(max_length=120, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="currency_accounts")
    currency = models.CharField(max_length=8)
    balance = models.DecimalField(max_digits=24, decimal_places=2, default=0)
    locked_balance = models.DecimalField(max_digits=24, decimal_places=2, default=0)

    @property
    def available_balance(self):
        return self.balance - self.locked_balance

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["wallet", "currency"], name="afripay_unique_wallet_currency"),
            models.CheckConstraint(condition=models.Q(balance__gte=0), name="afp_cur_bal_nonneg"),
            models.CheckConstraint(condition=models.Q(locked_balance__gte=0), name="afp_cur_locked_nonneg"),
            models.CheckConstraint(condition=models.Q(balance__gte=models.F("locked_balance")), name="afripay_locked_lte_balance"),
        ]


class Transaction(TimeStampedModel):
    STATUSES = (
        ("pending", "Pending"),
        ("routed", "Routed"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    transaction_id = models.CharField(max_length=120, unique=True)
    reference = models.CharField(max_length=160, unique=True)
    payer = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="outgoing_transactions")
    payee = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="incoming_transactions")
    amount = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    transaction_type = models.CharField(max_length=32)
    status = models.CharField(max_length=24, choices=STATUSES, default="pending")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["reference"], name="afripay_tx_reference_idx"),
            models.Index(fields=["payer", "status"], name="afripay_tx_payer_status_idx"),
            models.Index(fields=["payee", "status"], name="afripay_tx_payee_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="afripay_tx_amount_positive"),
        ]


class PaymentRoute(TimeStampedModel):
    route_id = models.CharField(max_length=120, unique=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="routes")
    provider = models.CharField(max_length=80)
    rail = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    fee = models.DecimalField(max_digits=24, decimal_places=2, default=0)
    status = models.CharField(max_length=24, default="planned")
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    external_reference = models.CharField(max_length=180, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "status"], name="afp_route_provider_idx"),
        ]


class LedgerAccount(TimeStampedModel):
    account_id = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=160)
    account_type = models.CharField(max_length=40)
    currency = models.CharField(max_length=8)


class JournalEntry(TimeStampedModel):
    journal_id = models.CharField(max_length=120, unique=True)
    reference = models.CharField(max_length=160, unique=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="journal_entries")


class EntryLine(TimeStampedModel):
    journal = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, related_name="lines")
    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="entry_lines")
    debit = models.DecimalField(max_digits=24, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=24, decimal_places=2, default=0)
    currency = models.CharField(max_length=8)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(debit__gte=0), name="afp_entry_debit_nonneg"),
            models.CheckConstraint(condition=models.Q(credit__gte=0), name="afp_entry_credit_nonneg"),
        ]


class FXRate(TimeStampedModel):
    locked_reference = models.CharField(max_length=120, unique=True)
    base_currency = models.CharField(max_length=8)
    quote_currency = models.CharField(max_length=8)
    rate = models.DecimalField(max_digits=24, decimal_places=8)
    provider = models.CharField(max_length=80)


class FXConversion(TimeStampedModel):
    conversion_id = models.CharField(max_length=120, unique=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="fx_conversions")
    amount_in = models.DecimalField(max_digits=24, decimal_places=2)
    amount_out = models.DecimalField(max_digits=24, decimal_places=2)
    from_currency = models.CharField(max_length=8)
    to_currency = models.CharField(max_length=8)
    rate = models.ForeignKey(FXRate, on_delete=models.PROTECT, related_name="conversions")


class LiquidityPool(TimeStampedModel):
    pool_id = models.CharField(max_length=120, unique=True)
    provider = models.CharField(max_length=80)
    currency = models.CharField(max_length=8)
    balance = models.DecimalField(max_digits=24, decimal_places=2)
    reserved = models.DecimalField(max_digits=24, decimal_places=2, default=0)
    low_watermark = models.DecimalField(max_digits=24, decimal_places=2, default=0)

    @property
    def available_balance(self):
        return self.balance - self.reserved

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "currency"], name="afp_unique_provider_pool"),
            models.CheckConstraint(condition=models.Q(balance__gte=0), name="afp_pool_bal_nonneg"),
            models.CheckConstraint(condition=models.Q(reserved__gte=0), name="afp_pool_res_nonneg"),
            models.CheckConstraint(condition=models.Q(balance__gte=models.F("reserved")), name="afp_pool_res_lte_bal"),
        ]


class TreasuryReservation(TimeStampedModel):
    reservation_id = models.CharField(max_length=160, unique=True)
    pool = models.ForeignKey(LiquidityPool, on_delete=models.PROTECT, related_name="reservations")
    amount = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    status = models.CharField(max_length=24, default="reserved")


class Escrow(TimeStampedModel):
    escrow_id = models.CharField(max_length=120, unique=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="escrows")
    payer = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="escrows_paid")
    payee = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="escrows_received")
    total = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    release_condition = models.CharField(max_length=240)
    status = models.CharField(max_length=24, default="locked")
    expires_at = models.DateTimeField(null=True, blank=True)


class PayoutBatch(TimeStampedModel):
    payout_id = models.CharField(max_length=120, unique=True)
    initiated_by = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="payout_batches")
    total = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    status = models.CharField(max_length=24, default="planned")


class PayoutItem(TimeStampedModel):
    payout = models.ForeignKey(PayoutBatch, on_delete=models.PROTECT, related_name="items")
    recipient = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="payout_items")
    amount = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    reference = models.CharField(max_length=160, unique=True)
    status = models.CharField(max_length=24, default="pending")
    retry_count = models.PositiveIntegerField(default=0)


class Subscription(TimeStampedModel):
    subscription_id = models.CharField(max_length=120, unique=True)
    customer = models.ForeignKey(AfriPayParty, on_delete=models.PROTECT, related_name="subscriptions")
    plan_name = models.CharField(max_length=120)
    recurring_amount = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    status = models.CharField(max_length=24, default="active")
    next_billing_at = models.DateTimeField()
    grace_period_days = models.PositiveIntegerField(default=3)


class Invoice(TimeStampedModel):
    invoice_id = models.CharField(max_length=120, unique=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name="invoices")
    amount = models.DecimalField(max_digits=24, decimal_places=2)
    currency = models.CharField(max_length=8)
    status = models.CharField(max_length=24, default="open")
    due_at = models.DateTimeField()


class KYCProfile(TimeStampedModel):
    party = models.OneToOneField(AfriPayParty, on_delete=models.PROTECT, related_name="kyc_profile")
    level = models.PositiveSmallIntegerField(default=0)
    document_type = models.CharField(max_length=80, null=True, blank=True)
    verified = models.BooleanField(default=False)
    risk_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)


class ProviderTransaction(TimeStampedModel):
    provider = models.CharField(max_length=80)
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="provider_transactions")
    internal_reference = models.CharField(max_length=160, null=True, blank=True)
    external_reference = models.CharField(max_length=180)
    status = models.CharField(max_length=40)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "external_reference"], name="afp_unique_provider_ref"),
        ]


class EventRecord(TimeStampedModel):
    event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=120)
    aggregate_id = models.CharField(max_length=160, null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    hash_chain = models.CharField(max_length=64)

    class Meta:
        indexes = [
            models.Index(fields=["aggregate_id", "created_at"], name="afripay_event_aggregate_idx"),
            models.Index(fields=["event_type"], name="afripay_event_type_idx"),
        ]


class IdempotencyKey(TimeStampedModel):
    key = models.CharField(max_length=180, unique=True)
    request_hash = models.CharField(max_length=64)
    response = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, default="stored")
    expires_at = models.DateTimeField(null=True, blank=True)


class OAuthClient(TimeStampedModel):
    client_id = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=160)
    secret_hash = models.CharField(max_length=64)
    scopes = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    suspended_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["client_id"], name="afp_oauth_client_idx"),
            models.Index(fields=["is_active"], name="afp_oauth_active_idx"),
        ]

    @staticmethod
    def hash_secret(raw_secret: str) -> str:
        import hashlib

        return hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()


class APIKeyCredential(TimeStampedModel):
    key_id = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=160)
    key_hash = models.CharField(max_length=64, unique=True)
    prefix = models.CharField(max_length=12)
    scopes = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    suspended_until = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["key_hash"], name="afp_apikey_hash_idx"),
            models.Index(fields=["is_active"], name="afp_apikey_active_idx"),
        ]

    @staticmethod
    def hash_key(raw_key: str) -> str:
        import hashlib

        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
