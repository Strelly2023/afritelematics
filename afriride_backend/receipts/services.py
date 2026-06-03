from earnings.models import DriverEarning
from earnings.services import record_driver_earning
from payments.models import Payment
from payments.services import (
    authorize_payment,
    capture_payment,
    charge_regional_payment,
)
from pricing.services import calculate_replay_backed_fare
from replay.services import generate_replay_receipt
from route_replay.receipts import build_route_replay_receipt


COMPLETED_STATUS = "completed"


def assert_replay_verified_completion(replay_receipt):
    verified_state = replay_receipt.get("verified_state", {})
    if verified_state.get("status") != COMPLETED_STATUS:
        raise ValueError("Cannot capture payment before replay-verified completion")


def complete_trip_with_payment(ride, fare_policy=None, currency="AUD"):
    """Capture payment and ledger earnings only after replay verifies completion."""

    replay_receipt = generate_replay_receipt(ride.id)
    assert_replay_verified_completion(replay_receipt)
    route_receipt = build_route_replay_receipt(ride.id)
    replay_receipt.setdefault("distance_km", route_receipt.get("distance_km", 0))
    replay_receipt.setdefault(
        "duration_minutes",
        route_receipt.get("duration_minutes", 0),
    )

    fare_result = calculate_replay_backed_fare(
        replay_receipt=replay_receipt,
        policy=fare_policy,
    )
    payment = authorize_payment(
        ride=ride,
        amount=fare_result["total_fare"],
        currency=currency,
    )
    capture_payment(payment)
    earning = record_driver_earning(ride, fare_result)

    return {
        "authority": "replay_backed_payment",
        "ride_id": ride.id,
        "fare": fare_result,
        "payment_id": payment.id,
        "earning_id": earning.id,
        "replay_verified": True,
        "gateway": "mock",
    }


def complete_trip_with_regional_payment(
    ride,
    country_code,
    payment_token,
    fare_policy=None,
):
    """Region-aware payment flow gated by replay-verified completion."""

    replay_receipt = generate_replay_receipt(ride.id)
    assert_replay_verified_completion(replay_receipt)
    route_receipt = build_route_replay_receipt(ride.id)
    replay_receipt.setdefault("distance_km", route_receipt.get("distance_km", 0))
    replay_receipt.setdefault(
        "duration_minutes",
        route_receipt.get("duration_minutes", 0),
    )

    fare_result = calculate_replay_backed_fare(
        replay_receipt=replay_receipt,
        policy=fare_policy,
    )
    payment = charge_regional_payment(
        ride=ride,
        subtotal=fare_result["total_fare"],
        token=payment_token,
        country_code=country_code,
    )
    earning = record_driver_earning(ride=ride, fare_result=fare_result)

    return {
        "authority": "regional_replay_backed_payment",
        "ride_id": ride.id,
        "country_code": payment.country_code,
        "currency": payment.currency,
        "fare": fare_result,
        "charged_total": str(payment.amount),
        "payment_id": payment.id,
        "earning_id": earning.id,
        "replay_verified": True,
        "gateway": payment.provider,
    }


def generate_customer_receipt(ride):
    replay = generate_replay_receipt(ride.id)
    assert_replay_verified_completion(replay)
    payment = Payment.objects.get(ride=ride)

    return {
        "authority": "replay_backed_receipt",
        "ride_id": ride.id,
        "rider_id": ride.rider_id,
        "payment_status": payment.status,
        "provider": payment.provider,
        "provider_reference": payment.provider_reference,
        "country_code": payment.country_code,
        "subtotal": str(payment.subtotal_amount) if payment.subtotal_amount else None,
        "tax": str(payment.tax_amount) if payment.tax_amount else None,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "replay_verified": True,
        "replay": replay,
    }


def generate_driver_receipt(ride):
    replay = generate_replay_receipt(ride.id)
    assert_replay_verified_completion(replay)
    earning = DriverEarning.objects.get(ride=ride)

    return {
        "authority": "replay_backed_earning_receipt",
        "ride_id": ride.id,
        "driver_id": ride.driver_id,
        "gross_fare": str(earning.gross_fare),
        "platform_fee": str(earning.platform_fee),
        "net_earning": str(earning.net_earning),
        "replay_verified": True,
        "replay": replay,
    }
