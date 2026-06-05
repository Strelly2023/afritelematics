from __future__ import annotations

from dataclasses import dataclass

import pytest

from afritech.audit.chain_validator import ChainValidationError
from afritech.guards.audit_chain_guard import AuditChainGuard


@dataclass
class AuditEntryStub:
    previous_hash: str
    entry_hash: str
    epoch: int
    status: str = "VALID"


def test_audit_chain_guard_accepts_forward_link():
    previous = AuditEntryStub(previous_hash="", entry_hash="prev", epoch=1)
    entry = AuditEntryStub(previous_hash="prev", entry_hash="next", epoch=2)

    assert AuditChainGuard.validate_pre_insert(entry, previous) is True


def test_audit_chain_guard_rejects_broken_forward_link():
    previous = AuditEntryStub(previous_hash="", entry_hash="prev", epoch=1)
    entry = AuditEntryStub(previous_hash="wrong", entry_hash="next", epoch=2)

    with pytest.raises(ChainValidationError, match="FORWARD_LINK_BROKEN"):
        AuditChainGuard.validate_pre_insert(entry, previous)
