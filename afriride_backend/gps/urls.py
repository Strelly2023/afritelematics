from django.urls import path

from .views import GPSUpdateView

urlpatterns = [
    path("gps/update", GPSUpdateView.as_view(), name="gps-update"),
]
