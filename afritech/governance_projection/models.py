from django.db import models


PROJECTION_STATUS = "DOCUMENTARY"
PROJECTION_IS_DOCUMENTARY_ONLY = True
RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False


class DocumentaryProjectionModel(models.Model):
    """Base shape for non-authoritative governance projection records."""

    source_path = models.CharField(max_length=512)
    source_id = models.CharField(max_length=96)
    title = models.CharField(max_length=256, blank=True)
    projection_status = models.CharField(max_length=32, default=PROJECTION_STATUS)
    projection_is_documentary_only = models.BooleanField(
        default=PROJECTION_IS_DOCUMENTARY_ONLY
    )
    runtime_authority = models.BooleanField(default=RUNTIME_AUTHORITY)
    enforcement_authority = models.BooleanField(default=ENFORCEMENT_AUTHORITY)
    payload = models.JSONField(default=dict)

    class Meta:
        abstract = True
        app_label = "governance_projection"
        managed = False

    def __str__(self) -> str:
        return f"{self.__class__.__name__}<{self.source_id}>"


class GovernanceADR(DocumentaryProjectionModel):
    status = models.CharField(max_length=64)
    adr_type = models.CharField(max_length=128, blank=True)
    runtime_authoritative_declared = models.BooleanField(default=False)

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance ADR"
        verbose_name_plural = "Governance ADRs"


class GovernanceInvariant(DocumentaryProjectionModel):
    adr_id = models.CharField(max_length=96, blank=True)
    description = models.TextField(blank=True)

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance invariant"
        verbose_name_plural = "Governance invariants"


class GovernanceRule(DocumentaryProjectionModel):
    adr_id = models.CharField(max_length=96, blank=True)
    description = models.TextField(blank=True)

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance rule"
        verbose_name_plural = "Governance rules"


class GovernanceBinding(DocumentaryProjectionModel):
    adr_id = models.CharField(max_length=96, blank=True)
    target = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance binding"
        verbose_name_plural = "Governance bindings"


class GovernanceCICheck(DocumentaryProjectionModel):
    adr_id = models.CharField(max_length=96, blank=True)
    check_name = models.CharField(max_length=160)

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance CI check"
        verbose_name_plural = "Governance CI checks"


class GovernanceNonClaim(DocumentaryProjectionModel):
    adr_id = models.CharField(max_length=96, blank=True)
    statement = models.TextField()

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance non-claim"
        verbose_name_plural = "Governance non-claims"


class GovernanceNextStep(DocumentaryProjectionModel):
    adr_id = models.CharField(max_length=96, blank=True)
    statement = models.TextField()

    class Meta(DocumentaryProjectionModel.Meta):
        verbose_name = "Governance next step"
        verbose_name_plural = "Governance next steps"
