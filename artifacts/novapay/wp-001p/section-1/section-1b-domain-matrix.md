# NovaPay Phase 1 Canonical Domain Matrix

- Domain modules: `16`
- Domain package exports: `168`
- Top-level exports: `190`

## `balance_snapshot`

- Module exports: `11`
- Canonical classes: `11`
- Enums: `3`
- Identifiers: `BalanceSnapshotHistoryId`, `BalanceSnapshotId`
- Status/lifecycle types: `BalanceSnapshotStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `BalanceComponent` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceComponentType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `BalanceReconciliation` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshot` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshotHistory` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshotHistoryId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshotId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshotMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshotStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `BalanceSnapshotType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `LedgerPosition` | YES | YES | NO | PRESENT | PRESENT | PRESENT |

## `currency`

- Module exports: `14`
- Canonical classes: `11`
- Enums: `3`
- Identifiers: `CurrencyDefinitionId`, `CurrencyRegistryId`
- Status/lifecycle types: `CurrencyStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `CurrencyCountryCodes` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyDefinition` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyDefinitionId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyName` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyRegistry` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyRegistryId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyRoundingMode` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `CurrencyStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `CurrencySymbol` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CurrencyType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `customer`

- Module exports: `10`
- Canonical classes: `10`
- Enums: `3`
- Identifiers: `CustomerId`
- Status/lifecycle types: `CustomerStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Customer` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerAddress` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerContact` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerName` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerPreferences` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `CustomerStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `CustomerTier` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `CustomerType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `exchange_rate_provider`

- Module exports: `16`
- Canonical classes: `16`
- Enums: `5`
- Identifiers: `ExchangeRateProviderId`, `ExchangeRateProviderRegistryId`, `RateSourceId`
- Status/lifecycle types: `ExchangeRateProviderStatus`, `RateSourceStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `ExchangeRateProvider` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ExchangeRateProviderId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ExchangeRateProviderRegistry` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ExchangeRateProviderRegistryId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ExchangeRateProviderStatus` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ExchangeRateProviderType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ProviderCapabilities` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ProviderEndpoint` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ProviderMetadata` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ProviderName` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ProviderTrustLevel` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `RateSource` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `RateSourceId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `RateSourceMetadata` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `RateSourceStatus` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `RateSourceType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |

## `financial_account`

- Module exports: `9`
- Canonical classes: `9`
- Enums: `3`
- Identifiers: `FinancialAccountId`
- Status/lifecycle types: `FinancialAccountStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `FinancialAccount` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FinancialAccountId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FinancialAccountMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FinancialAccountName` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FinancialAccountPurpose` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `FinancialAccountRestrictions` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FinancialAccountStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `FinancialAccountTerms` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FinancialAccountType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `fx`

- Module exports: `12`
- Canonical classes: `12`
- Enums: `3`
- Identifiers: `ExchangeRateId`, `FXQuoteId`
- Status/lifecycle types: `ExchangeRateStatus`, `FXQuoteStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `CurrencyPair` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ExchangeRate` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ExchangeRateId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ExchangeRateSource` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ExchangeRateStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ExchangeRateValue` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FXMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FXQuote` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FXQuoteId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `FXQuoteStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `FXValidityWindow` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RateSpread` | YES | YES | NO | PRESENT | PRESENT | PRESENT |

## `journal_entry`

- Module exports: `9`
- Canonical classes: `9`
- Enums: `3`
- Identifiers: `JournalEntryId`, `PostingLineId`
- Status/lifecycle types: `JournalEntryStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `JournalEntry` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `JournalEntryId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `JournalEntryMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `JournalEntryStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `JournalEntryType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `PostingLine` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `PostingLineId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `PostingLineMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `PostingSide` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `ledger_account`

- Module exports: `6`
- Canonical classes: `6`
- Enums: `3`
- Identifiers: `LedgerAccountId`
- Status/lifecycle types: `LedgerAccountStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `LedgerAccount` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `LedgerAccountId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `LedgerAccountMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `LedgerAccountStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `LedgerAccountType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `NormalBalanceSide` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `money`

