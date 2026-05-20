"""Django app config for ride requests."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class RideRequestConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.ride_request"
else:
    class RideRequestConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.ride_request"
