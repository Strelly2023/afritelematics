from afritech.semantic_engine.ir.schema import Expression, SystemInvalid


def _assert_declared(symbol: str, declared_symbols: frozenset[str]) -> None:
    if symbol not in declared_symbols:
        raise SystemInvalid(f"undeclared_symbol:{symbol}")


def _substitute(expr, variable: str, value: str):
    if isinstance(expr, str):
        return value if expr == variable else expr
    if isinstance(expr, tuple):
        return tuple(_substitute(item, variable, value) for item in expr)
    if isinstance(expr, Expression):
        return Expression(
            expr.operator,
            tuple(_substitute(operand, variable, value) for operand in expr.operands),
        )
    raise SystemInvalid("invalid_ir_node")


def evaluate(expr, truth_values: dict[str, bool], declared_symbols: frozenset[str]) -> bool:
    if isinstance(expr, str):
        _assert_declared(expr, declared_symbols)
        if expr not in truth_values:
            raise SystemInvalid(f"missing_truth_value:{expr}")
        return bool(truth_values[expr])

    if not isinstance(expr, Expression):
        raise SystemInvalid("invalid_ir_node")

    op = expr.operator
    args = expr.operands

    if op == "AND":
        return all(evaluate(a, truth_values, declared_symbols) for a in args)

    if op == "EQUIVALENT":
        return evaluate(args[0], truth_values, declared_symbols) == evaluate(args[1], truth_values, declared_symbols)

    if op == "REQUIRES":
        lhs = evaluate(args[0], truth_values, declared_symbols)
        rhs = evaluate(args[1], truth_values, declared_symbols)
        return (not lhs) or rhs

    if op == "FORALL":
        variable, domain, body = args
        if not isinstance(variable, str) or not isinstance(domain, tuple):
            raise SystemInvalid("invalid_forall_operands")
        for symbol in domain:
            if not isinstance(symbol, str):
                raise SystemInvalid("forall_domain_must_be_symbols")
            _assert_declared(symbol, declared_symbols)
            if not evaluate(_substitute(body, variable, symbol), truth_values, declared_symbols):
                return False
        return True

    raise SystemInvalid(f"unsupported_operator:{op}")
