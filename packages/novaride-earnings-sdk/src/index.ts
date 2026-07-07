import type { DriverEarnings, Payout } from "../../novaride-core/src";
export const calculateEarnings = (driverId: string, gross: number, feeRate = 0.18): DriverEarnings => ({ driverId, currency: "AUD", gross, fees: gross * feeRate, net: gross * (1 - feeRate) });
export const requestPayout = (driverId: string, amount: number): Payout => ({ id: `PAY-${Date.now()}`, driverId, amount, status: "requested" });
