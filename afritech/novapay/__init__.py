"""Governed NovaPay platform domains."""

from .repository import (
    NovaPayRecord,
    NovaPayRepository,
    PostgresNovaPayRepository,
    build_repository_from_environment,
    validate_database_runtime,
)
from .portal_suite import NovaPortalSuite
from .migration import migrate_legacy_monetary_state
from .service import NovaPayEcosystem
from .surfaces import build_app_surfaces, build_trust_surfaces
from .ecosystem_contract import novapay_ecosystem_contract

__all__ = [
    "AuthorityKind",
    "CANONICAL_NOVAPAY_PACKAGE",
    "CAPABILITY_AUTHORITIES",
    "CapabilityAuthority",
    "CapabilityStatus",
    "Currency",
    "Customer",
    "CustomerAddress",
    "CustomerContact",
    "CustomerId",
    "CustomerMetadata",
    "CustomerName",
    "CustomerPreferences",
    "CustomerStatus",
    "CustomerTier",
    "CustomerType",
    "DEFAULT_MINOR_UNITS",
    "JournalEntry",
    "JournalEntryId",
    "JournalEntryMetadata",
    "JournalEntryStatus",
    "JournalEntryType",
    "LEGACY_PAYMENT_ENGINE",
    "LedgerAccount",
    "LedgerAccountId",
    "LedgerAccountMetadata",
    "LedgerAccountStatus",
    "LedgerAccountType",
    "Money",
    "NOVAPAY_PRODUCT_OWNER",
    "NormalBalanceSide",
    "NovaPayEcosystem",
    "NovaPayRecord",
    "NovaPayRepository",
    "NovaPortalSuite",
    "PROHIBITED_DUPLICATION",
    "PostgresNovaPayRepository",
    "PostingLine",
    "PostingLineId",
    "PostingLineMetadata",
    "PostingSide",
    "Transaction",
    "TransactionDirection",
    "TransactionId",
    "TransactionMetadata",
    "TransactionStatus",
    "TransactionType",
    "Wallet",
    "WalletId",
    "WalletMetadata",
    "WalletStatus",
    "WalletType",
    "authority_for",
    "build_app_surfaces",
    "build_repository_from_environment",
    "build_trust_surfaces",
    "financial_source_of_truth",
    "freeze_money_payload",
    "migrate_legacy_monetary_state",
    "novapay_ecosystem_contract",
    "validate_authority_map",
    "validate_database_runtime",
]
# NovaPay WP-001B authority exports
from .authority import (
    AuthorityKind,
    CapabilityAuthority,
    CapabilityStatus,
    CANONICAL_NOVAPAY_PACKAGE,
    CAPABILITY_AUTHORITIES,
    LEGACY_PAYMENT_ENGINE,
    NOVAPAY_PRODUCT_OWNER,
    PROHIBITED_DUPLICATION,
    authority_for,
    financial_source_of_truth,
    validate_authority_map,
)

# NovaPay WP-001C1 domain exports
from .domain import (
    Currency,
    DEFAULT_MINOR_UNITS,
    Money,
    freeze_money_payload,
)

# NovaPay WP-001C2 wallet exports
from .domain import (
    Wallet,
    WalletId,
    WalletMetadata,
    WalletStatus,
    WalletType,
)

# NovaPay WP-001C3 ledger account exports
from .domain import (
    LedgerAccount,
    LedgerAccountId,
    LedgerAccountMetadata,
    LedgerAccountStatus,
    LedgerAccountType,
    NormalBalanceSide,
)


# NovaPay WP-001C5 transaction exports
from .domain import (
    Transaction,
    TransactionDirection,
    TransactionId,
    TransactionMetadata,
    TransactionStatus,
    TransactionType,
)


# NovaPay WP-001C4 journal-entry exports
from .domain import (
    JournalEntry,
    JournalEntryId,
    JournalEntryMetadata,
    JournalEntryStatus,
    JournalEntryType,
    PostingLine,
    PostingLineId,
    PostingLineMetadata,
    PostingSide,
)
from .domain.customer import (
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerId,
    CustomerMetadata,
    CustomerName,
    CustomerPreferences,
    CustomerStatus,
    CustomerTier,
    CustomerType,
)
