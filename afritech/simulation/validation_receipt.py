from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


SCHEMA = "afritech.simulation.validation_receipt.v1"


def stable_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ValidationReceipt:
    schema: str
    surface: str
    validator: str
    input_hash: str
    output_hash: str
    trace_hash: str
    replay_hash: str
    deterministic: bool
    replay_safe: bool
    evidence: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return asdict(self)


def build_validation_receipt(
    *,
    surface: str,
    validator: str,
    inputs: Any,
    outputs: Any,
    trace: Any,
    evidence: tuple[str, ...],
) -> ValidationReceipt:
    input_hash = stable_hash(inputs)
    output_hash = stable_hash(outputs)
    trace_hash = stable_hash(trace)
    replay_hash = stable_hash(
        {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "trace_hash": trace_hash,
        }
    )
    return ValidationReceipt(
        schema=SCHEMA,
        surface=surface,
        validator=validator,
        input_hash=input_hash,
        output_hash=output_hash,
        trace_hash=trace_hash,
        replay_hash=replay_hash,
        deterministic=True,
        replay_safe=True,
        evidence=evidence,
    )
