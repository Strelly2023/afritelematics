from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.ast_engine.python import PythonASTScanner
from architecture_validator.scanners.ast_engine.solidity import SolidityASTScanner
from architecture_validator.scanners.ast_engine.typescript import TypeScriptASTScanner


def check_ast_validation(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    scanners = (
        PythonASTScanner(
            config.get("python_ast_source_roots", config.get("ast_source_roots", [])),
            config.get("forbidden_python_call_names", []),
        ),
        TypeScriptASTScanner(
            config.get("typescript_ast_source_roots", config.get("ui_source_roots", [])),
            config.get("forbidden_typescript_patterns", []),
        ),
        SolidityASTScanner(
            config.get("solidity_ast_source_roots", []),
            config.get("forbidden_solidity_patterns", []),
        ),
    )

    for scanner in scanners:
        issues.extend(scanner.scan())

    return pass_or_fail("Multi-Language AST Validation", issues)
