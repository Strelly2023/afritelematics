from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_chain_promotion_doc_covers_sepolia_and_mainnet() -> None:
    source = read("docs/operations/AFRITECH_CHAIN_PROMOTION_SEPOLIA_TO_MAINNET.md")

    for required in (
        "Sepolia",
        "Mainnet",
        "AFRITECH_CHAIN_RPC_URL_SEPOLIA",
        "AFRITECH_CHAIN_RPC_URL_MAINNET",
        "afritech-verify",
        "afritech-verify-session",
    ):
        assert required in source


def test_external_verifier_cli_package_doc_covers_distribution() -> None:
    source = read("docs/partners/AFRITECH_EXTERNAL_VERIFIER_CLI_PACKAGE.md")

    for required in (
        "afritech-verify",
        "afritech-verify-session",
        "pipx install .",
        "Mainnet promotion",
    ):
        assert required in source


def test_first_partner_verification_session_doc_covers_expected_outcome() -> None:
    source = read("docs/partners/AFRITECH_FIRST_EXTERNAL_PARTNER_VERIFICATION_SESSION.md")

    for required in (
        "PARTNER_READY",
        "PASSED",
        "promote_to_mainnet",
    ):
        assert required in source
