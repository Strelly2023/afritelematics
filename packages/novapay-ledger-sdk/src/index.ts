export type LedgerEntry = Readonly<{
  id: string;
  transactionId: string;
  accountId: string;
  debit: number;
  credit: number;
}>;
export const isBalanced = (entries: readonly LedgerEntry[]) =>
  entries.reduce((sum, entry) => sum + entry.debit - entry.credit, 0) === 0;
