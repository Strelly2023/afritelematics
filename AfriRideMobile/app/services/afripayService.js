import { apiRequest } from "./api";

export async function createAfriPayPayment(payload, token = null) {
  return apiRequest("/api/afripay/payments", {
    method: "POST",
    body: payload,
    token,
    headers: {
      "Idempotency-Key": payload.reference,
    },
  });
}

export async function quoteAfriPayFx(payload, token = null) {
  return apiRequest("/api/afripay/fx/quote", {
    method: "POST",
    body: payload,
    token,
  });
}

export async function getAfriPayTreasuryPools(token = null) {
  return apiRequest("/api/afripay/treasury/pools", {
    method: "GET",
    token,
  });
}

export async function exportAfriPayProof(payload = {}, token = null) {
  const params = new URLSearchParams();
  if (payload.reference) params.set("reference", payload.reference);
  if (payload.anchor_network) params.set("anchor_network", payload.anchor_network);
  const query = params.toString();
  return apiRequest(`/api/afripay/proofs/export${query ? `?${query}` : ""}`, {
    method: "GET",
    token,
  });
}

export async function anchorAfriPayProof(payload, token = null) {
  return apiRequest("/api/afripay/proofs/anchor", {
    method: "POST",
    body: payload,
    token,
  });
}
