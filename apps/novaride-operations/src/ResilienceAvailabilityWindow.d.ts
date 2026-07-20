declare module "./ResilienceAvailabilityWindow.js" {
  import type React from "react";

  export interface NovaRideOperationsRuntimeConfig {
    baseUrl: string;
    liveMapEnabled: boolean;
    refundExecutionEnabled: boolean;
    productionActionsEnabled: boolean;
    requestTimeoutMs: number;
  }

  export interface NovaRideOperationsWorkspaceProps {
    api?: Record<string, unknown>;
    config?: Partial<NovaRideOperationsRuntimeConfig>;
    initialWorkspace?: unknown;
  }

  export function ResilienceAvailabilityWindow(
    props: NovaRideOperationsWorkspaceProps,
  ): React.ReactElement;
}

export {};
