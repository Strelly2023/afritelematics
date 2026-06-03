from django.urls import path

from .views import RouteReplayView

urlpatterns = [
    path("route-replay/<int:ride_id>", RouteReplayView.as_view(), name="route-replay"),
]
