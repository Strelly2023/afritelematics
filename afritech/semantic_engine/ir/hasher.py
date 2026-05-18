import hashlib
import json

from afritech.semantic_engine.ir.schema import Expression, SystemInvalid


def canonical_data(expr):
    if isinstance(expr, str):
        return {"type": "symbol", "value": expr}
    if isinstance(expr, tuple):
        return [canonical_data(item) for item in expr]
    if isinstance(expr, Expression):
        return {
            "type": "expression",
            "operator": expr.operator,
            "operands": [canonical_data(o) for o in expr.operands],
        }
    raise SystemInvalid("unhashable_ir_node")


def canonical_json(expr) -> str:
    return json.dumps(canonical_data(expr), sort_keys=True, separators=(",", ":"))


def hash_expression(expr) -> str:
    return hashlib.sha256(canonical_json(expr).encode("utf-8")).hexdigest()
