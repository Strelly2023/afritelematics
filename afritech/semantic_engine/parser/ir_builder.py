from pathlib import Path
from typing import Any

import yaml

from afritech.semantic_engine.ir.schema import Expression, SemanticProgram, SystemInvalid


ALLOWED_OPERATORS = {"AND", "EQUIVALENT", "REQUIRES", "FORALL"}


def build_expression(data):
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        return tuple(build_expression(item) for item in data)

    if not isinstance(data, dict):
        raise SystemInvalid("invalid_expression_shape")

    operator = data.get("operator")
    if operator not in ALLOWED_OPERATORS:
        raise SystemInvalid(f"unsupported_operator:{operator}")

    operands = data.get("operands")
    if not isinstance(operands, list):
        raise SystemInvalid("operands_must_be_list")

    return Expression(
        operator=operator,
        operands=tuple(build_expression(o) for o in operands),
    )


def compile_semantic_yaml(source: str | Path | dict[str, Any]) -> SemanticProgram:
    if isinstance(source, dict):
        data = source
    else:
        path = Path(source)
        data = yaml.safe_load(path.read_text()) if path.exists() else yaml.safe_load(str(source))

    if not isinstance(data, dict):
        raise SystemInvalid("semantic_yaml_must_be_mapping")

    expression_data = data.get("expression")
    if expression_data is None:
        raise SystemInvalid("missing_expression")

    symbols = data.get("declared_symbols", data.get("symbols", []))
    if isinstance(symbols, dict):
        symbols = list(symbols.keys())
    if not isinstance(symbols, list) or not all(isinstance(s, str) for s in symbols):
        raise SystemInvalid("declared_symbols_must_be_string_list")

    return SemanticProgram(
        id=str(data.get("id", "anonymous_semantic_program")),
        expression=build_expression(expression_data),
        declared_symbols=frozenset(symbols),
    )
