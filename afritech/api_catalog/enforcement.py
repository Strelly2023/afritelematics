"""Decorators for runtime contract enforcement."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

from afritech.api_catalog.metrics import record_contract_validation
from afritech.api_catalog.runtime_validation import RuntimeContractViolation, validate_payload


F = TypeVar("F", bound=Callable[..., Any])


def enforce_response_contract(*, schema: dict[str, Any], operation_id: str, mode: str = "enforce") -> Callable[[F], F]:
    def decorator(function: F) -> F:
        def _validate(payload: Any) -> None:
            try:
                validate_payload(payload, schema, operation_id=operation_id)
                record_contract_validation(operation_id=operation_id, result="pass")
            except RuntimeContractViolation:
                record_contract_validation(operation_id=operation_id, result="violation")
                if mode == "enforce":
                    raise

        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                payload = await function(*args, **kwargs)
                _validate(payload)
                return payload

            return async_wrapper  # type: ignore[return-value]

        @wraps(function)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            payload = function(*args, **kwargs)
            _validate(payload)
            return payload

        return sync_wrapper  # type: ignore[return-value]

    return decorator
