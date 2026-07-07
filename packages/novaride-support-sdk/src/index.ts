import type { DisputeCase, SupportTicket } from "../../novaride-core/src";
export const openDispute = (rideId: string, reason: string): DisputeCase => ({ id: `DIS-${Date.now()}`, rideId, reason, status: "open" });
export const openSupportTicket = (subject: string, rideId?: string): SupportTicket => ({ id: `SUP-${Date.now()}`, rideId, subject, status: "open" });
