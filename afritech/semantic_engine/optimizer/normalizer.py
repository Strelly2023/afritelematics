from afritech.semantic_engine.ir.hasher import canonical_data
from afritech.semantic_engine.ir.schema import Expression, SystemInvalid


MAX_REWRITE_STEPS = 128


def _sort_key(expr) -> str:
    return repr(canonical_data(expr))


def _normalize_once(expr):
    if isinstance(expr, str):
        return expr

    if isinstance(expr, tuple):
        return tuple(normalize(item) for item in expr)

    if not isinstance(expr, Expression):
        raise SystemInvalid("invalid_ir_node")

    operands = tuple(normalize(operand) for operand in expr.operands)

    if expr.operator == "AND":
        flattened = []
        for operand in operands:
            if isinstance(operand, Expression) and operand.operator == "AND":
                flattened.extend(operand.operands)
            else:
                flattened.append(operand)

        deduped = []
        seen = set()
        for operand in sorted(flattened, key=_sort_key):
            key = _sort_key(operand)
            if key not in seen:
                seen.add(key)
                deduped.append(operand)

        if not deduped:
            raise SystemInvalid("and_requires_operands")
        if len(deduped) == 1:
            return deduped[0]
        return Expression("AND", tuple(deduped))

    if expr.operator == "EQUIVALENT":
        if len(operands) != 2:
            raise SystemInvalid("equivalent_requires_two_operands")
        return Expression("EQUIVALENT", tuple(sorted(operands, key=_sort_key)))

    if expr.operator == "REQUIRES":
        if len(operands) != 2:
            raise SystemInvalid("requires_requires_two_operands")
        return Expression("REQUIRES", operands)

    if expr.operator == "FORALL":
        if len(operands) != 3 or not isinstance(operands[0], str) or not isinstance(operands[1], tuple):
            raise SystemInvalid("forall_requires_variable_domain_body")
        return Expression("FORALL", operands)

    raise SystemInvalid(f"unsupported_operator:{expr.operator}")


def normalize(expr):
    current = expr
    for _ in range(MAX_REWRITE_STEPS):
        rewritten = _normalize_once(current)
        if rewritten == current:
            return rewritten
        current = rewritten

    raise SystemInvalid("rewrite_overflow")
