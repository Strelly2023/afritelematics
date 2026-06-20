from __future__ import annotations

from ast import walk, parse, Import, ImportFrom, FunctionDef, ClassDef
from dataclasses import dataclass
from typing import Any

from afritech.afroprog_workspace.models import ProjectWorkspace, ProjectFile


@dataclass(frozen=True)
class GraphSummary:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    signals: dict[str, Any]
    technical_debt: dict[str, Any]


class RepositoryGraphIntelligence:
    def analyze(self, project: ProjectWorkspace) -> GraphSummary:
        nodes: list[dict[str, Any]] = [
            {"id": project.project_id, "type": "project", "label": project.name}
        ]
        edges: list[dict[str, Any]] = []
        python_import_count = 0
        function_count = 0
        class_count = 0
        todo_count = 0
        path_depths: list[int] = []

        for file in project.files:
            file_id = f"file:{file.path}"
            nodes.append(
                {
                    "id": file_id,
                    "type": "file",
                    "label": file.path,
                    "language": file.language,
                }
            )
            edges.append({"from": project.project_id, "to": file_id, "type": "contains"})
            path_depths.append(file.path.count("/") + 1)
            content = file.content or ""
            todo_count += content.lower().count("todo") + content.lower().count("fixme")
            if file.language.lower() == "python":
                try:
                    tree = parse(content)
                except SyntaxError:
                    tree = None
                if tree is not None:
                    for node in walk(tree):
                        if isinstance(node, (Import, ImportFrom)):
                            python_import_count += 1
                            module = getattr(node, "module", None) or ",".join(alias.name for alias in getattr(node, "names", []))
                            edges.append({"from": file_id, "to": f"module:{module}", "type": "imports"})
                        elif isinstance(node, FunctionDef):
                            function_count += 1
                            edges.append({"from": file_id, "to": f"fn:{node.name}", "type": "defines"})
                        elif isinstance(node, ClassDef):
                            class_count += 1
                            edges.append({"from": file_id, "to": f"class:{node.name}", "type": "defines"})

        signals = {
            "file_count": len(project.files),
            "language_count": len({item.language for item in project.files}),
            "python_import_count": python_import_count,
            "function_count": function_count,
            "class_count": class_count,
            "average_path_depth": round(sum(path_depths) / len(path_depths), 2) if path_depths else 0.0,
        }
        debt_score = min(
            100,
            10
            + len(project.files) * 7
            + python_import_count * 3
            + todo_count * 15
            + max(0, function_count - 4) * 2,
        )
        technical_debt = {
            "score": debt_score,
            "level": _debt_level(debt_score),
            "findings": _debt_findings(todo_count, python_import_count, project.files),
        }
        return GraphSummary(nodes=nodes, edges=edges, signals=signals, technical_debt=technical_debt)

    def summarize(self, project: ProjectWorkspace) -> dict[str, Any]:
        summary = self.analyze(project)
        return {
            "project_id": project.project_id,
            "project_name": project.name,
            "nodes": summary.nodes,
            "edges": summary.edges,
            "signals": summary.signals,
            "technical_debt": summary.technical_debt,
        }


def _debt_level(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def _debt_findings(todo_count: int, python_import_count: int, files: tuple[ProjectFile, ...]) -> list[str]:
    findings: list[str] = []
    if todo_count:
        findings.append(f"{todo_count} TODO/FIXME markers detected")
    if python_import_count == 0 and any(file.language.lower() == "python" for file in files):
        findings.append("python project without explicit imports may be incomplete")
    if len(files) > 6:
        findings.append("large workspace benefits from modularization")
    if not findings:
        findings.append("workspace appears structurally light")
    return findings


_DEFAULT_GRAPH = RepositoryGraphIntelligence()


def get_repository_graph_intelligence() -> RepositoryGraphIntelligence:
    return _DEFAULT_GRAPH
