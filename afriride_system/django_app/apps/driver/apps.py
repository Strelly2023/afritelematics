"""Django app config for drivers."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class DriverConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.driver"
else:
    class DriverConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.driver"
