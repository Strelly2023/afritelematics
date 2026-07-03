from __future__ import annotations

from collections.abc import Callable, Iterable

from architecture_validator.engine.context import ValidatorContext
from architecture_validator.model import RuleResult


RuleCallable = Callable[[dict[str, object]], RuleResult]


def run_rules(context: ValidatorContext, rules: Iterable[RuleCallable]) -> list[RuleResult]:
    return [rule(context.config) for rule in rules]
