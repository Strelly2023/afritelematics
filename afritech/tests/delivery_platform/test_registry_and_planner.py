from __future__ import annotations

from pathlib import Path

from afritech.delivery_platform import build_default_delivery_platform_registry
from afritech.delivery_platform.build_orchestrator import BuildOrchestrator
from afritech.delivery_platform.contracts import BuildDefinition
from afritech.delivery_platform.deployment_planner import DeploymentPlanner
from afritech.delivery_platform.optimisation import OptimisationEngine


def test_delivery_registry_has_reference_products() -> None:
    registry = build_default_delivery_platform_registry()
    assert registry.get_manifest("novacodepro") is not None
    assert registry.get_manifest("novafleet") is not None
    snapshot = registry.snapshot()
    assert snapshot["product_count"] >= 2


def test_build_plan_and_optimisation_are_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text("<html>NovaCodePro</html>", encoding="utf-8")

    registry = build_default_delivery_platform_registry()
    builder = BuildOrchestrator(registry)
    artifact = builder.build(
        BuildDefinition(
            build_id="build-001",
            product_code="novacodepro",
            component_name="portal",
            build_profile="vite",
            source_path=str(source),
            output_type="static",
            dependency_lockfile="package-lock.json",
            build_commands=("npm run build",),
            test_commands=("npm test",),
            security_commands=("npm audit",),
            artifact_name="novacodepro-portal",
            artifact_version="2026.07.0",
            optimisation_profile="frontend",
        )
    )

    manifest = registry.get_manifest("novacodepro")
    plan = DeploymentPlanner().plan(manifest, artifact, environment="staging", region="AU")
    assert plan.product_code == "novacodepro"
    assert plan.actions
    assert plan.plan_checksum.startswith("sha256:")

    optimisation = OptimisationEngine().analyse(artifact, manifest.optimisation_policies[0])
    assert optimisation.product_code == "novacodepro"
    assert optimisation.analysis["artifact_id"] == artifact.artifact_id

