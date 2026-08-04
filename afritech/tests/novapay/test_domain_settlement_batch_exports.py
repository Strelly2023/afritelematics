from __future__ import annotations

import ast
from pathlib import Path

import afritech.novapay as novapay
import afritech.novapay.domain as domain
import afritech.novapay.domain.settlement_batch as settlement_batch


DOMAIN_BACKUP = Path(
    "/tmp/novapay-wp-001m/final-certification/"
    "backups/domain-init.before-section-7a2.py"
)

TOP_LEVEL_BACKUP = Path(
    "/tmp/novapay-wp-001m/final-certification/"
    "backups/novapay-init.before-section-7a2.py"
)


def literal_all(path: Path) -> list[str]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "__all__"
            for target in node.targets
        )
    )

    value = ast.literal_eval(assignment.value)

    assert isinstance(value, list)
    assert all(
        isinstance(symbol, str)
        for symbol in value
    )

    return value


def test_canonical_inventory_contract() -> None:
    assert len(settlement_batch.__all__) == 20
    assert settlement_batch.__all__ == sorted(
        settlement_batch.__all__
    )
    assert len(settlement_batch.__all__) == len(
        set(settlement_batch.__all__)
    )


def test_domain_public_count() -> None:
    assert len(domain.__all__) == 166


def test_top_level_public_count() -> None:
    assert len(novapay.__all__) == 188


def test_domain_exports_every_canonical_symbol() -> None:
    for symbol in settlement_batch.__all__:
        assert symbol in domain.__all__
        assert hasattr(domain, symbol)
        assert getattr(domain, symbol) is getattr(
            settlement_batch,
            symbol,
        )


def test_top_level_exports_every_canonical_symbol() -> None:
    for symbol in settlement_batch.__all__:
        assert symbol in novapay.__all__
        assert hasattr(novapay, symbol)
        assert getattr(novapay, symbol) is getattr(
            settlement_batch,
            symbol,
        )


def test_cross_package_identity() -> None:
    for symbol in settlement_batch.__all__:
        assert getattr(domain, symbol) is getattr(
            novapay,
            symbol,
        )


def test_public_all_contracts_are_sorted() -> None:
    assert domain.__all__ == sorted(domain.__all__)
    assert novapay.__all__ == sorted(novapay.__all__)


def test_public_all_contracts_are_unique() -> None:
    assert len(domain.__all__) == len(set(domain.__all__))
    assert len(novapay.__all__) == len(
        set(novapay.__all__)
    )


def test_preexisting_domain_exports_are_preserved() -> None:
    before = literal_all(DOMAIN_BACKUP)

    assert len(before) == 127

    for symbol in before:
        assert symbol in domain.__all__
        assert hasattr(domain, symbol)


def test_preexisting_top_level_exports_are_preserved() -> None:
    before = literal_all(TOP_LEVEL_BACKUP)

    assert len(before) == 149

    for symbol in before:
        assert symbol in novapay.__all__
        assert hasattr(novapay, symbol)


def test_settlement_batch_domain_exports_remain_preserved() -> None:
    before = set(literal_all(DOMAIN_BACKUP))
    after = set(domain.__all__)
    canonical = set(settlement_batch.__all__)

    assert before.issubset(after)
    assert canonical.issubset(after)

    for symbol in settlement_batch.__all__:
        assert hasattr(domain, symbol)
        assert getattr(domain, symbol) is getattr(
            settlement_batch,
            symbol,
        )


def test_settlement_batch_top_level_exports_remain_preserved() -> None:
    before = set(literal_all(TOP_LEVEL_BACKUP))
    after = set(novapay.__all__)
    canonical = set(settlement_batch.__all__)

    assert before.issubset(after)
    assert canonical.issubset(after)

    for symbol in settlement_batch.__all__:
        assert hasattr(novapay, symbol)
        assert getattr(novapay, symbol) is getattr(
            settlement_batch,
            symbol,
        )


def test_authority_boundary_is_preserved() -> None:
    authority_types = (
        settlement_batch.SettlementBatch,
        settlement_batch.SettlementEntry,
        settlement_batch.SettlementInstruction,
        settlement_batch.SettlementFailure,
        settlement_batch.SettlementResult,
        settlement_batch.SettlementSummary,
    )

    forbidden = (
        "authorize",
        "reserve",
        "reserve_funds",
        "debit",
        "credit",
        "post",
        "post_entry",
        "execute",
        "settle",
        "clear",
        "net",
        "submit",
        "submit_to_provider",
        "send",
        "select_provider",
        "collect",
        "collect_fee",
        "save",
        "persist",
        "repository",
        "database",
    )

    for value_type in authority_types:
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for method_name in forbidden:
            assert method_name not in names
