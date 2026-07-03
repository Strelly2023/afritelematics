export type RealtimeEvent = {
  contract: "afriride.mobility.v1";
  type: string;
  sequence: number | null;
  stream_id?: string | null;
  authority: "server_projection";
  data: Record<string, unknown>;
};

export type RealtimeConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "recovering"
  | "offline";

type CursorStorage = {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
};

type RealtimeOptions = {
  apiBaseUrl: string;
  actorId: string;
  token: string;
  rideId?: string;
  storage: CursorStorage;
  onEvent(event: RealtimeEvent): void;
  onState(state: RealtimeConnectionState): void;
};

const MAX_BACKOFF_MS = 30_000;
const HEARTBEAT_MS = 15_000;

export class AfriRideRealtimeClient {
  private socket: WebSocket | null = null;
  private stopped = true;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private cursor = "0";

  constructor(private readonly options: RealtimeOptions) {}

  private get cursorKey() {
    return `@afriride/realtime/${this.options.actorId}/${this.options.rideId || "dispatch"}/cursor`;
  }

  async start() {
    if (!this.stopped) return;
    this.stopped = false;
    this.cursor = (await this.options.storage.getItem(this.cursorKey)) || "0";
    this.connect();
  }

  stop() {
    this.stopped = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    this.socket?.close(1000, "client_stopped");
    this.socket = null;
    this.options.onState("idle");
  }

  private connect() {
    if (this.stopped) return;
    this.options.onState(this.reconnectAttempt ? "recovering" : "connecting");
    const base = this.options.apiBaseUrl.replace(/^http/, "ws").replace(/\/$/, "");
    const params = new URLSearchParams({
      token: this.options.token,
      cursor: String(this.cursor),
    });
    if (this.options.rideId) params.set("ride_id", this.options.rideId);
    const socket = new WebSocket(
      `${base}/ws/mobility/${encodeURIComponent(this.options.actorId)}?${params.toString()}`,
    );
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.options.onState("connected");
      this.sendHeartbeat();
      this.heartbeatTimer = setInterval(() => this.sendHeartbeat(), HEARTBEAT_MS);
    };
    socket.onmessage = (message) => {
      try {
        const event = JSON.parse(String(message.data)) as RealtimeEvent;
        if (event.contract !== "afriride.mobility.v1") return;
        const nextCursor = event.stream_id || (event.sequence != null ? String(event.sequence) : null);
        if (nextCursor) {
          this.cursor = nextCursor;
          void this.options.storage.setItem(this.cursorKey, this.cursor);
        }
        this.options.onEvent(event);
      } catch {
        // Invalid frames are ignored; the socket remains available for recovery.
      }
    };
    socket.onerror = () => this.options.onState("offline");
    socket.onclose = () => {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
      if (!this.stopped) this.scheduleReconnect();
    };
  }

  private sendHeartbeat() {
    if (this.socket?.readyState !== WebSocket.OPEN) return;
    this.socket.send(
      JSON.stringify({
        type: "HEARTBEAT",
        cursor: this.cursor,
        sent_at: new Date().toISOString(),
      }),
    );
  }

  private scheduleReconnect() {
    this.reconnectAttempt += 1;
    const exponential = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** (this.reconnectAttempt - 1));
    const jitter = Math.floor(Math.random() * Math.min(1000, exponential / 4));
    this.options.onState("recovering");
    this.reconnectTimer = setTimeout(() => this.connect(), exponential + jitter);
  }
}
