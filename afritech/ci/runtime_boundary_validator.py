"""Validate the FastAPI vs Django runtime boundary and report violations."""

from __future__ import annotations

import ast
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STARTUP_MODULE = "afritech.api.app"
DEFAULT_SCAN_PREFIXES = (
    "afritech.api",
    "afritech.edge",
    "afritech.execution",
    "afritech.monitoring",
    "afritech.security",
    "afritech.partner_registry",
    "afritech.partner_verification",
    "afritech.standards_dependency",
    "afritech.trust_network",
)
FRAMEWORK_PREFIXES = ("django", "rest_framework")


@dataclass(frozen=True)
class BoundaryViolation:
    """One runtime-boundary violation."""

    code: str
    severity: str
    module: str
    path: str
    detail: str
    import_chain: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModuleScan:
    """Static scan result for one module."""

    module: str
    path: Path
    direct_framework_imports: tuple[str, ...]
    top_level_manager_calls: tuple[str, ...]
    afritech_imports: tuple[str, ...]

    @property
    def is_django_bound(self) -> bool:
        return bool(self.direct_framework_imports or self.top_level_manager_calls)


@dataclass(frozen=True)
class BoundaryReport:
    """Structured report emitted by the validator."""

    startup_module: str
    scanned_modules: int
    startup_modules: tuple[str, ...]
    declared_django_modules: tuple[str, ...]
    violations: tuple[BoundaryViolation, ...]

    def to_markdown(self) -> str:
        lines = [
            "# AfriTech Runtime Boundary Scan",
            "",
            f"- Startup module: `{self.startup_module}`",
            f"- Scanned modules: `{self.scanned_modules}`",
            f"- Startup-path modules discovered: `{len(self.startup_modules)}`",
            f"- Declared Django-bound modules discovered: `{len(self.declared_django_modules)}`",
            f"- Violations: `{len(self.violations)}`",
            "",
        ]

        if not self.violations:
            lines.extend(
                [
                    "## Result",
                    "",
                    "No runtime-boundary violations detected.",
                ]
            )
            return "\n".join(lines) + "\n"

        lines.extend(["## Violations", ""])
        for violation in self.violations:
            lines.append(
                f"- `{violation.severity}` `{violation.code}` `{violation.module}`: {violation.detail}"
            )
            if violation.import_chain:
                lines.append(f"  Chain: `{' -> '.join(violation.import_chain)}`")
            lines.append(f"  Path: `{violation.path}`")
        return "\n".join(lines) + "\n"


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def _coerce_violation(value: Any) -> BoundaryViolation:
    if isinstance(value, BoundaryViolation):
        return value
    if not isinstance(value, dict):
        return BoundaryViolation(
            code=str(getattr(value, "code", "")),
            severity=str(getattr(value, "severity", "")),
            module=str(getattr(value, "module", "")),
            path=str(getattr(value, "path", "")),
            detail=str(getattr(value, "detail", "")),
            import_chain=_tuple_of_strings(getattr(value, "import_chain", ())),
        )
    return BoundaryViolation(
        code=str(value.get("code", "")),
        severity=str(value.get("severity", "")),
        module=str(value.get("module", "")),
        path=str(value.get("path", "")),
        detail=str(value.get("detail", "")),
        import_chain=_tuple_of_strings(value.get("import_chain", ())),
    )


def _report_value(report: Any, name: str, default: Any = None) -> Any:
    if isinstance(report, dict):
        return report.get(name, default)
    return getattr(report, name, default)


def coerce_boundary_report(report: Any) -> BoundaryReport:
    """Return a BoundaryReport from object, fallback-object, or serialized dict shape."""

    violations = _report_value(report, "violations", ())
    if not isinstance(violations, (list, tuple)):
        violations = ()

    startup_modules = _report_value(report, "startup_modules", ())
    declared_django_modules = _report_value(
        report,
        "declared_django_modules",
        _report_value(report, "django_modules", ()),
    )
    scanned_modules = _report_value(report, "scanned_modules")
    modules = _report_value(report, "modules", ())
    if scanned_modules is None and isinstance(modules, (list, tuple)):
        scanned_modules = len(modules)

    return BoundaryReport(
        startup_module=str(_report_value(report, "startup_module", DEFAULT_STARTUP_MODULE)),
        scanned_modules=int(scanned_modules) if isinstance(scanned_modules, (int, str)) else 0,
        startup_modules=_tuple_of_strings(startup_modules),
        declared_django_modules=_tuple_of_strings(declared_django_modules),
        violations=tuple(_coerce_violation(item) for item in violations),
    )


class RuntimeBoundaryValidationError(RuntimeError):
    """Raised when the validator is asked to fail closed."""


