from evidence.models import EventLog
from replay.services import generate_replay_receipt

from .models import BillingAccount, BusinessRideCharge


COMPLETED_STATUS = "completed"


def create_billing_account(country, currency, organization=None, fleet=None):
    if organization is None and fleet is None:
        raise ValueError("Billing account requires organization or fleet")
    if organization is not None and fleet is not None:
        raise ValueError("Billing account target must be organization or fleet, not both")

    return BillingAccount.objects.create(
        organization=organization,
        fleet=fleet,
        country=country,
        currency=currency,
    )


def assert_ride_replay_verified(ride):
    replay_receipt = generate_replay_receipt(ride.id)
    verified_state = replay_receipt.get("verified_state", {})
    if verified_state.get("status") != COMPLETED_STATUS:
        raise ValueError("Cannot bill business account without replay verification")
    return replay_receipt


def charge_business_account(billing_account, ride, amount):
    replay_receipt = assert_ride_replay_verified(ride)

    charge = BusinessRideCharge.objects.create(
        billing_account=billing_account,
        ride=ride,
        amount=amount,
        currency=billing_account.currency,
        replay_verified=True,
    )

    EventLog.objects.create(
        ride=ride,
        event_type="business_account_charged",
        actor=ride.rider,
        metadata={
            "billing_account_id": billing_account.id,
            "business_charge_id": charge.id,
            "amount": str(amount),
            "currency": billing_account.currency,
            "replay_verified": True,
            "replay_receipt_id": replay_receipt.get("receipt_id"),
        },
    )

    return charge
