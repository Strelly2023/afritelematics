import type { Money } from "../../novapay-core/src";
export type Wallet = Readonly<{ id: string; ownerId: string; balance: Money }>;
export const canDebit = (wallet: Wallet, amount: number) => amount > 0 && wallet.balance.amount >= amount;
export const formatBalance = (wallet: Wallet) =>
  `${wallet.balance.currency} ${wallet.balance.amount.toFixed(2)}`;
