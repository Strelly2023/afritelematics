"""Django app config for pricing."""

try:
    from django.apps import AppConfig
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class PricingConfig:  # type: ignore[no-redef]
        name = "afriride_system.django_app.apps.pricing"
else:
    class PricingConfig(AppConfig):
        default_auto_field = "django.db.models.BigAutoField"
        name = "afriride_system.django_app.apps.pricing"
