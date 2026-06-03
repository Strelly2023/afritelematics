from evidence.models import EventLog
from regions.services import get_region_policy
from tax.calculator import calculate_tax
from tax.models import TaxRecord

from .gateways import PaymentGateway
from .models import Payment
from .router import get_payment_provider


def authorize_payment(ride, amount, currency="AUD"):
    gateway = PaymentGateway()
    result = gateway.authorize(ride.rider, amount, currency=currency)

    payment = Payment.objects.create(
        ride=ride,
        rider=ride.rider,
        amount=amount,
        currency=result["currency"],
        status=result["status"],
        provider=result["provider"],
        provider_reference=result["provider_reference"],
    )

    EventLog.objects.create(
        ride=ride,
        event_type="payment_authorized",
        actor=ride.rider,
        metadata={
            "amount": str(amount),
            "currency": payment.currency,
            "payment_id": payment.id,
            "provider": payment.provider,
            "provider_reference": payment.provider_reference,
        },
    )

    return payment


def capture_payment(payment):
    if payment.status != "authorized":
        raise ValueError("Payment must be authorized before capture")

    gateway = PaymentGateway()
    result = gateway.capture(payment.provider_reference)

    payment.status = result["status"]
    payment.save(update_fields=["status", "updated_at"])

    EventLog.objects.create(
        ride=payment.ride,
        event_type="payment_captured",
        actor=payment.rider,
        metadata={
            "amount": str(payment.amount),
            "currency": payment.currency,
            "payment_id": payment.id,
        },
    )

    return payment


def charge_regional_payment(ride, subtotal, token, country_code):
    """Charge a region-routed provider after caller verifies replay completion."""

    region = get_region_policy(country_code)
    tax_result = calculate_tax(subtotal=subtotal, tax_rate=region.tax_rate)
    provider = get_payment_provider(region)

    charge = provider.charge(
        amount=tax_result["total"],
        currency=region.currency,
        token=token,
        metadata={
            "ride_id": ride.id,
            "country_code": region.country_code,
            "tax_name": region.tax_name,
            "tax": str(tax_result["tax"]),
        },
    )

    payment = Payment.objects.create(
        ride=ride,
        rider=ride.rider,
        amount=tax_result["total"],
        currency=region.currency,
        status=charge["status"],
        provider=charge["provider"],
        provider_reference=charge["reference"],
        country_code=region.country_code,
        subtotal_amount=tax_result["subtotal"],
        tax_amount=tax_result["tax"],
    )

    tax_record = TaxRecord.objects.create(
        ride=ride,
        country_code=region.country_code,
        tax_name=region.tax_name,
        tax_rate=region.tax_rate,
        subtotal=tax_result["subtotal"],
        tax=tax_result["tax"],
        total=tax_result["total"],
        currency=region.currency,
    )

    EventLog.objects.create(
        ride=ride,
        event_type="payment_captured",
        actor=ride.rider,
        metadata={
            "payment_id": payment.id,
            "tax_record_id": tax_record.id,
            "provider": charge["provider"],
            "reference": charge["reference"],
            "subtotal": str(tax_result["subtotal"]),
            "tax_name": region.tax_name,
            "tax": str(tax_result["tax"]),
            "total": str(tax_result["total"]),
            "currency": region.currency,
            "country_code": region.country_code,
        },
    )

    return payment
