import { apiRequest } from "./api";

export async function createNovaPayPayment(payload, token = null) {
  return apiRequest("/api/novapay/payments", {
    method: "POST",
    body: payload,
    token,
    headers: {
      "Idempotency-Key": payload.reference,
    },
  });
}

export async function quoteNovaPayFx(payload, token = null) {
  return apiRequest("/api/novapay/fx/quote", {
    method: "POST",
    body: payload,
    token,
  });
}

export async function getNovaPayTreasuryPools(token = null) {
  return apiRequest("/api/novapay/treasury/pools", {
    method: "GET",
    token,
  });
}

export async function exportNovaPayProof(payload = {}, token = null) {
  const params = new URLSearchParams();
  if (payload.reference) params.set("reference", payload.reference);
  if (payload.anchor_network) params.set("anchor_network", payload.anchor_network);
  const query = params.toString();
  return apiRequest(`/api/novapay/proofs/export${query ? `?${query}` : ""}`, {
    method: "GET",
    token,
  });
}

export async function anchorNovaPayProof(payload, token = null) {
  return apiRequest("/api/novapay/proofs/anchor", {
    method: "POST",
    body: payload,
    token,
  });
}
