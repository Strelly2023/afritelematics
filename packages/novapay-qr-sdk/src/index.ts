export type QRPayment = Readonly<{ merchantId: string; amount: number; currency: string; reference: string }>;
export const encodeQRPayment = (payment: QRPayment) => `novapay://pay?${new URLSearchParams({
  merchant: payment.merchantId,
  amount: String(payment.amount),
  currency: payment.currency,
  reference: payment.reference,
}).toString()}`;
export const isNovaPayQR = (value: string) => value.startsWith("novapay://pay?");
