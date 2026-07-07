export type Money = Readonly<{ amount: number; currency: string }>;
export type TransactionState = "draft" | "pending" | "complete" | "failed";
export type Wallet = Readonly<{
  walletId: string;
  ownerId: string;
  balance: Money;
  status: "active" | "restricted" | "closed";
}>;
export type LedgerEntry = Readonly<{
  ledgerEntryId: string;
  walletId: string;
  debit?: Money;
  credit?: Money;
  referenceId: string;
  postedAt: string;
}>;
export type Transaction = Readonly<{
  id: string;
  kind: string;
  amount: Money;
  state: TransactionState;
  createdAt: string;
}>;
export type DigitalReceipt = Readonly<{
  receiptId: string;
  transactionId: string;
  amount: Money;
  proofOfPayment: string;
  issuedAt: string;
}>;
export type AuditEvent = Readonly<{
  id: string;
  action: string;
  actorId: string;
  occurredAt: string;
}>;

export const createTransaction = (kind: string, amount: Money): Transaction => ({
  id: `NP-${Date.now()}`,
  kind,
  amount,
  state: "pending",
  createdAt: new Date().toISOString(),
});
