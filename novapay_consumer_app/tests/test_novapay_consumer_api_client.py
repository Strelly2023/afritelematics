from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_consumer_api_client_targets_real_novapay_surfaces() -> None:
    source = read("src/novapayApi.ts")

    for item in (
        "https://api.afritechnology.com",
        "loadConsumerSurface",
        "/v1/novapay/apps",
        "/v1/novapay/portals",
        "Authorization",
        "unauthorized",
    ):
        assert item in source
