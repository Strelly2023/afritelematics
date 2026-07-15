export type NovaRideErrorCode =
  | "OFFLINE"
  | "DNS_FAILURE"
  | "TLS_FAILURE"
  | "TIMEOUT"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "CONFLICT"
  | "VALIDATION_ERROR"
  | "RATE_LIMITED"
  | "SERVER_ERROR"
  | "API_UNAVAILABLE"
  | "INCOMPATIBLE_CLIENT"
  | "UNKNOWN";

export type NovaRideClientOptions = {
  baseUrl: string;
  token?: string;
  apiVersion?: string;
  timeoutMs?: number;
  traceparent?: string;
};

export type RequestOptions = {
  idempotencyKey?: string;
  requestId?: string;
  offlineSafe?: boolean;
  traceparent?: string;
};

export class NovaRideApiError extends Error {
  constructor(
    public readonly code: NovaRideErrorCode,
    message: string,
    public readonly status?: number,
  ) {
    super(message);
  }
}

export class NovaRideApiClient {
  constructor(private readonly options: NovaRideClientOptions) {}

  private headers(options: RequestOptions = {}): Record<string, string> {
    const headers: Record<string, string> = {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "X-NovaRide-API-Version": this.options.apiVersion ?? "2026.2",
      "X-Request-ID": options.requestId ?? crypto.randomUUID(),
    };
    if (this.options.token) headers.Authorization = `Bearer ${this.options.token}`;
    if (options.idempotencyKey) headers["Idempotency-Key"] = options.idempotencyKey;
    if (options.traceparent ?? this.options.traceparent) {
      headers.traceparent = options.traceparent ?? this.options.traceparent ?? "";
    }
    return headers;
  }

  async request<T>(path: string, init: RequestInit = {}, options: RequestOptions = {}): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.options.timeoutMs ?? 15000);
    try {
      const response = await fetch(`${this.options.baseUrl}${path}`, {
        ...init,
        headers: { ...this.headers(options), ...(init.headers as Record<string, string> | undefined) },
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new NovaRideApiError(this.classify(response.status), await response.text(), response.status);
      }
      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof NovaRideApiError) throw error;
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new NovaRideApiError("TIMEOUT", "request_timeout");
      }
      throw new NovaRideApiError("UNKNOWN", "request_failed");
    } finally {
      clearTimeout(timeout);
    }
  }

  rider = {
    quote: (payload: unknown, options?: RequestOptions) =>
      this.request("/v1/rider/fares/quote", { method: "POST", body: JSON.stringify(payload) }, options),
    book: (payload: unknown, options: RequestOptions) =>
      this.request("/v1/rider/bookings", { method: "POST", body: JSON.stringify(payload) }, options),
  };

  driver = {
    availability: (driverId: string) => this.request(`/v1/driver/${driverId}/availability`, { method: "GET" }),
    acceptOffer: (offerId: string, options?: RequestOptions) =>
      this.request(`/v1/driver/offers/${offerId}/accept`, { method: "POST" }, options),
  };

  operator = {
    commandCenter: () => this.request("/v1/operator/command-center"),
  };

  private classify(status: number): NovaRideErrorCode {
    if (status === 401) return "UNAUTHORIZED";
    if (status === 403) return "FORBIDDEN";
    if (status === 404) return "NOT_FOUND";
    if (status === 409) return "CONFLICT";
    if (status === 422) return "VALIDATION_ERROR";
    if (status === 429) return "RATE_LIMITED";
    if (status >= 500) return "SERVER_ERROR";
    return "UNKNOWN";
  }
}
