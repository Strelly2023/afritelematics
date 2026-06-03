from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_ride_event(ride_id, event_type, payload):
    """Broadcast a non-authoritative ride projection.

    Final truth remains EventLog + ReplayEngine. This function only notifies
    rider, driver, and operator surfaces about confirmed backend events.
    """

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"ride_{ride_id}",
        {
            "type": "ride.event",
            "event_type": event_type,
            "payload": payload,
        },
    )

    async_to_sync(channel_layer.group_send)(
        "operator_monitor",
        {
            "type": "operator.event",
            "event_type": event_type,
            "payload": {
                "ride_id": ride_id,
                **payload,
            },
        },
    )
