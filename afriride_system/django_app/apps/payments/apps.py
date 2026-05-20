"""Django app config for payments."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class PaymentsConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.payments"
else:
    class PaymentsConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.payments"
