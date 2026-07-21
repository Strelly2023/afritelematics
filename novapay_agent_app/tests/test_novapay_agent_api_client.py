from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agent_api_client_targets_real_novapay_surfaces() -> None:
    source = read("src/novapayApi.ts")

    for item in (
        "https://api.afritechnology.com",
        "loadAgentSurface",
        "/v1/novapay/agents",
        "/v1/novapay/agents/profile",
        "/v1/novapay/agents/float",
        "/v1/novapay/agents/history",
        "/v1/novapay/agents/compliance",
        "/v1/novapay/agents/receipts",
        "/v1/novapay/agents/supervisor-review",
        "Authorization",
        "unauthorized",
    ):
        assert item in source
