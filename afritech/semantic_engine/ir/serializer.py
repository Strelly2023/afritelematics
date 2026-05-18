import json
from typing import Any

from afritech.semantic_engine.ir.hasher import canonical_data
from afritech.semantic_engine.ir.schema import Expression, SystemInvalid
from afritech.semantic_engine.parser.ir_builder import build_expression


def to_data(expr) -> Any:
    return canonical_data(expr)


def to_json(expr) -> str:
    return json.dumps(to_data(expr), sort_keys=True, separators=(",", ":"))


def from_data(data: Any):
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return tuple(from_data(item) for item in data)
    if not isinstance(data, dict):
        raise SystemInvalid("invalid_serialized_ir")

    node_type = data.get("type")
    if node_type == "symbol":
        value = data.get("value")
        if not isinstance(value, str):
            raise SystemInvalid("invalid_serialized_symbol")
        return value
    if node_type == "expression":
        operator = data.get("operator")
        operands = data.get("operands", [])
        if not isinstance(operator, str) or not isinstance(operands, list):
            raise SystemInvalid("invalid_serialized_expression")
        return Expression(operator=operator, operands=tuple(from_data(item) for item in operands))
    if "operator" in data:
        return build_expression(data)

    raise SystemInvalid("invalid_serialized_ir")


def from_json(payload: str):
    try:
        return from_data(json.loads(payload))
    except json.JSONDecodeError as exc:
        raise SystemInvalid(f"invalid_ir_json:{exc.msg}") from exc


def expression_to_dict(expr: Expression | str | tuple) -> Any:
    return to_data(expr)
