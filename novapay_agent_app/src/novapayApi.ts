type BackendState = "loading" | "loaded" | "unauthorized" | "error";

type SurfaceList = Readonly<{
  view?: string;
  app?: Record<string, unknown>;
  agent_count?: number;
  wallet_count?: number;
  receipt_count?: number;
  status?: string;
  wallets?: readonly unknown[];
  receipts?: readonly unknown[];
  approvals?: readonly unknown[];
  holds?: readonly unknown[];
  summaries?: readonly unknown[];
}>;

export type AgentSurfaceState = Readonly<{
  status: BackendState;
  apiUrl: string;
  agent?: SurfaceList;
  profile?: SurfaceList;
  float?: SurfaceList;
  history?: SurfaceList;
  compliance?: SurfaceList;
  receipts?: SurfaceList;
  supervisorReview?: SurfaceList;
  message?: string;
}>;

type RuntimeGlobals = typeof globalThis & {
  __NOVAPAY_API_URL__?: string;
  __NOVAPAY_AUTH_TOKEN__?: string;
};

const DEFAULT_API_URL = "https://api.afritechnology.com";

function getRuntime(): RuntimeGlobals {
  return globalThis as RuntimeGlobals;
}

export function resolveNovaPayApiUrl(): string {
  return (getRuntime().__NOVAPAY_API_URL__ || DEFAULT_API_URL).replace(/\/+$/, "");
}

function resolveAuthToken(): string | undefined {
  const token = getRuntime().__NOVAPAY_AUTH_TOKEN__;
  return token && token.trim() ? token.trim() : undefined;
}

async function fetchJson(path: string): Promise<SurfaceList> {
  const response = await fetch(`${resolveNovaPayApiUrl()}${path}`, {
    headers: resolveAuthToken()
      ? {
          Authorization: `Bearer ${resolveAuthToken()}`,
          Accept: "application/json",
        }
      : {
          Accept: "application/json",
        },
  });
  if (response.status === 401 || response.status === 403) {
    throw Object.assign(new Error("unauthorized"), { status: response.status });
  }
  if (!response.ok) {
    throw new Error(`request_failed:${response.status}`);
  }
  return (await response.json()) as SurfaceList;
}

export async function loadAgentSurface(): Promise<AgentSurfaceState> {
  const apiUrl = resolveNovaPayApiUrl();
  try {
    const [agent, profile, floatSummary, history, compliance, receipts, supervisorReview] = await Promise.all([
      fetchJson("/v1/novapay/agents"),
      fetchJson("/v1/novapay/agents/profile"),
      fetchJson("/v1/novapay/agents/float"),
      fetchJson("/v1/novapay/agents/history"),
      fetchJson("/v1/novapay/agents/compliance"),
      fetchJson("/v1/novapay/agents/receipts"),
      fetchJson("/v1/novapay/agents/supervisor-review"),
    ]);
    return {
      status: "loaded",
      apiUrl,
      agent,
      profile,
      float: floatSummary,
      history,
      compliance,
      receipts,
      supervisorReview,
    };
  } catch (error: unknown) {
    const status = typeof error === "object" && error !== null && "status" in error ? Number((error as { status?: number }).status) : undefined;
    return {
      status: status === 401 || status === 403 ? "unauthorized" : "error",
      apiUrl,
      message: error instanceof Error ? error.message : String(error),
    };
  }
}
