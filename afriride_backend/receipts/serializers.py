from rest_framework import serializers


class CustomerReceiptSerializer(serializers.Serializer):
    authority = serializers.CharField()
    ride_id = serializers.IntegerField()
    rider_id = serializers.IntegerField()
    payment_status = serializers.CharField()
    provider = serializers.CharField()
    provider_reference = serializers.CharField(allow_blank=True)
    country_code = serializers.CharField(allow_blank=True)
    subtotal = serializers.CharField(allow_null=True)
    tax = serializers.CharField(allow_null=True)
    amount = serializers.CharField()
    currency = serializers.CharField()
    replay_verified = serializers.BooleanField()
    replay = serializers.DictField()


class DriverReceiptSerializer(serializers.Serializer):
    authority = serializers.CharField()
    ride_id = serializers.IntegerField()
    driver_id = serializers.IntegerField()
    gross_fare = serializers.CharField()
    platform_fee = serializers.CharField()
    net_earning = serializers.CharField()
    replay_verified = serializers.BooleanField()
    replay = serializers.DictField()
