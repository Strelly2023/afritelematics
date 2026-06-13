"""DRF serializers for AfriPay API."""

from __future__ import annotations

from rest_framework import serializers

from afriride_system.django_app.apps.afripay.models import (
    CurrencyAccount,
    Escrow,
    EventRecord,
    LiquidityPool,
    PaymentRoute,
    Transaction,
    Wallet,
)
from afritech.afripay.money import SUPPORTED_CURRENCIES


class MoneyInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=24, decimal_places=2)
    currency = serializers.CharField(max_length=8)

    def validate_currency(self, value: str) -> str:
        upper = value.upper()
        if upper not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError("unsupported currency")
        return upper


class PaymentCreateSerializer(serializers.Serializer):
    payer_id = serializers.CharField(max_length=120)
    payer_country = serializers.CharField(max_length=8, default="AU")
    payer_kyc_level = serializers.IntegerField(default=2, min_value=0)
    payee_id = serializers.CharField(max_length=120)
    payee_country = serializers.CharField(max_length=8, default="BI")
    payee_kyc_level = serializers.IntegerField(default=2, min_value=0)
    amount = serializers.DecimalField(max_digits=24, decimal_places=2)
    currency = serializers.CharField(max_length=8)
    reference = serializers.CharField(max_length=160)
    preference = serializers.ChoiceField(
        choices=("balanced", "cheapest", "fastest", "reliable"),
        default="balanced",
    )
    metadata = serializers.DictField(required=False, default=dict)
    async_processing = serializers.BooleanField(default=False)

    def validate_currency(self, value: str) -> str:
        upper = value.upper()
        if upper not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError("unsupported currency")
        return upper

    def validate_payer_country(self, value: str) -> str:
        return value.upper()

    def validate_payee_country(self, value: str) -> str:
        return value.upper()


class FXQuoteSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=24, decimal_places=2)
    from_currency = serializers.CharField(max_length=8)
    to_currency = serializers.CharField(max_length=8)

    def validate_from_currency(self, value: str) -> str:
        upper = value.upper()
        if upper not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError("unsupported currency")
        return upper

    def validate_to_currency(self, value: str) -> str:
        upper = value.upper()
        if upper not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError("unsupported currency")
        return upper


class EscrowCreateSerializer(serializers.Serializer):
    transaction_reference = serializers.CharField(max_length=160)
    release_condition = serializers.CharField(max_length=240)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class EscrowReleaseSerializer(serializers.Serializer):
    evidence = serializers.CharField(max_length=240)


class PayoutItemInputSerializer(serializers.Serializer):
    recipient_id = serializers.CharField(max_length=120)
    recipient_country = serializers.CharField(max_length=8, default="BI")
    amount = serializers.DecimalField(max_digits=24, decimal_places=2)
    currency = serializers.CharField(max_length=8)
    reference = serializers.CharField(max_length=160)

    def validate_currency(self, value: str) -> str:
        upper = value.upper()
        if upper not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError("unsupported currency")
        return upper


class PayoutCreateSerializer(serializers.Serializer):
    initiated_by = serializers.CharField(max_length=120)
    initiated_by_country = serializers.CharField(max_length=8, default="AU")
    items = PayoutItemInputSerializer(many=True)


class OAuthTokenSerializer(serializers.Serializer):
    grant_type = serializers.CharField(max_length=40)
    client_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
    client_secret = serializers.CharField(max_length=160, required=False, allow_blank=True)
    scope = serializers.CharField(max_length=240, required=False, allow_blank=True, allow_null=True)


class APIKeyIssueSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    scopes = serializers.ListField(
        child=serializers.CharField(max_length=80),
        allow_empty=True,
        required=False,
        default=list,
    )


class CurrencyAccountSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)

    class Meta:
        model = CurrencyAccount
        fields = ("account_id", "currency", "balance", "locked_balance", "available_balance")


class WalletSerializer(serializers.ModelSerializer):
    currency_accounts = CurrencyAccountSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = ("wallet_id", "owner_id", "wallet_type", "home_country", "is_active", "currency_accounts")


class PaymentRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRoute
        fields = ("route_id", "provider", "rail", "amount", "currency", "fee", "status", "latency_ms", "external_reference")


class TransactionSerializer(serializers.ModelSerializer):
    routes = PaymentRouteSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = ("transaction_id", "reference", "payer_id", "payee_id", "amount", "currency", "transaction_type", "status", "metadata", "routes")


class LiquidityPoolSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)

    class Meta:
        model = LiquidityPool
        fields = ("pool_id", "provider", "currency", "balance", "reserved", "available_balance", "low_watermark")


class EventRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRecord
        fields = ("event_id", "event_type", "aggregate_id", "payload", "hash_chain", "created_at")


class EscrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escrow
        fields = ("escrow_id", "transaction_id", "payer_id", "payee_id", "total", "currency", "release_condition", "status", "expires_at")
