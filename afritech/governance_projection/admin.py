from django.contrib import admin

from .models import (
    GovernanceADR,
    GovernanceBinding,
    GovernanceCICheck,
    GovernanceInvariant,
    GovernanceNextStep,
    GovernanceNonClaim,
    GovernanceRule,
)


class DocumentaryProjectionAdmin(admin.ModelAdmin):
    list_display = (
        "source_id",
        "title",
        "projection_status",
        "projection_is_documentary_only",
        "runtime_authority",
        "enforcement_authority",
    )
    search_fields = ("source_id", "title", "source_path")

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in (
    GovernanceADR,
    GovernanceInvariant,
    GovernanceRule,
    GovernanceBinding,
    GovernanceCICheck,
    GovernanceNonClaim,
    GovernanceNextStep,
):
    admin.site.register(model, DocumentaryProjectionAdmin)
