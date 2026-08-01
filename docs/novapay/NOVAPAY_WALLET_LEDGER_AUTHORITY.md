# NovaPay Wallet and Ledger Authority

## Status

This document defines the canonical ownership and migration boundary for
NovaPay wallet, ledger, payment, provider, treasury, and reconciliation
capabilities.

## Product authority

NovaPay owns:

- payment product contracts;
- wallet contracts;
- ledger policy;
- transaction lifecycle semantics;
- settlement and reconciliation contracts;
- provider integration boundaries;
- receipts and financial verification contracts;
- downstream integration contracts.

AfriPay remains a legacy-compatible implementation surface during migration.
Its existing wallet, ledger, orchestration, treasury, provider, reconciliation,
and proof components must not be removed or silently changed while dependent
tests and services continue to use them.

## Financial source of truth

The double-entry ledger is the sole authoritative financial source of truth.

Every authoritative monetary mutation must:

1. pass authentication and authorization;
2. satisfy tenant and jurisdiction policy;
3. use an idempotency boundary;
4. produce balanced debit and credit entries;
5. persist atomically;
6. emit auditable evidence;
7. become replayable and reconcilable.

## Wallet balances

Wallet balances are ledger-derived projections.

A wallet service may coordinate commands such as credit, debit, lock, release,
and transfer, but a wallet balance must not become an independent source of
financial truth.

Clients must never:

- invent balances;
- mutate balances locally;
- display queued offline activity as completed;
- treat a provider callback as final ledger authority.

## Provider boundary

Providers execute external payment instructions and return evidence.

Provider responses and callbacks:

- must be authenticated where supported;
- must be idempotently persisted;
- must be reconciled;
- must not directly redefine ledger balances;
- must not bypass valid lifecycle transitions.

## NovaRide boundary

NovaRide consumes NovaPay payment contracts.

NovaRide may retain payment references, status projections, receipts, and
mobility-specific associations, but it must not maintain an independent
authoritative payment ledger.

## Migration rule

Migration from `afritech.afripay` to canonical NovaPay modules must proceed
through compatibility-preserving slices:

1. declare authority;
2. introduce stable NovaPay interfaces;
3. place adapters over existing implementations;
4. run existing AfriPay and NovaPay compatibility gates;
5. migrate callers incrementally;
6. remove legacy paths only after verified zero usage and formal approval.

## Prohibited duplication

The following are prohibited:

- independent authoritative wallet balances outside the NovaPay ledger;
- provider callbacks treated as ledger truth;
- client-side balance mutation;
- NovaRide-owned authoritative payment ledgers;
- separate unbalanced posting engines;
- silent migrations that change existing financial behaviour.
