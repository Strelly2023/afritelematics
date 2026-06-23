/**
 * NovaTrust public verification SDK.
 *
 * Dependency-free ESM client for partner systems. It uses only public,
 * read-only NovaTrust endpoints.
 */

export class NovaTrustClient {
  constructor({ baseUrl, fetchImpl = globalThis.fetch }) {
    if (!baseUrl) {
      throw new Error("baseUrl is required");
    }
    if (!fetchImpl) {
      throw new Error("fetch implementation is required");
    }
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.fetch = fetchImpl;
  }

  explorerUrl(trustId) {
    return `${this.baseUrl}/trust/explorer/${encodeURIComponent(trustId)}`;
  }

  auditPdfUrl(trustId) {
    return `${this.explorerUrl(trustId)}/audit.pdf`;
  }

  bundleUrl(trustId) {
    return `${this.explorerUrl(trustId)}/bundle.zip`;
  }

  async fetchPacket(trustId) {
    return this.#getJson(this.explorerUrl(trustId));
  }

  async fetchSignature(trustId) {
    return this.#getJson(`${this.explorerUrl(trustId)}/signature`);
  }

  async fetchComplianceReport(trustId) {
    return this.#getJson(`${this.explorerUrl(trustId)}/compliance-report`);
  }

  async fetchAnchor(trustId) {
    return this.#getJson(`${this.explorerUrl(trustId)}/anchor`);
  }

  async fetchOptionalBlockchainAnchor(trustId) {
    return this.#getJson(`${this.explorerUrl(trustId)}/anchor/blockchain`);
  }

  async verify(trustId) {
    const [packet, signature, complianceReport] = await Promise.all([
      this.fetchPacket(trustId),
      this.fetchSignature(trustId),
      this.fetchComplianceReport(trustId),
    ]);

    return {
      trustId,
      explorerUrl: this.explorerUrl(trustId),
      auditPdfUrl: this.auditPdfUrl(trustId),
      bundleUrl: this.bundleUrl(trustId),
      signatureVerified: signature.verified === true,
      payloadHash: signature.signature?.payload_hash || null,
      controlCount: Array.isArray(complianceReport.controls)
        ? complianceReport.controls.length
        : 0,
      packet,
      signature,
      complianceReport,
    };
  }

  async #getJson(url) {
    const response = await this.fetch(url, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      throw new Error(`NovaTrust request failed: ${response.status} ${url}`);
    }
    return response.json();
  }
}
