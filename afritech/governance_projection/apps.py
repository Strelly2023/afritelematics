from django.apps import AppConfig


class GovernanceProjectionConfig(AppConfig):
    """Django app config for documentary governance projection records."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "afritech.governance_projection"
    label = "governance_projection"
    verbose_name = "AfriTech Governance Projection"

    projection_status = "DOCUMENTARY"
    projection_is_documentary_only = True
    runtime_authority = False
    enforcement_authority = False
