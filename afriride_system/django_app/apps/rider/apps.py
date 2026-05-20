"""Django app config for riders."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class RiderConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.rider"
else:
    class RiderConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.rider"
