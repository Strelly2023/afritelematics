"""Canonical payload transformations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TransformResult:
    source_schema: str
    target_schema: str
    payload: Mapping[str, Any]


class DataTransformer(Protocol):
    transformer_id: str
    source_schema: str
    target_schema: str

    def transform(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


def transform_payload(transformer: DataTransformer, payload: Mapping[str, Any]) -> TransformResult:
    return TransformResult(
        source_schema=transformer.source_schema,
        target_schema=transformer.target_schema,
        payload=transformer.transform(payload),
    )
