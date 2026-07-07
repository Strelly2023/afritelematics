export type DigitalReceipt = Readonly<{
  id: string;
  transactionId: string;
  proofOfPayment: string;
  issuedAt: string;
}>;
export const createReceipt = (transactionId: string): DigitalReceipt => ({
  id: `NPR-${transactionId}`,
  transactionId,
  proofOfPayment: `sha256:${transactionId}`,
  issuedAt: new Date().toISOString(),
});
