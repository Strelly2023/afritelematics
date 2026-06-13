"""Double-entry ledger for AfriPay."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from afritech.afripay.exceptions import DuplicateReference, GuardViolation
from afritech.afripay.guards import guard_journal_balances
from afritech.afripay.models import EntryLine, JournalEntry, LedgerAccount, new_id
from afritech.afripay.money import Money


class DoubleEntryLedger:
    def __init__(self) -> None:
        self._accounts: dict[str, LedgerAccount] = {}
        self._entries: list[JournalEntry] = []
        self._references: set[str] = set()

    def create_account(self, name: str, account_type: str, currency: str) -> LedgerAccount:
        account = LedgerAccount(new_id("ledgeracct"), name, account_type, currency.upper())
        self._accounts[account.account_id] = account
        return account

    def post(
        self,
        *,
        reference: str,
        transaction_id: str,
        lines: tuple[EntryLine, ...],
    ) -> JournalEntry:
        if reference in self._references:
            raise DuplicateReference(f"duplicate journal reference: {reference}")
        for line in lines:
            account = self._accounts.get(line.account_id)
            if account is None:
                raise GuardViolation("journal line references unknown account")
            if account.currency != line.debit.currency or account.currency != line.credit.currency:
                raise GuardViolation("journal line currency differs from account")
        guard_journal_balances(lines)
        entry = JournalEntry(new_id("journal"), reference, transaction_id, lines)
        self._entries.append(entry)
        self._references.add(reference)
        return entry

    def balance(self, account_id: str) -> Money:
        account = self._accounts[account_id]
        value = Decimal("0.00")
        for entry in self._entries:
            for line in entry.lines:
                if line.account_id == account_id:
                    value += line.debit.amount - line.credit.amount
        return Money.of(value, account.currency)

    def entries(self) -> tuple[JournalEntry, ...]:
        return tuple(self._entries)

    def accounts(self) -> tuple[LedgerAccount, ...]:
        return tuple(self._accounts.values())

    def trial_balance(self) -> dict[str, dict[str, Decimal]]:
        totals: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"debit": Decimal("0.00"), "credit": Decimal("0.00")})
        for entry in self._entries:
            for line in entry.lines:
                currency = line.debit.currency
                totals[currency]["debit"] += line.debit.amount
                totals[currency]["credit"] += line.credit.amount
        return dict(totals)

    def verify_balanced(self) -> bool:
        return all(total["debit"] == total["credit"] for total in self.trial_balance().values())


def debit(account: LedgerAccount, amount: Money) -> EntryLine:
    return EntryLine(account.account_id, amount, Money.of("0.00", amount.currency))


def credit(account: LedgerAccount, amount: Money) -> EntryLine:
    return EntryLine(account.account_id, Money.of("0.00", amount.currency), amount)
