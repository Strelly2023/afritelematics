"""
AfriTech Strategy Registry

PURPOSE:
--------
Provides a registry for adaptive optimization strategies.

Responsibilities:
- register custom optimization strategies
- retrieve strategy functions dynamically
- allow runtime strategy switching
- ensure deterministic behavior

CRITICAL LAW:
-------------
Strategy Registry MAY:
- register optimization strategies
- select strategy based on name

Strategy Registry may NOT:
- modify event data
- introduce randomness
- alter execution semantics
"""

# ============================================================
# ✅ INTERNAL REGISTRY STORAGE
# ============================================================

_STRATEGIES = {}


# ============================================================
# ✅ REGISTER STRATEGY
# ============================================================

def register_strategy(name: str, func):
    """
    Register a new adaptive strategy.

    Args:
        name: unique strategy name
        func: function(load_state, context) -> policy dict
    """

    if not isinstance(name, str):
        raise TypeError("Strategy name must be a string")

    if not callable(func):
        raise TypeError("Strategy must be a callable function")

    if name in _STRATEGIES:
        raise Exception(
            f"[STRATEGY ERROR] Strategy '{name}' already registered"
        )

    _STRATEGIES[name] = func


# ============================================================
# ✅ GET STRATEGY
# ============================================================

def get_strategy(name: str):
    """
    Retrieve a registered strategy.

    Returns:
        function or None (if not found)
    """

    if not isinstance(name, str):
        raise TypeError("Strategy name must be a string")

    return _STRATEGIES.get(name)


# ============================================================
# ✅ REMOVE STRATEGY
# ============================================================

def unregister_strategy(name: str):
    """
    Remove a strategy from registry.
    """

    if name in _STRATEGIES:
        del _STRATEGIES[name]


# ============================================================
# ✅ LIST STRATEGIES
# ============================================================

def list_strategies():
    """
    Returns list of registered strategy names.
    """

    return list(_STRATEGIES.keys())


# ============================================================
# ✅ CLEAR REGISTRY (TESTING ONLY)
# ============================================================

def clear_strategies():
    """
    Clears all registered strategies.

    ⚠️ Use only in testing environments.
    """

    _STRATEGIES.clear()


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_strategy(name: str):
    """
    Ensures strategy exists.
    """

    if name not in _STRATEGIES:
        raise Exception(
            f"[STRATEGY ERROR] Strategy '{name}' not found"
        )

    return True


# ============================================================
# ✅ SAFE EXECUTION WRAPPER
# ============================================================

def execute_strategy(name: str, load_state: str, context):
    """
    Execute strategy safely.

    Returns:
        proposed policy dict
    """

    strategy = get_strategy(name)

    if not strategy:
        raise Exception(
            f"[STRATEGY ERROR] Strategy '{name}' not registered"
        )

    result = strategy(load_state, context)

    if not isinstance(result, dict):
        raise Exception(
            "[STRATEGY ERROR] Strategy must return a policy dictionary"
        )

    return result


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_strategy_determinism(name: str, load_state: str, context):
    """
    Ensures strategy produces consistent output.
    """

    strategy = get_strategy(name)

    if not strategy:
        raise Exception(
            f"[STRATEGY ERROR] Strategy '{name}' not registered"
        )

    r1 = strategy(load_state, context)
    r2 = strategy(load_state, context)

    if r1 != r2:
        raise Exception(
            f"[STRATEGY ERROR] '{name}' is non-deterministic"
        )

    return True


# ============================================================
# ✅ TRACE / DEBUG
# ============================================================

def trace_strategy(name: str, load_state: str, context):
    """
    Debug helper to inspect strategy output.
    """

    strategy = get_strategy(name)

    if not strategy:
        return {
            "strategy": name,
            "status": "not_found"
        }

    result = strategy(load_state, context)

    return {
        "strategy": name,
        "load_state": load_state,
        "result": result,
    }


# ============================================================
# ✅ DEFAULT STRATEGY REGISTRATION (OPTIONAL)
# ============================================================

def register_default_strategies():
    """
    Registers built-in strategies.

    Example:
    - conservative
    - aggressive
    """

    def conservative(load_state, context):
        policy = dict(context.policy)

        if load_state == "overloaded":
            policy["batch_size"] = min(policy["batch_size"] + 2, 50)

        return policy

    def aggressive(load_state, context):
        policy = dict(context.policy)

        if load_state in ["high", "overloaded"]:
            policy["batch_size"] = min(policy["batch_size"] * 2, 1000)

        return policy

    # Register safely
    if "conservative" not in _STRATEGIES:
        register_strategy("conservative", conservative)

    if "aggressive" not in _STRATEGIES:
        register_strategy("aggressive", aggressive)