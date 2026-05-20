"""Django app config for notifications."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class NotificationsConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.notifications"
else:
    class NotificationsConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.notifications"
