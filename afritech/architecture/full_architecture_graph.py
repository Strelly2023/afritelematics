"""Generate the full AfriTech architecture graph from repo facts."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from afritech.ci.runtime_boundary_validator import build_report, coerce_boundary_report


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/architecture/AFRITECH_FULL_ARCHITECTURE_GRAPH.md"
APP = ROOT / "afritech/api/app.py"

AFRITECH_AREAS = (
    ("api", ROOT / "afritech/api"),
    ("edge", ROOT / "afritech/edge"),
    ("execution", ROOT / "afritech/execution"),
    ("security", ROOT / "afritech/security"),
    ("monitoring", ROOT / "afritech/monitoring"),
    ("proof", ROOT / "afritech/proof"),
    ("replay", ROOT / "afritech/replay"),
    ("governance", ROOT / "afritech/governance"),
    ("semantic_engine", ROOT / "afritech/semantic_engine"),
    ("runtime", ROOT / "afritech/runtime"),
)

EXTERNAL_SURFACES = (
    ("afriride_backend", ROOT / "afriride_system/backend", ("py",)),
    ("afriride_django", ROOT / "afriride_system/django_app", ("py",)),
    ("dashboard_ui", ROOT / "dashboard/src", ("ts", "tsx", "js", "jsx")),
    ("deploy_production", ROOT / "deploy/production", ("yml", "yaml", "conf", "Dockerfile")),
)


def _file_count(path: Path, suffixes: tuple[str, ...]) -> int:
    if not path.exists():
        return 0
    total = 0
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        if "__pycache__" in candidate.parts or "node_modules" in candidate.parts:
            continue
        if candidate.name == "Dockerfile" and "Dockerfile" in suffixes:
            total += 1
            continue
        suffix = candidate.suffix.lstrip(".")
        if suffix in suffixes:
            total += 1
    return total


def _repo_summary() -> dict[str, int]:
    summary: dict[str, int] = {}
    for label, path in AFRITECH_AREAS:
        summary[label] = _file_count(path, ("py",))
    for label, path, suffixes in EXTERNAL_SURFACES:
        summary[label] = _file_count(path, suffixes)
    return summary


def _startup_imports() -> list[str]:
    tree = ast.parse(APP.read_text(encoding="utf-8"), filename=str(APP))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("afritech"):
            modules.append(node.module)
    return sorted(set(modules))


def _group_startup_modules(startup_modules: tuple[str, ...]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for module in startup_modules:
        if module == "afritech.api.app":
            groups["api"].append(module)
        elif module.startswith("afritech.api"):
            groups["api"].append(module)
        elif module.startswith("afritech.edge"):
            groups["edge"].append(module)
        elif module.startswith("afritech.execution"):
            groups["execution"].append(module)
        elif module.startswith("afritech.security"):
            groups["security"].append(module)
        elif module.startswith("afritech.monitoring"):
            groups["monitoring"].append(module)
        elif module.startswith(
            (
                "afritech.partner_registry",
                "afritech.partner_verification",
                "afritech.trust_network",
                "afritech.standards_dependency",
            )
        ):
            groups["trust_and_registry"].append(module)
        elif module.startswith(("afritech.trace", "afritech.proof", "afritech.verify", "afritech.replay")):
            groups["proof_and_replay"].append(module)
        else:
            groups["other"].append(module)
    return {label: sorted(values) for label, values in sorted(groups.items())}


def _mermaid_runtime_graph(report_startup_count: int, declared_django_count: int, startup_import_count: int) -> str:
    return f"""```mermaid
flowchart LR
    Client["Clients / Operators / Partners"] --> Edge["Caddy / HTTP Edge\\ndeploy/production"]
    Dashboard["React Dashboard\\ndashboard/src"] --> Edge
    Edge --> App["FastAPI Runtime\\nafritech/api/app.py"]

    subgraph FastAPI["Startup-Safe FastAPI Surface ({report_startup_count} modules)"]
        App --> Api["API Routers\\nauth, trace, system, public verify"]
        App --> Workspace["AfriPro Workspace API"]
        App --> Governance["Ops Governance API"]
        App --> Trust["Partner / Trust Network APIs"]
    end

    subgraph Pipeline["Deterministic Execution Pipeline"]
        App --> Adapt["Edge Adapter"]
        Adapt --> Normalize["Normalization"]
        Normalize --> Queue["Partitioned Queue"]
        Queue --> Worker["Worker Pool"]
    end

    subgraph State["Stateful Domain Surfaces ({declared_django_count} Django-bound modules declared)"]
        Worker --> Domain["AfriRide Backend\\nafriride_system/backend"]
        Domain --> Django["Django State Layer\\nafriride_system/django_app"]
    end

    subgraph Proof["Proof / Replay / Verification"]
        Worker --> Trace["Trace / Replay / Evidence / Receipt"]
        Trace --> Public["Public Verification"]
        Trace --> Registry["Partner Registry / Trust Network"]
    end

    subgraph GovernancePlane["Governance & Enforcement"]
        Contract["Boundary Contract\\nAFRITECH_FASTAPI_DJANGO_BOUNDARY_CONTRACT"] --> Validator["Runtime Boundary Validator"]
        Checklist["Safe Import Checklist"] --> Validator
        Validator --> Review["Generated Scan Report"]
    end

    App -. startup imports .-> Imports["Direct startup imports from app.py ({startup_import_count})"]
```"""


def _mermaid_inventory_graph(summary: dict[str, int]) -> str:
    return f"""```mermaid
flowchart TD
    Root["AfriTech Repository"] --> Core["afritech/"]
    Root --> Ride["afriride_system/"]
    Root --> Ui["dashboard/"]
    Root --> Deploy["deploy/production/"]

    Core --> Api["api ({summary['api']} files)"]
    Core --> Edge["edge ({summary['edge']} files)"]
    Core --> Execution["execution ({summary['execution']} files)"]
    Core --> Security["security ({summary['security']} files)"]
    Core --> Monitoring["monitoring ({summary['monitoring']} files)"]
    Core --> Proof["proof ({summary['proof']} files)"]
    Core --> Replay["replay ({summary['replay']} files)"]
    Core --> Governance["governance ({summary['governance']} files)"]
    Core --> Semantic["semantic_engine ({summary['semantic_engine']} files)"]
    Core --> Runtime["runtime ({summary['runtime']} files)"]

    Ride --> Backend["backend ({summary['afriride_backend']} files)"]
    Ride --> Django["django_app ({summary['afriride_django']} files)"]
    Ui --> Dashboard["src ({summary['dashboard_ui']} files)"]
    Deploy --> Production["production ({summary['deploy_production']} files)"]
```"""


def _startup_inventory(groups: dict[str, list[str]]) -> str:
    lines = ["## Startup Inventory", ""]
    for label, modules in groups.items():
        lines.append(f"### {label.replace('_', ' ').title()} ({len(modules)})")
        lines.append("")
        for module in modules:
            lines.append(f"- `{module}`")
        lines.append("")
    return "\n".join(lines)


def generate_architecture_graph() -> str:
    report = coerce_boundary_report(build_report())
    summary = _repo_summary()
    startup_imports = _startup_imports()
    startup_groups = _group_startup_modules(report.startup_modules)

    lines = [
        "# AfriTech Full Architecture Graph",
        "",
        "Status: GENERATED FULL ARCHITECTURE GRAPH",
        "",
        "Classification: REPO-BACKED ARCHITECTURE INVENTORY AND RUNTIME GRAPH",
        "",
        "Purpose: render a current-state architecture graph from the repository,",
        "the FastAPI startup closure, and the runtime boundary validator output.",
        "",
        "Generated: `deterministic-repo-snapshot`",
        "",
        "## Runtime Summary",
        "",
        f"- Startup module: `{report.startup_module}`",
        f"- Startup-safe closure size: `{len(report.startup_modules)}`",
        f"- Django-bound modules declared in repo: `{len(report.declared_django_modules)}`",
        f"- Runtime-boundary violations: `{len(report.violations)}`",
        f"- Direct startup imports from `afritech.api.app`: `{len(startup_imports)}`",
        "",
        "## Runtime Architecture Graph",
        "",
        _mermaid_runtime_graph(
            report_startup_count=len(report.startup_modules),
            declared_django_count=len(report.declared_django_modules),
            startup_import_count=len(startup_imports),
        ),
        "",
        "## Repository Architecture Inventory",
        "",
        _mermaid_inventory_graph(summary),
        "",
        "## Repo Area Counts",
        "",
    ]

    for label, count in summary.items():
        lines.append(f"- `{label}`: `{count}` files")

    lines.extend(
        [
            "",
            _startup_inventory(startup_groups),
            "## Direct Startup Imports",
            "",
        ]
    )
    for module in startup_imports:
        lines.append(f"- `{module}`")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The runtime graph is based on the current production-style FastAPI entrypoint.",
            "- The inventory graph is repo-wide and broader than the active startup path.",
            "- Django-bound surfaces are allowed in the repo but must remain outside FastAPI import-time coupling.",
            "- Regenerate this file after major routing, deployment, or domain-boundary changes.",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def write_architecture_graph(output: Path = OUTPUT) -> Path:
    output.write_text(generate_architecture_graph(), encoding="utf-8")
    return output
