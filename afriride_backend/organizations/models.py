from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    billing_email = models.EmailField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("rider", "Rider"),
        ("finance", "Finance"),
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("organization", "user")
        ordering = ("organization", "role")

    def __str__(self):
        return f"{self.organization_id}:{self.user_id}:{self.role}"
