from django.urls import path, include

from afritech.api.afriride_driver_views import (
    driver_availability,
    driver_earnings,
    driver_queue,
    driver_replay_history,
    driver_status,
    ride_accept,
    ride_arrive,
    ride_complete,
    ride_reject,
    ride_start,
)
from afritech.api.trust_kernel_views import verify_event_view

urlpatterns = [
    path("api/", include("afritech.api.urls")),
    path("verify/<uuid:event_id>", verify_event_view),
    path("driver/availability", driver_availability),
    path("driver/status", driver_status),
    path("driver/<str:driver_id>/queue", driver_queue),
    path("driver/<str:driver_id>/earnings", driver_earnings),
    path("driver/replay-history", driver_replay_history),
    path("ride/<str:ride_id>/accept", ride_accept),
    path("ride/<str:ride_id>/reject", ride_reject),
    path("ride/arrive", ride_arrive),
    path("ride/<str:ride_id>/start", ride_start),
    path("ride/<str:ride_id>/complete", ride_complete),
]
