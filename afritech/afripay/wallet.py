"""Wallet service with multi-currency and locked balance support."""

from __future__ import annotations

from afritech.afripay.exceptions import GuardViolation, InsufficientFunds
from afritech.afripay.models import Wallet, WalletType, new_id, utc_now
from afritech.afripay.money import Money


class WalletService:
    def create_wallet(self, owner_id: str, home_country: str, wallet_type: WalletType = WalletType.PERSONAL) -> Wallet:
        if not owner_id:
            raise GuardViolation("owner_id is required")
        return Wallet(new_id("wallet"), owner_id, wallet_type, home_country)

    def credit(self, wallet: Wallet, amount: Money) -> None:
        amount.require_positive()
        account = wallet.account(amount.currency)
        account.balance = account.balance + amount
        account.updated_at = utc_now()

    def debit(self, wallet: Wallet, amount: Money) -> None:
        amount.require_positive()
        account = wallet.account(amount.currency)
        if account.available.amount < amount.amount:
            raise InsufficientFunds("insufficient wallet funds")
        account.balance = account.balance - amount
        account.updated_at = utc_now()

    def lock(self, wallet: Wallet, amount: Money) -> None:
        amount.require_positive()
        account = wallet.account(amount.currency)
        if account.available.amount < amount.amount:
            raise InsufficientFunds("insufficient funds to lock")
        account.locked = account.locked + amount
        account.updated_at = utc_now()

    def release_lock(self, wallet: Wallet, amount: Money) -> None:
        amount.require_positive()
        account = wallet.account(amount.currency)
        if account.locked.amount < amount.amount:
            raise GuardViolation("locked balance cannot go negative")
        account.locked = account.locked - amount
        account.updated_at = utc_now()

    def transfer(self, source: Wallet, destination: Wallet, amount: Money) -> None:
        self.debit(source, amount)
        self.credit(destination, amount)

    def geo_balance(self, wallet: Wallet, country: str, preferred_currency: str | None = None) -> Money:
        currency = preferred_currency or _country_currency(country) or _country_currency(wallet.home_country)
        return wallet.account(currency).available


def _country_currency(country: str) -> str:
    return {
        "AU": "AUD",
        "AUS": "AUD",
        "AUSTRALIA": "AUD",
        "BI": "BIF",
        "BDI": "BIF",
        "BURUNDI": "BIF",
        "CD": "CDF",
        "COD": "CDF",
        "DRC": "CDF",
        "KENYA": "KES",
        "KE": "KES",
    }.get(country.upper(), "USD")
