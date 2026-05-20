"""Django app config for safety."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class SafetyConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.safety"
else:
    class SafetyConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.safety"
