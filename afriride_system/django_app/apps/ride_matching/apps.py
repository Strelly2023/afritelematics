"""Django app config for ride matching."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class RideMatchingConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.ride_matching"
else:
    class RideMatchingConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.ride_matching"
