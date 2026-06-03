from django.urls import path

from .consumers import OperatorMonitorConsumer, RideConsumer

websocket_urlpatterns = [
    path("ws/rides/<int:ride_id>/", RideConsumer.as_asgi()),
    path("ws/operator/monitor/", OperatorMonitorConsumer.as_asgi()),
]