- Module exports: `4`
- Canonical classes: `2`
- Enums: `0`
- Identifiers: None identified
- Status/lifecycle types: None identified
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Currency` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `Money` | YES | YES | NO | PRESENT | PRESENT | PRESENT |

## `receipt`

- Module exports: `25`
- Canonical classes: `25`
- Enums: `10`
- Identifiers: `ReceiptAdjustmentId`, `ReceiptId`, `ReceiptLineItemId`, `ReceiptPartyId`, `ReceiptTaxId`
- Status/lifecycle types: `ReceiptStatus`, `ReceiptVerificationStatus`
- Reference types: `ReceiptReference`, `ReceiptReferenceType`

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Receipt` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptAdjustment` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptAdjustmentId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptAdjustmentType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptFormat` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptIntegrityEvidence` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReceiptIntegrityEvidenceType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptLineItem` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptLineItemId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptLineItemType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptMetadata` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptMonetarySummary` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptParty` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptPartyId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptPartyType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptReference` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptReferenceType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptStatus` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptTax` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptTaxId` | YES | YES | NO | PRESENT | ABSENT | ABSENT |
| `ReceiptTaxType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptType` | NO | NO | YES | PRESENT | ABSENT | ABSENT |
| `ReceiptVerificationResult` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReceiptVerificationStatus` | NO | NO | YES | PRESENT | ABSENT | ABSENT |

## `remittance`

- Module exports: `20`
- Canonical classes: `20`
- Enums: `6`
- Identifiers: `RemittanceId`, `RemittanceInstructionId`
- Status/lifecycle types: `RemittanceStatus`
- Reference types: `RemittanceFundingReference`, `RemittanceRecipientReference`, `RemittanceReference`

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Remittance` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceAmountBreakdown` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceCharge` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceCorridor` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceDirection` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `RemittanceFee` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceFeeType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `RemittanceFundingReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceInstruction` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceInstructionId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceInstructionMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittancePricingMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittancePriority` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `RemittancePurpose` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `RemittanceRecipientReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `RemittanceStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `RemittanceType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `settlement_batch`

- Module exports: `20`
- Canonical classes: `20`
- Enums: `5`
- Identifiers: `SettlementBatchId`, `SettlementEntryId`, `SettlementInstructionId`, `SettlementParticipantId`
- Status/lifecycle types: `SettlementBatchStatus`, `SettlementEntryStatus`
- Reference types: `SettlementReference`, `SettlementReferenceType`

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `SettlementBatch` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementBatchId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementBatchStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `SettlementBatchType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `SettlementEntry` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementEntryId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementEntryStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `SettlementFailure` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementInstruction` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementInstructionId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementInstructionMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementParticipant` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementParticipantId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementParticipantType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `SettlementReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementReferenceType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `SettlementResult` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementSummary` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementWindow` | YES | YES | NO | PRESENT | PRESENT | PRESENT |

## `settlement_reconciliation`

- Module exports: `19`
- Canonical classes: `19`
- Enums: `6`
- Identifiers: `ReconciliationDifferenceId`, `ReconciliationEvidenceId`, `ReconciliationItemId`, `ReconciliationObservationId`, `SettlementReconciliationId`
- Status/lifecycle types: `ReconciliationItemStatus`, `ReconciliationStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `ReconciliationDifference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationDifferenceId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationDifferenceType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ReconciliationEvidence` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationEvidenceId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationEvidenceType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ReconciliationItem` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationItemId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationItemStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ReconciliationMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationObservation` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationObservationId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationObservationSource` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ReconciliationResult` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `ReconciliationSummary` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `ReconciliationType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `SettlementReconciliation` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `SettlementReconciliationId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |

## `transaction`

- Module exports: `6`
- Canonical classes: `6`
- Enums: `3`
- Identifiers: `TransactionId`
- Status/lifecycle types: `TransactionStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Transaction` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransactionDirection` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransactionId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransactionMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransactionStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransactionType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `transfer`

- Module exports: `21`
- Canonical classes: `21`
- Enums: `6`
- Identifiers: `TransferId`, `TransferInstructionId`
- Status/lifecycle types: `TransferStatus`
- Reference types: `TransferAccountReference`, `TransferBeneficiaryReference`, `TransferFundingReference`, `TransferPartyReference`, `TransferReference`

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Transfer` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferAccountReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferAmountBreakdown` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferBeneficiaryReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferCharge` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferDirection` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransferFee` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferFeeType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransferFundingReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferInstruction` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferInstructionId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferInstructionMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferPartyReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferPricingMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferPriority` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransferPurpose` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransferReference` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `TransferStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `TransferType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

## `wallet`

- Module exports: `5`
- Canonical classes: `5`
- Enums: `2`
- Identifiers: `WalletId`
- Status/lifecycle types: `WalletStatus`
- Reference types: None identified

| Symbol | Dataclass | Frozen | Enum | Module | Domain | Top-level |
|---|---:|---:|---:|---:|---:|---:|
| `Wallet` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `WalletId` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `WalletMetadata` | YES | YES | NO | PRESENT | PRESENT | PRESENT |
| `WalletStatus` | NO | NO | YES | PRESENT | PRESENT | PRESENT |
| `WalletType` | NO | NO | YES | PRESENT | PRESENT | PRESENT |