class RuntimeBoundaryValidator:
    """Static validator for the FastAPI vs Django startup boundary."""

    def __init__(
        self,
        *,
        root: Path | None = None,
        startup_module: str = DEFAULT_STARTUP_MODULE,
        scan_prefixes: tuple[str, ...] = DEFAULT_SCAN_PREFIXES,
    ) -> None:
        self.root = (root or PROJECT_ROOT).resolve()
        self.startup_module = startup_module
        self.scan_prefixes = scan_prefixes
        self.package_prefix = startup_module.split(".", 1)[0]

    def build_report(self) -> BoundaryReport:
        modules = self._discover_modules()
        scans = {module: self._scan_module(path, module) for module, path in modules.items()}
        startup_closure = self._startup_closure(scans)
        violations = self._detect_violations(scans, startup_closure)
        declared = tuple(sorted(module for module, scan in scans.items() if self._is_declared_django_surface(module, scan.path)))
        return BoundaryReport(
            startup_module=self.startup_module,
            scanned_modules=len(scans),
            startup_modules=tuple(sorted(startup_closure)),
            declared_django_modules=declared,
            violations=tuple(violations),
        )

    def validate(self) -> bool:
        report = self.build_report()
        if report.violations:
            raise RuntimeBoundaryValidationError(report.to_markdown())
        return True

    def _discover_modules(self) -> dict[str, Path]:
        modules: dict[str, Path] = {}
        for path in self.root.rglob("*.py"):
            if any(part in {"__pycache__", ".git", "venv", ".venv", "node_modules"} for part in path.parts):
                continue
            module = self._module_name_from_path(path)
            if module:
                existing = modules.get(module)
                if existing is None:
                    modules[module] = path
                elif existing.name == "__init__.py" and path.name != "__init__.py":
                    modules[module] = path
        return modules

    def _module_name_from_path(self, path: Path) -> str | None:
        try:
            relative = path.relative_to(self.root)
        except ValueError:
            return None
        if relative.name == "__init__.py":
            relative = relative.parent
        else:
            relative = relative.with_suffix("")
        return ".".join(relative.parts)

    def _module_path(self, module: str) -> Path | None:
        file_candidate = self.root / Path(*module.split("."))
        py_candidate = file_candidate.with_suffix(".py")
        if py_candidate.exists():
            return py_candidate
        init_candidate = file_candidate / "__init__.py"
        if init_candidate.exists():
            return init_candidate
        return None

    def _parse(self, path: Path) -> ast.AST:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def _scan_module(self, path: Path, module: str) -> ModuleScan:
        tree = self._parse(path)
        direct_framework_imports: list[str] = []
        top_level_manager_calls: list[str] = []
        afritech_imports: list[str] = []

        for statement in self._iter_top_level_nodes(tree):
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    name = alias.name
                    if name.startswith(FRAMEWORK_PREFIXES):
                        direct_framework_imports.append(name)
                    if name.startswith(self.package_prefix):
                        afritech_imports.extend(self._expand_imported_modules(name))

            elif isinstance(statement, ast.ImportFrom):
                resolved = self._resolve_from_import(module, statement)
                if not resolved:
                    continue
                for imported in resolved:
                    if imported.startswith(FRAMEWORK_PREFIXES):
                        direct_framework_imports.append(imported)
                    if imported.startswith(self.package_prefix):
                        afritech_imports.extend(self._expand_imported_modules(imported))

            elif isinstance(statement, ast.Expr):
                top_level_manager_calls.extend(self._extract_manager_calls(statement.value))

            elif isinstance(statement, ast.Assign):
                top_level_manager_calls.extend(self._extract_manager_calls(statement.value))

            elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
                top_level_manager_calls.extend(self._extract_manager_calls(statement.value))

        return ModuleScan(
            module=module,
            path=path,
            direct_framework_imports=tuple(sorted(set(direct_framework_imports))),
            top_level_manager_calls=tuple(sorted(set(top_level_manager_calls))),
            afritech_imports=tuple(sorted(set(afritech_imports))),
        )

    def _iter_top_level_nodes(self, tree: ast.AST) -> Iterable[ast.stmt]:
        assert isinstance(tree, ast.Module)
        for node in tree.body:
            yield from self._flatten_statement(node)

    def _flatten_statement(self, node: ast.stmt) -> Iterable[ast.stmt]:
        yield node
        if isinstance(node, ast.Try):
            for child in node.body:
                yield from self._flatten_statement(child)
            for handler in node.handlers:
                for child in handler.body:
                    yield from self._flatten_statement(child)
            for child in node.orelse:
                yield from self._flatten_statement(child)
            for child in node.finalbody:
                yield from self._flatten_statement(child)
        elif isinstance(node, ast.If):
            for child in node.body:
                yield from self._flatten_statement(child)
            for child in node.orelse:
                yield from self._flatten_statement(child)

    def _resolve_from_import(self, module: str, node: ast.ImportFrom) -> tuple[str, ...]:
        base = node.module or ""
        if node.level:
            package_parts = module.split(".")
            module_path = self._module_path(module)
            if module_path is not None and module_path.name != "__init__.py":
                package_parts = package_parts[:-1]
            anchor = package_parts[: len(package_parts) - node.level + 1]
            base_parts = [part for part in base.split(".") if part]
            resolved_base = ".".join(part for part in [*anchor, *base_parts] if part)
        else:
            resolved_base = base

        if not resolved_base:
            return ()

        resolved = [resolved_base]
        for alias in node.names:
            if alias.name == "*":
                continue
            candidate = f"{resolved_base}.{alias.name}"
            if self._module_path(candidate) is not None:
                resolved.append(candidate)
        return tuple(resolved)

    def _expand_imported_modules(self, module: str) -> tuple[str, ...]:
        expanded: list[str] = []
        parts = module.split(".")
        for idx in range(1, len(parts) + 1):
            candidate = ".".join(parts[:idx])
            if self._module_path(candidate) is not None:
                expanded.append(candidate)
        return tuple(expanded)

    def _extract_manager_calls(self, node: ast.AST) -> list[str]:
        calls: list[str] = []
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in {"get", "filter", "create", "all", "select_related", "prefetch_related"}:
                continue
            owner = func.value
            if isinstance(owner, ast.Attribute) and owner.attr == "objects":
                calls.append(f"objects.{func.attr}")
        return calls

    def _startup_closure(self, scans: dict[str, ModuleScan]) -> set[str]:
        pending = [self.startup_module]
        seen: set[str] = set()

        while pending:
            module = pending.pop()
            if module in seen:
                continue
            seen.add(module)
            scan = scans.get(module)
            if scan is None:
                continue
            for imported in scan.afritech_imports:
                if imported not in seen:
                    pending.append(imported)
        return seen

    def _detect_violations(
        self,
        scans: dict[str, ModuleScan],
        startup_closure: set[str],
    ) -> list[BoundaryViolation]:
        violations: list[BoundaryViolation] = []

        for module in sorted(startup_closure):
            scan = scans.get(module)
            if scan is None or self._is_declared_django_surface(module, scan.path):
                continue

            if scan.direct_framework_imports:
                violations.append(
                    BoundaryViolation(
                        code="RBV-001",
                        severity="high",
                        module=module,
                        path=str(scan.path),
                        detail="startup path directly imports Django/DRF modules: "
                        + ", ".join(scan.direct_framework_imports),
                        import_chain=self._find_chain(scans, self.startup_module, module),
                    )
                )

            if scan.top_level_manager_calls:
                violations.append(
                    BoundaryViolation(
                        code="RBV-002",
                        severity="high",
                        module=module,
                        path=str(scan.path),
                        detail="startup path executes model-manager style calls at import time: "
                        + ", ".join(scan.top_level_manager_calls),
                        import_chain=self._find_chain(scans, self.startup_module, module),
                    )
                )

        for module, scan in sorted(scans.items()):
            if self._is_declared_django_surface(module, scan.path):
                continue
            if not any(module.startswith(prefix) for prefix in self.scan_prefixes):
                continue
            if scan.direct_framework_imports:
                violations.append(
                    BoundaryViolation(
                        code="RBV-003",
                        severity="medium",
                        module=module,
                        path=str(scan.path),
                        detail="runtime-safe namespace directly imports Django/DRF modules: "
                        + ", ".join(scan.direct_framework_imports),
                    )
                )
            if scan.top_level_manager_calls:
                violations.append(
                    BoundaryViolation(
                        code="RBV-004",
                        severity="medium",
                        module=module,
                        path=str(scan.path),
                        detail="runtime-safe namespace performs manager-style calls at import time: "
                        + ", ".join(scan.top_level_manager_calls),
                    )
                )

        unique: dict[tuple[str, str, str], BoundaryViolation] = {}
        for violation in violations:
            unique[(violation.code, violation.module, violation.detail)] = violation
        return [unique[key] for key in sorted(unique)]

    def _find_chain(
        self,
        scans: dict[str, ModuleScan],
        start: str,
        target: str,
    ) -> tuple[str, ...]:
        pending: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
        visited: set[str] = set()
        while pending:
            module, chain = pending.pop(0)
            if module == target:
                return chain
            if module in visited:
                continue
            visited.add(module)
            scan = scans.get(module)
            if scan is None:
                continue
            for imported in scan.afritech_imports:
                if imported not in visited:
                    pending.append((imported, (*chain, imported)))
        return (start, target)

    def _is_declared_django_surface(self, module: str, path: Path) -> bool:
        if module.startswith("afriride_system."):
            return True
        if module == "afritech.api.urls":
            return True
        name = path.name
        if name.endswith("_views.py") or name.endswith("_models.py"):
            return True
        return False


def build_report(
    *,
    root: Path | None = None,
    startup_module: str = DEFAULT_STARTUP_MODULE,
) -> BoundaryReport:
    return RuntimeBoundaryValidator(root=root, startup_module=startup_module).build_report()


def validate() -> bool:
    return RuntimeBoundaryValidator().validate()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--startup-module", default=DEFAULT_STARTUP_MODULE)
    parser.add_argument("--markdown-out")
    parser.add_argument("--fail-on-violations", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(startup_module=args.startup_module)
    if args.markdown_out:
        Path(args.markdown_out).write_text(report.to_markdown(), encoding="utf-8")

    print(report.to_markdown(), end="")

    if args.fail_on_violations and report.violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
