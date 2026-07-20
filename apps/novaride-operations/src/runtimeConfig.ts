export type NovaRideOperationsRuntimeConfig = {
  baseUrl: string;
  authBaseUrl: string;
  liveMapEnabled: boolean;
  refundExecutionEnabled: boolean;
  productionActionsEnabled: boolean;
  requestTimeoutMs: number;
};

declare global {
  interface Window {
    __NOVARIDE_OPERATION_CONFIG__?: Partial<NovaRideOperationsRuntimeConfig>;
  }
}

const defaultConfig: NovaRideOperationsRuntimeConfig = {
  baseUrl: "/api/v1/novaride/operations",
  authBaseUrl: "/v1",
  liveMapEnabled: true,
  refundExecutionEnabled: false,
  productionActionsEnabled: false,
  requestTimeoutMs: 12_000,
};

function parseBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value == null) return fallback;
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

export function getOperationsRuntimeConfig(): NovaRideOperationsRuntimeConfig {
  const injected = typeof window !== "undefined" ? window.__NOVARIDE_OPERATION_CONFIG__ : undefined;
  const meta = import.meta as ImportMeta & { env?: Record<string, string | undefined> };
  const envBaseUrl = typeof meta.env?.VITE_NOVARIDE_OPERATIONS_BASE_URL === "string" ? meta.env.VITE_NOVARIDE_OPERATIONS_BASE_URL : undefined;
  const envAuthBaseUrl = typeof meta.env?.VITE_NOVARIDE_AUTH_BASE_URL === "string" ? meta.env.VITE_NOVARIDE_AUTH_BASE_URL : undefined;
  const envLiveMapEnabled = parseBoolean(meta.env?.VITE_NOVARIDE_OPERATIONS_LIVE_MAP_ENABLED, defaultConfig.liveMapEnabled);
  const envRefundExecutionEnabled = parseBoolean(meta.env?.VITE_NOVARIDE_OPERATIONS_REFUND_EXECUTION_ENABLED, defaultConfig.refundExecutionEnabled);
  const envProductionActionsEnabled = parseBoolean(meta.env?.VITE_NOVARIDE_OPERATIONS_PRODUCTION_ACTIONS_ENABLED, defaultConfig.productionActionsEnabled);

  return {
    ...defaultConfig,
    ...injected,
    baseUrl: (injected?.baseUrl || envBaseUrl || defaultConfig.baseUrl).replace(/\/$/, ""),
    authBaseUrl: (injected?.authBaseUrl || envAuthBaseUrl || defaultConfig.authBaseUrl).replace(/\/$/, ""),
    liveMapEnabled: injected?.liveMapEnabled ?? envLiveMapEnabled,
    refundExecutionEnabled: injected?.refundExecutionEnabled ?? envRefundExecutionEnabled,
    productionActionsEnabled: injected?.productionActionsEnabled ?? envProductionActionsEnabled,
  };
}
