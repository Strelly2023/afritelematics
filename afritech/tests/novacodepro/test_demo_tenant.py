from __future__ import annotations

from pathlib import Path

import pytest

from afritech.novacodepro.demo.guard import DemoEnvironmentGuard
from afritech.novacodepro.demo.personas import DEMO_PERSONAS, build_demo_persona_token
from afritech.novacodepro.demo.seed import EnterpriseDemoSeed, seed_enterprise_demo
from afritech.novacodepro.platform import NovaCodeProPlatform, NovaCodeProRepository


def test_demo_manifest_and_seed(tmp_path: Path) -> None:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "demo.sqlite3"))
    manifest_path = Path("afritech/novacodepro/demo/manifests/enterprise_demo_manifest.yaml")
    summary = seed_enterprise_demo(platform, manifest_path=manifest_path, reset=True)

    assert summary["status"] == "SUCCESS"
    assert summary["users"] == 29
    assert summary["projects"] == 4
    assert summary["workflows"] == 8
    assert summary["command_center_snapshots"] == 1


def test_demo_guard_blocks_production_side_effects() -> None:
    guard = DemoEnvironmentGuard()
    blocked = guard.enforce("production.deploy")
    allowed = guard.enforce("command_center.read")
    assert blocked["status"] == "blocked"
    assert allowed["status"] == "allowed"


def test_demo_persona_token_carries_demo_claims() -> None:
    persona = DEMO_PERSONAS[0]
    token = build_demo_persona_token(persona)
    assert token["claims"]["demo"] is True
    assert token["claims"]["realm"] == "novatech-enterprise-demo"
    assert token["claims"]["tenant_id"] == persona.tenant_id


def test_demo_persona_token_rejects_wrong_realm() -> None:
    persona = DEMO_PERSONAS[0]
    with pytest.raises(RuntimeError, match="persona_switcher_disabled"):
        build_demo_persona_token(persona, realm="wrong-realm")

