from evidence.models import EventLog

from .models import DriverEarning


def record_driver_earning(ride, fare_result):
    earning = DriverEarning.objects.create(
        ride=ride,
        driver=ride.driver,
        gross_fare=fare_result["total_fare"],
        platform_fee=fare_result["platform_fee"],
        net_earning=fare_result["driver_earnings"],
    )

    EventLog.objects.create(
        ride=ride,
        event_type="driver_earning_recorded",
        actor=ride.driver,
        metadata={
            "earning_id": earning.id,
            "gross_fare": str(earning.gross_fare),
            "platform_fee": str(earning.platform_fee),
            "net_earning": str(earning.net_earning),
        },
    )

    return earning
