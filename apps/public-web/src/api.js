import { fallbackProducts, fallbackServices, fallbackSite, fallbackTrust } from "./data.js";

const API_BASE = import.meta.env.VITE_AFRITECH_PUBLIC_API_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`request_failed:${response.status}`);
  }
  return response.json();
}

export async function loadPublicGateway() {
  const state = {
    site: fallbackSite,
    products: fallbackProducts,
    trust: fallbackTrust,
    downloads: fallbackSite.downloads || [],
    verifications: fallbackSite.verifications || [],
    status: {
      overall: "DEGRADED",
      note: "Live status API unavailable. Public content remains available from approved fallback records.",
      components: [],
    },
    degraded: false,
  };
  try {
    const [site, products, trust, status] = await Promise.all([
      request("/v1/public/site"),
      request("/v1/public/products"),
      request("/v1/public/trust"),
      request("/v1/public/status"),
    ]);
    let downloads = site.downloads || fallbackSite.downloads || [];
    let verifications = site.verification_records || fallbackSite.verifications || [];
    let services = fallbackServices;
    try {
      const catalog = await request("/v1/catalog/services");
      services = catalog.services || fallbackServices;
    } catch {
      services = fallbackServices;
    }
    try {
      const artifactCatalog = await request("/v1/public/downloads");
      downloads = artifactCatalog.artifacts || downloads;
    } catch {
      downloads = downloads;
    }
    try {
      const verificationCatalog = await request("/v1/public/verifications");
      verifications = verificationCatalog.records || verifications;
    } catch {
      verifications = verifications;
    }
    return {
      site,
      products: products.products,
      trust,
      status,
      services,
      downloads,
      verifications,
      degraded: false,
    };
  } catch (error) {
    return { ...state, services: fallbackServices, degraded: true, error: String(error.message || error) };
  }
}

export async function submitContact(payload) {
  return request("/v1/public/contact-requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function searchPublic(query) {
  return request("/v1/public/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
