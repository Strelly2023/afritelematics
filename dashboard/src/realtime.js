const WS_API_BASE_URL =
  import.meta?.env?.VITE_AFRIRIDE_API_URL ||
  (globalThis.location?.hostname === "localhost" || globalThis.location?.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : globalThis.location?.origin || "");

function toWebSocketBaseUrl(baseUrl) {
  const url = new URL(baseUrl || globalThis.location?.origin || "http://127.0.0.1:8000");
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url;
}

export function getDashboardRealtimeUrl(token) {
  const url = toWebSocketBaseUrl(WS_API_BASE_URL);
  url.pathname = "/ws/dashboard";
  url.search = token ? `?token=${encodeURIComponent(token)}` : "";
  return url.toString();
}

export function connectDashboardRealtime(token, handlers = {}) {
  const socket = new WebSocket(getDashboardRealtimeUrl(token));

  socket.onopen = () => {
    handlers.onOpen?.();
  };

  socket.onmessage = (event) => {
    try {
      handlers.onMessage?.(JSON.parse(event.data));
    } catch (error) {
      handlers.onError?.(error);
    }
  };

  socket.onerror = (event) => {
    handlers.onError?.(event);
  };

  socket.onclose = () => {
    handlers.onClose?.();
  };

  return socket;
}

