"""
AFRIPower Intelligence Validator
"""

from __future__ import annotations

import ast
import inspect
import sys
from types import ModuleType
from typing import Any, Dict, Iterable

from afritech.afripower import constants as afripower_constants
from afritech.afripower.adapters import receipt_provider
from afritech.afripower.ai_reasoning import constants as reasoning_constants
from afritech.afripower.ai_reasoning import engine, explain, insights
from afritech.afripower.contracts import read_only_contract
from afritech.afripower.dashboard import constants as dashboard_constants
from afritech.afripower.dashboard import metrics, services, views
from afritech.afripower.graph import constants as graph_constants
from afritech.afripower.graph import models, projection, query, serializers
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


# =============================================================================
# ERROR
# =============================================================================

class AFRIPowerIntelligenceValidationError(RuntimeError):
    """Raised when AFRIPower violates read-only intelligence boundaries."""


# =============================================================================
# RULES
# =============================================================================

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.execution",
    "afritech.replay",
    "afritech.verify",
    "afritech.proof",
    "afritech.registry",
    "afritech.governance_projection",
)

FORBIDDEN_CALL_NAMES = (
    "open",
    "load",
    "dump",
    "save",
    "delete",
    "execute",
    "enforce",
    "validate",
    "authorize",
    "admit",
    "decide",
    "mutate",
    "write",
    "create",
    "update",
)

FORBIDDEN_MUTATION_ATTRIBUTES = (
    "save",
    "delete",
    "update",
    "create",
)

REQUIRED_FALSE_FLAGS = (
    "RUNTIME_AUTHORITY",
    "ENFORCEMENT_AUTHORITY",
    "VALIDATION_AUTHORITY",
    "GOVERNANCE_AUTHORITY",
    "INTELLIGENCE_AUTHORITY",
    "EXECUTION_AUTHORITY",
    "REPLAY_AUTHORITY",
    "PROOF_AUTHORITY",
)

REQUIRED_TRUE_FLAGS = (
    "READ_ONLY",
    "DISPLAY_ONLY",
)

MODULES_TO_SCAN: tuple[ModuleType, ...] = (
    afripower_constants,
    read_only_contract,
    receipt_provider,
    dashboard_constants,
    metrics,
    services,
    views,
    reasoning_constants,
    engine,
    insights,
    explain,
    graph_constants,
    models,
    projection,
    query,
    serializers,
)


# =============================================================================
# CORE FAIL
# =============================================================================

def _fail(message: str) -> None:
    args = [message]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__fail__mutmut_orig, x__fail__mutmut_mutants, args, kwargs, None)


# =============================================================================
# CORE FAIL
# =============================================================================

def x__fail__mutmut_orig(message: str) -> None:
    raise AFRIPowerIntelligenceValidationError(message)


# =============================================================================
# CORE FAIL
# =============================================================================

def x__fail__mutmut_1(message: str) -> None:
    raise AFRIPowerIntelligenceValidationError(None)

x__fail__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__fail__mutmut_1': x__fail__mutmut_1
}
x__fail__mutmut_orig.__name__ = 'x__fail'


# =============================================================================
# AST HELPERS
# =============================================================================

def _source(module: ModuleType) -> str:
    args = [module]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__source__mutmut_orig, x__source__mutmut_mutants, args, kwargs, None)


# =============================================================================
# AST HELPERS
# =============================================================================

def x__source__mutmut_orig(module: ModuleType) -> str:
    try:
        return inspect.getsource(module)
    except OSError as exc:
        _fail(f"cannot inspect module {module.__name__}: {exc}")


# =============================================================================
# AST HELPERS
# =============================================================================

def x__source__mutmut_1(module: ModuleType) -> str:
    try:
        return inspect.getsource(None)
    except OSError as exc:
        _fail(f"cannot inspect module {module.__name__}: {exc}")


# =============================================================================
# AST HELPERS
# =============================================================================

def x__source__mutmut_2(module: ModuleType) -> str:
    try:
        return inspect.getsource(module)
    except OSError as exc:
        _fail(None)

x__source__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__source__mutmut_1': x__source__mutmut_1, 
    'x__source__mutmut_2': x__source__mutmut_2
}
x__source__mutmut_orig.__name__ = 'x__source'


def _tree(module: ModuleType) -> ast.Module:
    args = [module]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__tree__mutmut_orig, x__tree__mutmut_mutants, args, kwargs, None)


def x__tree__mutmut_orig(module: ModuleType) -> ast.Module:
    try:
        return ast.parse(_source(module))
    except SyntaxError as exc:
        _fail(f"syntax error in {module.__name__}: {exc}")


def x__tree__mutmut_1(module: ModuleType) -> ast.Module:
    try:
        return ast.parse(None)
    except SyntaxError as exc:
        _fail(f"syntax error in {module.__name__}: {exc}")


def x__tree__mutmut_2(module: ModuleType) -> ast.Module:
    try:
        return ast.parse(_source(None))
    except SyntaxError as exc:
        _fail(f"syntax error in {module.__name__}: {exc}")


def x__tree__mutmut_3(module: ModuleType) -> ast.Module:
    try:
        return ast.parse(_source(module))
    except SyntaxError as exc:
        _fail(None)

