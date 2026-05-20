"""Django app config for ride lifecycle."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class RideLifecycleConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.ride_lifecycle"
else:
    class RideLifecycleConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.ride_lifecycle"
