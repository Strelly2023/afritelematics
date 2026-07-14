"""API audience taxonomy."""

from __future__ import annotations

from enum import StrEnum


class ApiAudience(StrEnum):
    PUBLIC = "public"
    PARTNER = "partner"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    OPERATOR = "operator"
    ADMINISTRATOR = "administrator"
    INTERNAL_SERVICE = "internal-service"


PUBLIC_COMPATIBLE_AUDIENCES = {ApiAudience.PUBLIC, ApiAudience.PARTNER, ApiAudience.CUSTOMER}
