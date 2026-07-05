import { PartnerClient } from "../models";

const now = () => new Date().toISOString();

export async function createOAuthClient(name: string): Promise<PartnerClient> {
  return {
    id: `partner-${Math.random().toString(36).slice(2, 8)}`,
    name,
    clientId: `client-${Math.random().toString(36).slice(2, 10)}`,
    secretHint: "rotating-secret-enabled",
    webhookUrl: "https://partner.example/webhooks/novaid",
    apiUsage: 0,
    status: "verified",
  };
}

export async function rotatePartnerSecret(client: PartnerClient): Promise<PartnerClient> {
  return {
    ...client,
    secretHint: `rotated-${now()}`,
    apiUsage: client.apiUsage + 1,
  };
}

export async function testWebhook(client: PartnerClient): Promise<{ ok: boolean; message: string }> {
  return {
    ok: true,
    message: `Webhook delivered for ${client.name}`,
  };
}
