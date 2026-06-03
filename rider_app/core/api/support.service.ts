import { apiRequest } from "./client";

export type SupportTicketPayload = {
  rideId: string;
  replayId: string;
  message: string;
};

export type SupportTicket = {
  ticketId: string;
  status: string;
};

export async function createSupportTicket(
  payload: SupportTicketPayload,
): Promise<SupportTicket> {
  const result = await apiRequest<{ ticket_id: string; status: string }>(
    "/support/ticket",
    {
      method: "POST",
      body: {
        ride_id: payload.rideId,
        replay_id: payload.replayId,
        message: payload.message,
      },
    },
  );

  return {
    ticketId: result.ticket_id,
    status: result.status,
  };
}
