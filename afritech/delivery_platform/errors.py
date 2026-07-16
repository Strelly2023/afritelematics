"""Delivery platform errors."""

from __future__ import annotations


class DeliveryPlatformError(RuntimeError):
    pass


class NotConnectedError(DeliveryPlatformError):
    pass


class ManifestConflictError(DeliveryPlatformError):
    pass


class DeploymentStateError(DeliveryPlatformError):
    pass

