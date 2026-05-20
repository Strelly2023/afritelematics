"""Compatibility re-export for the product validation bridge."""

from afriride_system.django_app.orchestration.validation_bridge import (
    ValidationReceipt,
    validate_execution,
)

__all__ = ["ValidationReceipt", "validate_execution"]