x__tree__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__tree__mutmut_1': x__tree__mutmut_1, 
    'x__tree__mutmut_2': x__tree__mutmut_2, 
    'x__tree__mutmut_3': x__tree__mutmut_3
}
x__tree__mutmut_orig.__name__ = 'x__tree'


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def _validate_forbidden_imports(module: ModuleType) -> None:
    args = [module]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_forbidden_imports__mutmut_orig, x__validate_forbidden_imports__mutmut_mutants, args, kwargs, None)


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_orig(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_1(module: ModuleType) -> None:
    tree = None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_2(module: ModuleType) -> None:
    tree = _tree(None)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_3(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(None):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_4(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(None):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_5(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(None) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_6(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(None)

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_7(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = None
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_8(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module and ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_9(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or "XXXX"
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_10(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(None):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_11(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(None) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(f"{module.__name__} imports forbidden surface {mod}")


# =============================================================================
# STATIC VALIDATION
# =============================================================================

def x__validate_forbidden_imports__mutmut_12(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} imports forbidden surface {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(mod.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES):
                _fail(None)

x__validate_forbidden_imports__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_forbidden_imports__mutmut_1': x__validate_forbidden_imports__mutmut_1, 
    'x__validate_forbidden_imports__mutmut_2': x__validate_forbidden_imports__mutmut_2, 
    'x__validate_forbidden_imports__mutmut_3': x__validate_forbidden_imports__mutmut_3, 
    'x__validate_forbidden_imports__mutmut_4': x__validate_forbidden_imports__mutmut_4, 
    'x__validate_forbidden_imports__mutmut_5': x__validate_forbidden_imports__mutmut_5, 
    'x__validate_forbidden_imports__mutmut_6': x__validate_forbidden_imports__mutmut_6, 
    'x__validate_forbidden_imports__mutmut_7': x__validate_forbidden_imports__mutmut_7, 
    'x__validate_forbidden_imports__mutmut_8': x__validate_forbidden_imports__mutmut_8, 
    'x__validate_forbidden_imports__mutmut_9': x__validate_forbidden_imports__mutmut_9, 
    'x__validate_forbidden_imports__mutmut_10': x__validate_forbidden_imports__mutmut_10, 
    'x__validate_forbidden_imports__mutmut_11': x__validate_forbidden_imports__mutmut_11, 
    'x__validate_forbidden_imports__mutmut_12': x__validate_forbidden_imports__mutmut_12
}
x__validate_forbidden_imports__mutmut_orig.__name__ = 'x__validate_forbidden_imports'


def _validate_forbidden_calls(module: ModuleType) -> None:
    args = [module]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_forbidden_calls__mutmut_orig, x__validate_forbidden_calls__mutmut_mutants, args, kwargs, None)


def x__validate_forbidden_calls__mutmut_orig(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_1(module: ModuleType) -> None:
    tree = None

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_2(module: ModuleType) -> None:
    tree = _tree(None)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_3(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(None):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_4(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = None

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_5(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = "XXXX"

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_6(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = None
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_7(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = None

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_8(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES and name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_9(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name not in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_10(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name not in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(f"{module.__name__} uses forbidden call {name}")


def x__validate_forbidden_calls__mutmut_11(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name in FORBIDDEN_CALL_NAMES or name in FORBIDDEN_MUTATION_ATTRIBUTES:
                _fail(None)

x__validate_forbidden_calls__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_forbidden_calls__mutmut_1': x__validate_forbidden_calls__mutmut_1, 
    'x__validate_forbidden_calls__mutmut_2': x__validate_forbidden_calls__mutmut_2, 
    'x__validate_forbidden_calls__mutmut_3': x__validate_forbidden_calls__mutmut_3, 
    'x__validate_forbidden_calls__mutmut_4': x__validate_forbidden_calls__mutmut_4, 
    'x__validate_forbidden_calls__mutmut_5': x__validate_forbidden_calls__mutmut_5, 
    'x__validate_forbidden_calls__mutmut_6': x__validate_forbidden_calls__mutmut_6, 
    'x__validate_forbidden_calls__mutmut_7': x__validate_forbidden_calls__mutmut_7, 
    'x__validate_forbidden_calls__mutmut_8': x__validate_forbidden_calls__mutmut_8, 
    'x__validate_forbidden_calls__mutmut_9': x__validate_forbidden_calls__mutmut_9, 
    'x__validate_forbidden_calls__mutmut_10': x__validate_forbidden_calls__mutmut_10, 
    'x__validate_forbidden_calls__mutmut_11': x__validate_forbidden_calls__mutmut_11
}
x__validate_forbidden_calls__mutmut_orig.__name__ = 'x__validate_forbidden_calls'


def _validate_no_authority_literals(module: ModuleType) -> None:
    args = [module]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_no_authority_literals__mutmut_orig, x__validate_no_authority_literals__mutmut_mutants, args, kwargs, None)


def x__validate_no_authority_literals__mutmut_orig(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_1(module: ModuleType) -> None:
    tree = None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_2(module: ModuleType) -> None:
    tree = _tree(None)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_3(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(None):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_4(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = None

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_5(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") and name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_6(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith(None) or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_7(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("XX_AUTHORITYXX") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_8(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_authority") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_9(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name != "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_10(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "XXAUTHORITATIVEXX":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_11(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "authoritative":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_12(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) or node.value.value is True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_13(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is not True:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_14(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is False:
                            _fail(f"{module.__name__} sets {name}=True")


def x__validate_no_authority_literals__mutmut_15(module: ModuleType) -> None:
    tree = _tree(module)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    if name.endswith("_AUTHORITY") or name == "AUTHORITATIVE":
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            _fail(None)

x__validate_no_authority_literals__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_no_authority_literals__mutmut_1': x__validate_no_authority_literals__mutmut_1, 
    'x__validate_no_authority_literals__mutmut_2': x__validate_no_authority_literals__mutmut_2, 
    'x__validate_no_authority_literals__mutmut_3': x__validate_no_authority_literals__mutmut_3, 
    'x__validate_no_authority_literals__mutmut_4': x__validate_no_authority_literals__mutmut_4, 
    'x__validate_no_authority_literals__mutmut_5': x__validate_no_authority_literals__mutmut_5, 
    'x__validate_no_authority_literals__mutmut_6': x__validate_no_authority_literals__mutmut_6, 
    'x__validate_no_authority_literals__mutmut_7': x__validate_no_authority_literals__mutmut_7, 
    'x__validate_no_authority_literals__mutmut_8': x__validate_no_authority_literals__mutmut_8, 
    'x__validate_no_authority_literals__mutmut_9': x__validate_no_authority_literals__mutmut_9, 
    'x__validate_no_authority_literals__mutmut_10': x__validate_no_authority_literals__mutmut_10, 
    'x__validate_no_authority_literals__mutmut_11': x__validate_no_authority_literals__mutmut_11, 
    'x__validate_no_authority_literals__mutmut_12': x__validate_no_authority_literals__mutmut_12, 
    'x__validate_no_authority_literals__mutmut_13': x__validate_no_authority_literals__mutmut_13, 
    'x__validate_no_authority_literals__mutmut_14': x__validate_no_authority_literals__mutmut_14, 
    'x__validate_no_authority_literals__mutmut_15': x__validate_no_authority_literals__mutmut_15
}
x__validate_no_authority_literals__mutmut_orig.__name__ = 'x__validate_no_authority_literals'


def _validate_flags(module: ModuleType) -> None:
    args = [module]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_flags__mutmut_orig, x__validate_flags__mutmut_mutants, args, kwargs, None)


def x__validate_flags__mutmut_orig(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_1(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) or getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_2(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(None, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_3(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, None) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_4(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_5(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, ) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_6(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(None, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_7(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, None) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_8(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_9(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, ) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_10(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_11(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_12(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(None)

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_13(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) or getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_14(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(None, flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_15(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, None) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_16(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(flag) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_17(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, ) and getattr(module, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_18(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(None, flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_19(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, None) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_20(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(flag) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_21(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, ) is not True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_22(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is True:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_23(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be True")


def x__validate_flags__mutmut_24(module: ModuleType) -> None:
    for flag in REQUIRED_FALSE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not False:
            _fail(f"{module.__name__}.{flag} must be False")

    for flag in REQUIRED_TRUE_FLAGS:
        if hasattr(module, flag) and getattr(module, flag) is not True:
            _fail(None)

x__validate_flags__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_flags__mutmut_1': x__validate_flags__mutmut_1, 
    'x__validate_flags__mutmut_2': x__validate_flags__mutmut_2, 
    'x__validate_flags__mutmut_3': x__validate_flags__mutmut_3, 
    'x__validate_flags__mutmut_4': x__validate_flags__mutmut_4, 
    'x__validate_flags__mutmut_5': x__validate_flags__mutmut_5, 
    'x__validate_flags__mutmut_6': x__validate_flags__mutmut_6, 
    'x__validate_flags__mutmut_7': x__validate_flags__mutmut_7, 
    'x__validate_flags__mutmut_8': x__validate_flags__mutmut_8, 
    'x__validate_flags__mutmut_9': x__validate_flags__mutmut_9, 
    'x__validate_flags__mutmut_10': x__validate_flags__mutmut_10, 
    'x__validate_flags__mutmut_11': x__validate_flags__mutmut_11, 
    'x__validate_flags__mutmut_12': x__validate_flags__mutmut_12, 
    'x__validate_flags__mutmut_13': x__validate_flags__mutmut_13, 
    'x__validate_flags__mutmut_14': x__validate_flags__mutmut_14, 
    'x__validate_flags__mutmut_15': x__validate_flags__mutmut_15, 
    'x__validate_flags__mutmut_16': x__validate_flags__mutmut_16, 
    'x__validate_flags__mutmut_17': x__validate_flags__mutmut_17, 
    'x__validate_flags__mutmut_18': x__validate_flags__mutmut_18, 
    'x__validate_flags__mutmut_19': x__validate_flags__mutmut_19, 
    'x__validate_flags__mutmut_20': x__validate_flags__mutmut_20, 
    'x__validate_flags__mutmut_21': x__validate_flags__mutmut_21, 
    'x__validate_flags__mutmut_22': x__validate_flags__mutmut_22, 
    'x__validate_flags__mutmut_23': x__validate_flags__mutmut_23, 
    'x__validate_flags__mutmut_24': x__validate_flags__mutmut_24
}
x__validate_flags__mutmut_orig.__name__ = 'x__validate_flags'


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def _validate_contract() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_contract__mutmut_orig, x__validate_contract__mutmut_mutants, args, kwargs, None)


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_orig() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_1() -> None:
    metadata = None

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_2() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") and key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_3() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith(None) or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_4() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("XX_authorityXX") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_5() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_AUTHORITY") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_6() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key != "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_7() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "XXauthoritativeXX":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_8() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "AUTHORITATIVE":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_9() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_10() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not True:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_11() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(None)

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_12() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key not in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_13() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("XXread_onlyXX", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_14() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("READ_ONLY", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_15() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "XXdisplay_onlyXX", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_16() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "DISPLAY_ONLY", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_17() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "XXobservational_onlyXX"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_18() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "OBSERVATIONAL_ONLY"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_19() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_20() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not False:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_21() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(None)

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_22() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_23() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        None
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_24() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail(None)


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_25() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("XXDEFAULT_READ_ONLY_CONTRACT failed validationXX")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_26() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("default_read_only_contract failed validation")


# =============================================================================
# CONTRACT VALIDATION
# =============================================================================

def x__validate_contract__mutmut_27() -> None:
    metadata = read_only_contract.read_only_contract_metadata()

    for key, value in metadata.items():
        if key.endswith("_authority") or key == "authoritative":
            if value is not False:
                _fail(f"contract key {key} must be False")

        if key in ("read_only", "display_only", "observational_only"):
            if value is not True:
                _fail(f"contract key {key} must be True")

    if not read_only_contract.assert_read_only_contract(
        read_only_contract.DEFAULT_READ_ONLY_CONTRACT
    ):
        _fail("DEFAULT_READ_ONLY_CONTRACT FAILED VALIDATION")

x__validate_contract__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_contract__mutmut_1': x__validate_contract__mutmut_1, 
    'x__validate_contract__mutmut_2': x__validate_contract__mutmut_2, 
    'x__validate_contract__mutmut_3': x__validate_contract__mutmut_3, 
    'x__validate_contract__mutmut_4': x__validate_contract__mutmut_4, 
    'x__validate_contract__mutmut_5': x__validate_contract__mutmut_5, 
    'x__validate_contract__mutmut_6': x__validate_contract__mutmut_6, 
    'x__validate_contract__mutmut_7': x__validate_contract__mutmut_7, 
    'x__validate_contract__mutmut_8': x__validate_contract__mutmut_8, 
    'x__validate_contract__mutmut_9': x__validate_contract__mutmut_9, 
    'x__validate_contract__mutmut_10': x__validate_contract__mutmut_10, 
    'x__validate_contract__mutmut_11': x__validate_contract__mutmut_11, 
    'x__validate_contract__mutmut_12': x__validate_contract__mutmut_12, 
    'x__validate_contract__mutmut_13': x__validate_contract__mutmut_13, 
    'x__validate_contract__mutmut_14': x__validate_contract__mutmut_14, 
    'x__validate_contract__mutmut_15': x__validate_contract__mutmut_15, 
    'x__validate_contract__mutmut_16': x__validate_contract__mutmut_16, 
    'x__validate_contract__mutmut_17': x__validate_contract__mutmut_17, 
    'x__validate_contract__mutmut_18': x__validate_contract__mutmut_18, 
    'x__validate_contract__mutmut_19': x__validate_contract__mutmut_19, 
    'x__validate_contract__mutmut_20': x__validate_contract__mutmut_20, 
    'x__validate_contract__mutmut_21': x__validate_contract__mutmut_21, 
    'x__validate_contract__mutmut_22': x__validate_contract__mutmut_22, 
    'x__validate_contract__mutmut_23': x__validate_contract__mutmut_23, 
    'x__validate_contract__mutmut_24': x__validate_contract__mutmut_24, 
    'x__validate_contract__mutmut_25': x__validate_contract__mutmut_25, 
    'x__validate_contract__mutmut_26': x__validate_contract__mutmut_26, 
    'x__validate_contract__mutmut_27': x__validate_contract__mutmut_27
}
x__validate_contract__mutmut_orig.__name__ = 'x__validate_contract'


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def _immutable_check(obj: Any, extractor) -> None:
    args = [obj, extractor]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__immutable_check__mutmut_orig, x__immutable_check__mutmut_mutants, args, kwargs, None)


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_orig(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = extractor(obj)

    if before != mutated:
        _fail("immutability violation detected")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_1(obj: Any, extractor) -> None:
    before = None
    mutated = extractor(obj)

    if before != mutated:
        _fail("immutability violation detected")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_2(obj: Any, extractor) -> None:
    before = extractor(None)
    mutated = extractor(obj)

    if before != mutated:
        _fail("immutability violation detected")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_3(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = None

    if before != mutated:
        _fail("immutability violation detected")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_4(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = extractor(None)

    if before != mutated:
        _fail("immutability violation detected")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_5(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = extractor(obj)

    if before == mutated:
        _fail("immutability violation detected")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_6(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = extractor(obj)

    if before != mutated:
        _fail(None)


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_7(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = extractor(obj)

    if before != mutated:
        _fail("XXimmutability violation detectedXX")


# =============================================================================
# RUNTIME VALIDATION
# =============================================================================

def x__immutable_check__mutmut_8(obj: Any, extractor) -> None:
    before = extractor(obj)
    mutated = extractor(obj)

    if before != mutated:
        _fail("IMMUTABILITY VIOLATION DETECTED")

x__immutable_check__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__immutable_check__mutmut_1': x__immutable_check__mutmut_1, 
    'x__immutable_check__mutmut_2': x__immutable_check__mutmut_2, 
    'x__immutable_check__mutmut_3': x__immutable_check__mutmut_3, 
    'x__immutable_check__mutmut_4': x__immutable_check__mutmut_4, 
    'x__immutable_check__mutmut_5': x__immutable_check__mutmut_5, 
    'x__immutable_check__mutmut_6': x__immutable_check__mutmut_6, 
    'x__immutable_check__mutmut_7': x__immutable_check__mutmut_7, 
    'x__immutable_check__mutmut_8': x__immutable_check__mutmut_8
}
x__immutable_check__mutmut_orig.__name__ = 'x__immutable_check'


def _validate_receipt_provider() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_receipt_provider__mutmut_orig, x__validate_receipt_provider__mutmut_mutants, args, kwargs, None)


def x__validate_receipt_provider__mutmut_orig() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_1() -> None:
    receipt = None

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_2() -> None:
    receipt = {
        "XXexecution_idXX": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_3() -> None:
    receipt = {
        "EXECUTION_ID": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_4() -> None:
    receipt = {
        "execution_id": "XXexec-001XX",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_5() -> None:
    receipt = {
        "execution_id": "EXEC-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_6() -> None:
    receipt = {
        "execution_id": "exec-001",
        "XXgovernance_traceabilityXX": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_7() -> None:
    receipt = {
        "execution_id": "exec-001",
        "GOVERNANCE_TRACEABILITY": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_8() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"XXtypeXX": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_9() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"TYPE": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_10() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "XXADRXX", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_11() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "adr", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_12() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "XXidXX": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_13() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "ID": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_14() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "XXADR-1XX"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_15() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "adr-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_16() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = None
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_17() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider(None)
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_18() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = None

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_19() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = None

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_20() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[1]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_21() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["XXexecution_idXX"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_22() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["EXECUTION_ID"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_23() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "XXMUTATEDXX"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_24() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "mutated"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_25() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[1]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_26() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["XXexecution_idXX"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_27() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["EXECUTION_ID"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_28() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] == "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_29() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "XXexec-001XX":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_30() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "EXEC-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_31() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail(None)

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_32() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("XXreceipt provider mutated stateXX")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_33() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("RECEIPT PROVIDER MUTATED STATE")

    if provider.AUTHORITY is not False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_34() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is False:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_35() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not True:
        _fail("receipt provider has authority")


def x__validate_receipt_provider__mutmut_36() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail(None)


def x__validate_receipt_provider__mutmut_37() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("XXreceipt provider has authorityXX")


def x__validate_receipt_provider__mutmut_38() -> None:
    receipt = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-1"}],
    }

    provider = receipt_provider.build_receipt_provider((receipt,))
    base = provider.raw_receipts()

    base[0]["execution_id"] = "MUTATED"

    if provider.raw_receipts()[0]["execution_id"] != "exec-001":
        _fail("receipt provider mutated state")

    if provider.AUTHORITY is not False:
        _fail("RECEIPT PROVIDER HAS AUTHORITY")

x__validate_receipt_provider__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_receipt_provider__mutmut_1': x__validate_receipt_provider__mutmut_1, 
    'x__validate_receipt_provider__mutmut_2': x__validate_receipt_provider__mutmut_2, 
    'x__validate_receipt_provider__mutmut_3': x__validate_receipt_provider__mutmut_3, 
    'x__validate_receipt_provider__mutmut_4': x__validate_receipt_provider__mutmut_4, 
    'x__validate_receipt_provider__mutmut_5': x__validate_receipt_provider__mutmut_5, 
    'x__validate_receipt_provider__mutmut_6': x__validate_receipt_provider__mutmut_6, 
    'x__validate_receipt_provider__mutmut_7': x__validate_receipt_provider__mutmut_7, 
    'x__validate_receipt_provider__mutmut_8': x__validate_receipt_provider__mutmut_8, 
    'x__validate_receipt_provider__mutmut_9': x__validate_receipt_provider__mutmut_9, 
    'x__validate_receipt_provider__mutmut_10': x__validate_receipt_provider__mutmut_10, 
    'x__validate_receipt_provider__mutmut_11': x__validate_receipt_provider__mutmut_11, 
    'x__validate_receipt_provider__mutmut_12': x__validate_receipt_provider__mutmut_12, 
    'x__validate_receipt_provider__mutmut_13': x__validate_receipt_provider__mutmut_13, 
    'x__validate_receipt_provider__mutmut_14': x__validate_receipt_provider__mutmut_14, 
    'x__validate_receipt_provider__mutmut_15': x__validate_receipt_provider__mutmut_15, 
    'x__validate_receipt_provider__mutmut_16': x__validate_receipt_provider__mutmut_16, 
    'x__validate_receipt_provider__mutmut_17': x__validate_receipt_provider__mutmut_17, 
    'x__validate_receipt_provider__mutmut_18': x__validate_receipt_provider__mutmut_18, 
    'x__validate_receipt_provider__mutmut_19': x__validate_receipt_provider__mutmut_19, 
    'x__validate_receipt_provider__mutmut_20': x__validate_receipt_provider__mutmut_20, 
    'x__validate_receipt_provider__mutmut_21': x__validate_receipt_provider__mutmut_21, 
    'x__validate_receipt_provider__mutmut_22': x__validate_receipt_provider__mutmut_22, 
    'x__validate_receipt_provider__mutmut_23': x__validate_receipt_provider__mutmut_23, 
    'x__validate_receipt_provider__mutmut_24': x__validate_receipt_provider__mutmut_24, 
    'x__validate_receipt_provider__mutmut_25': x__validate_receipt_provider__mutmut_25, 
    'x__validate_receipt_provider__mutmut_26': x__validate_receipt_provider__mutmut_26, 
    'x__validate_receipt_provider__mutmut_27': x__validate_receipt_provider__mutmut_27, 
    'x__validate_receipt_provider__mutmut_28': x__validate_receipt_provider__mutmut_28, 
    'x__validate_receipt_provider__mutmut_29': x__validate_receipt_provider__mutmut_29, 
    'x__validate_receipt_provider__mutmut_30': x__validate_receipt_provider__mutmut_30, 
    'x__validate_receipt_provider__mutmut_31': x__validate_receipt_provider__mutmut_31, 
    'x__validate_receipt_provider__mutmut_32': x__validate_receipt_provider__mutmut_32, 
    'x__validate_receipt_provider__mutmut_33': x__validate_receipt_provider__mutmut_33, 
    'x__validate_receipt_provider__mutmut_34': x__validate_receipt_provider__mutmut_34, 
    'x__validate_receipt_provider__mutmut_35': x__validate_receipt_provider__mutmut_35, 
    'x__validate_receipt_provider__mutmut_36': x__validate_receipt_provider__mutmut_36, 
    'x__validate_receipt_provider__mutmut_37': x__validate_receipt_provider__mutmut_37, 
    'x__validate_receipt_provider__mutmut_38': x__validate_receipt_provider__mutmut_38
}
x__validate_receipt_provider__mutmut_orig.__name__ = 'x__validate_receipt_provider'


# =============================================================================
# DASHBOARD
# =============================================================================

def _validate_dashboard() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_dashboard__mutmut_orig, x__validate_dashboard__mutmut_mutants, args, kwargs, None)


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_orig() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_1() -> None:
    receipts = None

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_2() -> None:
    receipts = (
        {"XXexecution_idXX": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_3() -> None:
    receipts = (
        {"EXECUTION_ID": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_4() -> None:
    receipts = (
        {"execution_id": "XXe1XX", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_5() -> None:
    receipts = (
        {"execution_id": "E1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_6() -> None:
    receipts = (
        {"execution_id": "e1", "XXgovernance_traceabilityXX": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_7() -> None:
    receipts = (
        {"execution_id": "e1", "GOVERNANCE_TRACEABILITY": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_8() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"XXtypeXX": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_9() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"TYPE": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_10() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "XXADRXX","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_11() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "adr","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_12() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","XXidXX": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_13() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","ID": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_14() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "XXADR-1XX"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_15() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "adr-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_16() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = None

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_17() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(None)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_18() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get(None) is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_19() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("XXread_onlyXX") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_20() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("READ_ONLY") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_21() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_22() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not False:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_23() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail(None)

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_24() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("XXdashboard must be read_onlyXX")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_25() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("DASHBOARD MUST BE READ_ONLY")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_26() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get(None) is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_27() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("XXobservational_onlyXX") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_28() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("OBSERVATIONAL_ONLY") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_29() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_30() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not False:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_31() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail(None)

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_32() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("XXdashboard must be observational_onlyXX")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_33() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("DASHBOARD MUST BE OBSERVATIONAL_ONLY")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_34() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = None
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_35() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(None)
    if not isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_36() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if isinstance(mp.get("metrics"), dict):
        _fail("dashboard metrics invalid")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_37() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail(None)


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_38() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("XXdashboard metrics invalidXX")


# =============================================================================
# DASHBOARD
# =============================================================================

def x__validate_dashboard__mutmut_39() -> None:
    receipts = (
        {"execution_id": "e1", "governance_traceability": [{"type": "ADR","id": "ADR-1"}]},
    )

    payload = services.build_dashboard_payload(receipts)

    if payload.get("read_only") is not True:
        _fail("dashboard must be read_only")

    if payload.get("observational_only") is not True:
        _fail("dashboard must be observational_only")

    mp = metrics.build_metric_payload(receipts)
    if not isinstance(mp.get("metrics"), dict):
        _fail("DASHBOARD METRICS INVALID")

x__validate_dashboard__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_dashboard__mutmut_1': x__validate_dashboard__mutmut_1, 
    'x__validate_dashboard__mutmut_2': x__validate_dashboard__mutmut_2, 
    'x__validate_dashboard__mutmut_3': x__validate_dashboard__mutmut_3, 
    'x__validate_dashboard__mutmut_4': x__validate_dashboard__mutmut_4, 
    'x__validate_dashboard__mutmut_5': x__validate_dashboard__mutmut_5, 
    'x__validate_dashboard__mutmut_6': x__validate_dashboard__mutmut_6, 
    'x__validate_dashboard__mutmut_7': x__validate_dashboard__mutmut_7, 
    'x__validate_dashboard__mutmut_8': x__validate_dashboard__mutmut_8, 
    'x__validate_dashboard__mutmut_9': x__validate_dashboard__mutmut_9, 
    'x__validate_dashboard__mutmut_10': x__validate_dashboard__mutmut_10, 
    'x__validate_dashboard__mutmut_11': x__validate_dashboard__mutmut_11, 
    'x__validate_dashboard__mutmut_12': x__validate_dashboard__mutmut_12, 
    'x__validate_dashboard__mutmut_13': x__validate_dashboard__mutmut_13, 
    'x__validate_dashboard__mutmut_14': x__validate_dashboard__mutmut_14, 
    'x__validate_dashboard__mutmut_15': x__validate_dashboard__mutmut_15, 
    'x__validate_dashboard__mutmut_16': x__validate_dashboard__mutmut_16, 
    'x__validate_dashboard__mutmut_17': x__validate_dashboard__mutmut_17, 
    'x__validate_dashboard__mutmut_18': x__validate_dashboard__mutmut_18, 
    'x__validate_dashboard__mutmut_19': x__validate_dashboard__mutmut_19, 
    'x__validate_dashboard__mutmut_20': x__validate_dashboard__mutmut_20, 
    'x__validate_dashboard__mutmut_21': x__validate_dashboard__mutmut_21, 
    'x__validate_dashboard__mutmut_22': x__validate_dashboard__mutmut_22, 
    'x__validate_dashboard__mutmut_23': x__validate_dashboard__mutmut_23, 
    'x__validate_dashboard__mutmut_24': x__validate_dashboard__mutmut_24, 
    'x__validate_dashboard__mutmut_25': x__validate_dashboard__mutmut_25, 
    'x__validate_dashboard__mutmut_26': x__validate_dashboard__mutmut_26, 
    'x__validate_dashboard__mutmut_27': x__validate_dashboard__mutmut_27, 
    'x__validate_dashboard__mutmut_28': x__validate_dashboard__mutmut_28, 
    'x__validate_dashboard__mutmut_29': x__validate_dashboard__mutmut_29, 
    'x__validate_dashboard__mutmut_30': x__validate_dashboard__mutmut_30, 
    'x__validate_dashboard__mutmut_31': x__validate_dashboard__mutmut_31, 
    'x__validate_dashboard__mutmut_32': x__validate_dashboard__mutmut_32, 
    'x__validate_dashboard__mutmut_33': x__validate_dashboard__mutmut_33, 
    'x__validate_dashboard__mutmut_34': x__validate_dashboard__mutmut_34, 
    'x__validate_dashboard__mutmut_35': x__validate_dashboard__mutmut_35, 
    'x__validate_dashboard__mutmut_36': x__validate_dashboard__mutmut_36, 
    'x__validate_dashboard__mutmut_37': x__validate_dashboard__mutmut_37, 
    'x__validate_dashboard__mutmut_38': x__validate_dashboard__mutmut_38, 
    'x__validate_dashboard__mutmut_39': x__validate_dashboard__mutmut_39
}
x__validate_dashboard__mutmut_orig.__name__ = 'x__validate_dashboard'


# =============================================================================
# REASONING
# =============================================================================

def _validate_reasoning() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_reasoning__mutmut_orig, x__validate_reasoning__mutmut_mutants, args, kwargs, None)


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_orig() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_1() -> None:
    receipts = None

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_2() -> None:
    receipts = (
        {"XXexecution_idXX": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_3() -> None:
    receipts = (
        {"EXECUTION_ID": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_4() -> None:
    receipts = (
        {"execution_id": "XXe1XX","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_5() -> None:
    receipts = (
        {"execution_id": "E1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_6() -> None:
    receipts = (
        {"execution_id": "e1","XXgovernance_traceabilityXX": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_7() -> None:
    receipts = (
        {"execution_id": "e1","GOVERNANCE_TRACEABILITY": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_8() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"XXtypeXX":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_9() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"TYPE":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_10() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"XXADRXX","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_11() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"adr","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_12() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","XXidXX":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_13() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","ID":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_14() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"XXADR-1XX"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_15() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"adr-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_16() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = None

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_17() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(None)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_18() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get(None) is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_19() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("XXinterpretive_onlyXX") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_20() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("INTERPRETIVE_ONLY") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_21() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_22() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not False:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_23() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail(None)

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_24() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("XXreasoning must be interpretive_onlyXX")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_25() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("REASONING MUST BE INTERPRETIVE_ONLY")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_26() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = None

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_27() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(None, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_28() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=None)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_29() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_30() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, )

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_31() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=1)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_32() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get(None) is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_33() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("XXauthoritativeXX") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_34() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("AUTHORITATIVE") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_35() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_36() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not True:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_37() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail(None)

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_38() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("XXinsights must be non-authoritativeXX")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_39() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("INSIGHTS MUST BE NON-AUTHORITATIVE")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_40() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = None

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_41() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(None, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_42() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, None)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_43() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_44() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, )

    if explanation.get("authoritative") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_45() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get(None) is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_46() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("XXauthoritativeXX") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_47() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("AUTHORITATIVE") is not False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_48() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is False:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_49() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not True:
        _fail("explanations must be non-authoritative")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_50() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail(None)


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_51() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("XXexplanations must be non-authoritativeXX")


# =============================================================================
# REASONING
# =============================================================================

def x__validate_reasoning__mutmut_52() -> None:
    receipts = (
        {"execution_id": "e1","governance_traceability": [{"type":"ADR","id":"ADR-1"}]},
    )

    patterns = engine.extract_patterns(receipts)

    if patterns.get("interpretive_only") is not True:
        _fail("reasoning must be interpretive_only")

    insights_payload = insights.build_insight_payload(patterns, threshold=0)

    if insights_payload.get("authoritative") is not False:
        _fail("insights must be non-authoritative")

    explanation = explain.build_reasoning_explanation_payload(patterns, insights_payload)

    if explanation.get("authoritative") is not False:
        _fail("EXPLANATIONS MUST BE NON-AUTHORITATIVE")

x__validate_reasoning__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_reasoning__mutmut_1': x__validate_reasoning__mutmut_1, 
    'x__validate_reasoning__mutmut_2': x__validate_reasoning__mutmut_2, 
    'x__validate_reasoning__mutmut_3': x__validate_reasoning__mutmut_3, 
    'x__validate_reasoning__mutmut_4': x__validate_reasoning__mutmut_4, 
    'x__validate_reasoning__mutmut_5': x__validate_reasoning__mutmut_5, 
    'x__validate_reasoning__mutmut_6': x__validate_reasoning__mutmut_6, 
    'x__validate_reasoning__mutmut_7': x__validate_reasoning__mutmut_7, 
    'x__validate_reasoning__mutmut_8': x__validate_reasoning__mutmut_8, 
    'x__validate_reasoning__mutmut_9': x__validate_reasoning__mutmut_9, 
    'x__validate_reasoning__mutmut_10': x__validate_reasoning__mutmut_10, 
    'x__validate_reasoning__mutmut_11': x__validate_reasoning__mutmut_11, 
    'x__validate_reasoning__mutmut_12': x__validate_reasoning__mutmut_12, 
    'x__validate_reasoning__mutmut_13': x__validate_reasoning__mutmut_13, 
    'x__validate_reasoning__mutmut_14': x__validate_reasoning__mutmut_14, 
    'x__validate_reasoning__mutmut_15': x__validate_reasoning__mutmut_15, 
    'x__validate_reasoning__mutmut_16': x__validate_reasoning__mutmut_16, 
    'x__validate_reasoning__mutmut_17': x__validate_reasoning__mutmut_17, 
    'x__validate_reasoning__mutmut_18': x__validate_reasoning__mutmut_18, 
    'x__validate_reasoning__mutmut_19': x__validate_reasoning__mutmut_19, 
    'x__validate_reasoning__mutmut_20': x__validate_reasoning__mutmut_20, 
    'x__validate_reasoning__mutmut_21': x__validate_reasoning__mutmut_21, 
    'x__validate_reasoning__mutmut_22': x__validate_reasoning__mutmut_22, 
    'x__validate_reasoning__mutmut_23': x__validate_reasoning__mutmut_23, 
    'x__validate_reasoning__mutmut_24': x__validate_reasoning__mutmut_24, 
    'x__validate_reasoning__mutmut_25': x__validate_reasoning__mutmut_25, 
    'x__validate_reasoning__mutmut_26': x__validate_reasoning__mutmut_26, 
    'x__validate_reasoning__mutmut_27': x__validate_reasoning__mutmut_27, 
    'x__validate_reasoning__mutmut_28': x__validate_reasoning__mutmut_28, 
    'x__validate_reasoning__mutmut_29': x__validate_reasoning__mutmut_29, 
    'x__validate_reasoning__mutmut_30': x__validate_reasoning__mutmut_30, 
    'x__validate_reasoning__mutmut_31': x__validate_reasoning__mutmut_31, 
    'x__validate_reasoning__mutmut_32': x__validate_reasoning__mutmut_32, 
    'x__validate_reasoning__mutmut_33': x__validate_reasoning__mutmut_33, 
    'x__validate_reasoning__mutmut_34': x__validate_reasoning__mutmut_34, 
    'x__validate_reasoning__mutmut_35': x__validate_reasoning__mutmut_35, 
    'x__validate_reasoning__mutmut_36': x__validate_reasoning__mutmut_36, 
    'x__validate_reasoning__mutmut_37': x__validate_reasoning__mutmut_37, 
    'x__validate_reasoning__mutmut_38': x__validate_reasoning__mutmut_38, 
    'x__validate_reasoning__mutmut_39': x__validate_reasoning__mutmut_39, 
    'x__validate_reasoning__mutmut_40': x__validate_reasoning__mutmut_40, 
    'x__validate_reasoning__mutmut_41': x__validate_reasoning__mutmut_41, 
    'x__validate_reasoning__mutmut_42': x__validate_reasoning__mutmut_42, 
    'x__validate_reasoning__mutmut_43': x__validate_reasoning__mutmut_43, 
    'x__validate_reasoning__mutmut_44': x__validate_reasoning__mutmut_44, 
    'x__validate_reasoning__mutmut_45': x__validate_reasoning__mutmut_45, 
    'x__validate_reasoning__mutmut_46': x__validate_reasoning__mutmut_46, 
    'x__validate_reasoning__mutmut_47': x__validate_reasoning__mutmut_47, 
    'x__validate_reasoning__mutmut_48': x__validate_reasoning__mutmut_48, 
    'x__validate_reasoning__mutmut_49': x__validate_reasoning__mutmut_49, 
    'x__validate_reasoning__mutmut_50': x__validate_reasoning__mutmut_50, 
    'x__validate_reasoning__mutmut_51': x__validate_reasoning__mutmut_51, 
    'x__validate_reasoning__mutmut_52': x__validate_reasoning__mutmut_52
}
x__validate_reasoning__mutmut_orig.__name__ = 'x__validate_reasoning'


# =============================================================================
# GRAPH
# =============================================================================

def _validate_graph() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_graph__mutmut_orig, x__validate_graph__mutmut_mutants, args, kwargs, None)


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_orig() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_1() -> None:
    receipts = None

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_2() -> None:
    receipts = (
        {"XXexecution_idXX":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_3() -> None:
    receipts = (
        {"EXECUTION_ID":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_4() -> None:
    receipts = (
        {"execution_id":"XXe1XX","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_5() -> None:
    receipts = (
        {"execution_id":"E1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_6() -> None:
    receipts = (
        {"execution_id":"e1","XXgovernance_traceabilityXX":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_7() -> None:
    receipts = (
        {"execution_id":"e1","GOVERNANCE_TRACEABILITY":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_8() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"XXtypeXX":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_9() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"TYPE":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_10() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"XXADRXX","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_11() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"adr","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_12() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","XXidXX":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_13() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","ID":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_14() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"XXADR-1XX"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_15() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"adr-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_16() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = None

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_17() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(None)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_18() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get(None) is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_19() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("XXauthoritativeXX") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_20() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("AUTHORITATIVE") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_21() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_22() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not True:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_23() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail(None)

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_24() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("XXgraph must be non-authoritativeXX")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_25() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("GRAPH MUST BE NON-AUTHORITATIVE")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_26() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = None

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_27() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(None)

    if summary.get("representation_only") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_28() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get(None) is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_29() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("XXrepresentation_onlyXX") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_30() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("REPRESENTATION_ONLY") is not True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_31() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is True:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_32() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not False:
        _fail("graph query must be representation-only")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_33() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail(None)


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_34() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("XXgraph query must be representation-onlyXX")


# =============================================================================
# GRAPH
# =============================================================================

def x__validate_graph__mutmut_35() -> None:
    receipts = (
        {"execution_id":"e1","governance_traceability":[{"type":"ADR","id":"ADR-1"}]},
    )

    graph = projection.project_graph(receipts)

    if graph.get("authoritative") is not False:
        _fail("graph must be non-authoritative")

    summary = query.build_graph_query_summary(graph)

    if summary.get("representation_only") is not True:
        _fail("GRAPH QUERY MUST BE REPRESENTATION-ONLY")

x__validate_graph__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_graph__mutmut_1': x__validate_graph__mutmut_1, 
    'x__validate_graph__mutmut_2': x__validate_graph__mutmut_2, 
    'x__validate_graph__mutmut_3': x__validate_graph__mutmut_3, 
    'x__validate_graph__mutmut_4': x__validate_graph__mutmut_4, 
    'x__validate_graph__mutmut_5': x__validate_graph__mutmut_5, 
    'x__validate_graph__mutmut_6': x__validate_graph__mutmut_6, 
    'x__validate_graph__mutmut_7': x__validate_graph__mutmut_7, 
    'x__validate_graph__mutmut_8': x__validate_graph__mutmut_8, 
    'x__validate_graph__mutmut_9': x__validate_graph__mutmut_9, 
    'x__validate_graph__mutmut_10': x__validate_graph__mutmut_10, 
    'x__validate_graph__mutmut_11': x__validate_graph__mutmut_11, 
    'x__validate_graph__mutmut_12': x__validate_graph__mutmut_12, 
    'x__validate_graph__mutmut_13': x__validate_graph__mutmut_13, 
    'x__validate_graph__mutmut_14': x__validate_graph__mutmut_14, 
    'x__validate_graph__mutmut_15': x__validate_graph__mutmut_15, 
    'x__validate_graph__mutmut_16': x__validate_graph__mutmut_16, 
    'x__validate_graph__mutmut_17': x__validate_graph__mutmut_17, 
    'x__validate_graph__mutmut_18': x__validate_graph__mutmut_18, 
    'x__validate_graph__mutmut_19': x__validate_graph__mutmut_19, 
    'x__validate_graph__mutmut_20': x__validate_graph__mutmut_20, 
    'x__validate_graph__mutmut_21': x__validate_graph__mutmut_21, 
    'x__validate_graph__mutmut_22': x__validate_graph__mutmut_22, 
    'x__validate_graph__mutmut_23': x__validate_graph__mutmut_23, 
    'x__validate_graph__mutmut_24': x__validate_graph__mutmut_24, 
    'x__validate_graph__mutmut_25': x__validate_graph__mutmut_25, 
    'x__validate_graph__mutmut_26': x__validate_graph__mutmut_26, 
    'x__validate_graph__mutmut_27': x__validate_graph__mutmut_27, 
    'x__validate_graph__mutmut_28': x__validate_graph__mutmut_28, 
    'x__validate_graph__mutmut_29': x__validate_graph__mutmut_29, 
    'x__validate_graph__mutmut_30': x__validate_graph__mutmut_30, 
    'x__validate_graph__mutmut_31': x__validate_graph__mutmut_31, 
    'x__validate_graph__mutmut_32': x__validate_graph__mutmut_32, 
    'x__validate_graph__mutmut_33': x__validate_graph__mutmut_33, 
    'x__validate_graph__mutmut_34': x__validate_graph__mutmut_34, 
    'x__validate_graph__mutmut_35': x__validate_graph__mutmut_35
}
x__validate_graph__mutmut_orig.__name__ = 'x__validate_graph'


# =============================================================================
# ENTRY
# =============================================================================

def validate_afripower_intelligence() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_validate_afripower_intelligence__mutmut_orig, x_validate_afripower_intelligence__mutmut_mutants, args, kwargs, None)


# =============================================================================
# ENTRY
# =============================================================================

def x_validate_afripower_intelligence__mutmut_orig() -> None:
    for module in MODULES_TO_SCAN:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(module)
        _validate_no_authority_literals(module)
        _validate_flags(module)

    _validate_contract()
    _validate_receipt_provider()
    _validate_dashboard()
    _validate_reasoning()
    _validate_graph()


# =============================================================================
# ENTRY
# =============================================================================

def x_validate_afripower_intelligence__mutmut_1() -> None:
    for module in MODULES_TO_SCAN:
        _validate_forbidden_imports(None)
        _validate_forbidden_calls(module)
        _validate_no_authority_literals(module)
        _validate_flags(module)

    _validate_contract()
    _validate_receipt_provider()
    _validate_dashboard()
    _validate_reasoning()
    _validate_graph()


# =============================================================================
# ENTRY
# =============================================================================

def x_validate_afripower_intelligence__mutmut_2() -> None:
    for module in MODULES_TO_SCAN:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(None)
        _validate_no_authority_literals(module)
        _validate_flags(module)

    _validate_contract()
    _validate_receipt_provider()
    _validate_dashboard()
    _validate_reasoning()
    _validate_graph()


# =============================================================================
# ENTRY
# =============================================================================

def x_validate_afripower_intelligence__mutmut_3() -> None:
    for module in MODULES_TO_SCAN:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(module)
        _validate_no_authority_literals(None)
        _validate_flags(module)

    _validate_contract()
    _validate_receipt_provider()
    _validate_dashboard()
    _validate_reasoning()
    _validate_graph()


# =============================================================================
# ENTRY
# =============================================================================

def x_validate_afripower_intelligence__mutmut_4() -> None:
    for module in MODULES_TO_SCAN:
        _validate_forbidden_imports(module)
        _validate_forbidden_calls(module)
        _validate_no_authority_literals(module)
        _validate_flags(None)

    _validate_contract()
    _validate_receipt_provider()
    _validate_dashboard()
    _validate_reasoning()
    _validate_graph()

x_validate_afripower_intelligence__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_validate_afripower_intelligence__mutmut_1': x_validate_afripower_intelligence__mutmut_1, 
    'x_validate_afripower_intelligence__mutmut_2': x_validate_afripower_intelligence__mutmut_2, 
    'x_validate_afripower_intelligence__mutmut_3': x_validate_afripower_intelligence__mutmut_3, 
    'x_validate_afripower_intelligence__mutmut_4': x_validate_afripower_intelligence__mutmut_4
}
x_validate_afripower_intelligence__mutmut_orig.__name__ = 'x_validate_afripower_intelligence'


def main() -> None:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_main__mutmut_orig, x_main__mutmut_mutants, args, kwargs, None)


def x_main__mutmut_orig() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(1)

    print("AFRIPower validation PASSED")


def x_main__mutmut_1() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(None)
        sys.exit(1)

    print("AFRIPower validation PASSED")


def x_main__mutmut_2() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(None)

    print("AFRIPower validation PASSED")


def x_main__mutmut_3() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(2)

    print("AFRIPower validation PASSED")


def x_main__mutmut_4() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(1)

    print(None)


def x_main__mutmut_5() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(1)

    print("XXAFRIPower validation PASSEDXX")


def x_main__mutmut_6() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(1)

    print("afripower validation passed")


def x_main__mutmut_7() -> None:
    try:
        validate_afripower_intelligence()
    except AFRIPowerIntelligenceValidationError as exc:
        print(f"AFRIPower validation FAILED: {exc}")
        sys.exit(1)

    print("AFRIPOWER VALIDATION PASSED")

x_main__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_main__mutmut_1': x_main__mutmut_1, 
    'x_main__mutmut_2': x_main__mutmut_2, 
    'x_main__mutmut_3': x_main__mutmut_3, 
    'x_main__mutmut_4': x_main__mutmut_4, 
    'x_main__mutmut_5': x_main__mutmut_5, 
    'x_main__mutmut_6': x_main__mutmut_6, 
    'x_main__mutmut_7': x_main__mutmut_7
}
x_main__mutmut_orig.__name__ = 'x_main'


if __name__ == "__main__":
    main()