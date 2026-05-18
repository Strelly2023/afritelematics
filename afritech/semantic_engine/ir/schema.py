from dataclasses import dataclass
from typing import Any

@dataclass
class SystemInvalid(Exception):
    reason: str

    def __str__(self) -> str:
        return f"SYSTEM_INVALID: {self.reason}"


@dataclass(frozen=True)
class Expression:
    operator: str
    operands: tuple[Any, ...]

@dataclass
class Axiom:
    id: str
    expression: Expression


@dataclass(frozen=True)
class SemanticProgram:
    id: str
    expression: Expression | str
    declared_symbols: frozenset[str]
