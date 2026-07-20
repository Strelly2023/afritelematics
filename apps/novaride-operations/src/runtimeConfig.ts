export type NovaRideOperationsRuntimeConfig = {
  baseUrl: string;
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
  liveMapEnabled: true,
  refundExecutionEnabled: false,
  productionActionsEnabled: false,
  requestTimeoutMs: 12_000,
};

export function getOperationsRuntimeConfig(): NovaRideOperationsRuntimeConfig {
  const injected = typeof window !== "undefined" ? window.__NOVARIDE_OPERATION_CONFIG__ : undefined;
  const meta = import.meta as ImportMeta & { env?: Record<string, string | undefined> };
  const envBaseUrl = typeof meta.env?.VITE_NOVARIDE_OPERATIONS_BASE_URL === "string" ? meta.env.VITE_NOVARIDE_OPERATIONS_BASE_URL : undefined;

  return {
    ...defaultConfig,
    ...injected,
    baseUrl: (injected?.baseUrl || envBaseUrl || defaultConfig.baseUrl).replace(/\/$/, ""),
  };
}
