import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import { ResilienceAvailabilityWindow } from "./ResilienceAvailabilityWindow.js";
import { createOperationsApi } from "./api/operationsApi.js";
import { getOperationsRuntimeConfig } from "./runtimeConfig.js";
import "./styles.css";

const AUTH_STORAGE_KEY = "novaride.operations.auth_token";
const SESSION_STORAGE_KEY = "novaride.operations.session";

type OperationsSession = {
  token: string;
  userId: string;
  role: string;
  tenantId: string;
  organizationId: string;
  region: string;
  exp: number;
};

type JwtClaims = {
  sub?: string;
  role?: string;
  tenant_id?: string;
  organization_id?: string;
  region?: string;
  exp?: number;
};

type LoginFormState = {
  userId: string;
  role: string;
  tenantId: string;
  organizationId: string;
  region: string;
};

const defaultLoginForm: LoginFormState = {
  userId: "ops_browser",
  role: "OPERATIONS_TEAM",
  tenantId: "novaride-tenant",
  organizationId: "novaride-org",
  region: "AU",
};

function safeDecodeBase64Url(value: string): string {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
  return atob(padded);
}

function decodeJwtClaims(token: string): JwtClaims | null {
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    return JSON.parse(safeDecodeBase64Url(parts[1])) as JwtClaims;
  } catch {
    return null;
  }
}

function sessionFromToken(token: string): OperationsSession | null {
  const claims = decodeJwtClaims(token);
  if (!claims?.sub || !claims?.role || !claims?.exp) {
    return null;
  }
  if (Date.now() >= claims.exp * 1000) {
    return null;
  }
  return {
    token,
    userId: claims.sub,
    role: claims.role,
    tenantId: claims.tenant_id || "novaride-tenant",
    organizationId: claims.organization_id || claims.tenant_id || "novaride-org",
    region: claims.region || "AU",
    exp: claims.exp,
  };
}

function loadSession(): { session: OperationsSession | null; expired: boolean } {
  if (typeof window === "undefined") {
    return { session: null, expired: false };
  }
  const token = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!token) return { session: null, expired: false };
  const session = sessionFromToken(token);
  if (!session) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return { session: null, expired: true };
  }
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  return { session, expired: false };
}

function persistSession(session: OperationsSession | null) {
  if (typeof window === "undefined") return;
  if (!session) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(AUTH_STORAGE_KEY, session.token);
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

function authEndpoint(baseUrl: string): string {
  const resolved = new URL(`${baseUrl.replace(/\/$/, "")}/`, window.location.href);
  return new URL("auth/token", resolved).toString();
}

function LoginScreen({
  config,
  error,
  onSignedIn,
}: {
  config: ReturnType<typeof getOperationsRuntimeConfig>;
  error: string;
  onSignedIn: (session: OperationsSession) => void;
}) {
  const [form, setForm] = useState<LoginFormState>(defaultLoginForm);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(error);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch(authEndpoint(config.authBaseUrl), {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          user_id: form.userId,
          role: form.role,
          tenant_id: form.tenantId,
          organization_id: form.organizationId,
          region: form.region,
        }),
        credentials: "include",
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(String(payload?.detail || payload?.message || `Authentication failed (${response.status})`));
      }
      const session = sessionFromToken(String(payload.token));
      if (!session) {
        throw new Error("Received an invalid or expired session token.");
      }
      persistSession(session);
      onSignedIn(session);
    } catch (loginError) {
      setMessage(loginError instanceof Error ? loginError.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="operations-shell auth-shell" aria-labelledby="auth-title">
      <section className="panel auth-panel">
        <p className="eyebrow">NovaRide operations</p>
        <h1 id="auth-title">Sign in to the operations workspace</h1>
        <p className="lede">Use a controlled test account to open the governed operations portal.</p>
        <form className="create-form auth-form" onSubmit={handleSubmit}>
          <label>
            <span>User ID</span>
            <input value={form.userId} onChange={(event) => setForm((current) => ({ ...current, userId: event.target.value }))} />
          </label>
          <label>
            <span>Role</span>
            <input value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))} />
          </label>
          <label>
            <span>Tenant</span>
            <input value={form.tenantId} onChange={(event) => setForm((current) => ({ ...current, tenantId: event.target.value }))} />
          </label>
          <label>
            <span>Organization</span>
            <input value={form.organizationId} onChange={(event) => setForm((current) => ({ ...current, organizationId: event.target.value }))} />
          </label>
          <label>
            <span>Region</span>
            <input value={form.region} onChange={(event) => setForm((current) => ({ ...current, region: event.target.value }))} />
          </label>
          {message ? <p className="notice" role="alert">{message}</p> : null}
          <button type="submit" className="action-button primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
      </section>
    </main>
  );
}

function AppShell() {
  const runtimeConfig = useMemo(() => getOperationsRuntimeConfig(), []);
  const operationsApi = useMemo(
    () =>
      createOperationsApi({
        baseUrl: runtimeConfig.baseUrl,
        timeoutMs: runtimeConfig.requestTimeoutMs,
        authTokenProvider: () => (typeof window === "undefined" ? null : window.localStorage.getItem(AUTH_STORAGE_KEY)),
      }),
    [runtimeConfig.baseUrl, runtimeConfig.requestTimeoutMs],
  );
  const [sessionState, setSessionState] = useState<{ session: OperationsSession | null; expired: boolean }>(() => loadSession());
  const [sessionError, setSessionError] = useState("");

  useEffect(() => {
    const timer = window.setInterval(() => {
      setSessionState(loadSession());
    }, 60_000);
    const onStorage = () => {
      setSessionState(loadSession());
    };
    window.addEventListener("storage", onStorage);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  function handleLogout() {
    persistSession(null);
    setSessionState({ session: null, expired: false });
    setSessionError("");
  }

  if (!sessionState.session) {
    return (
      <LoginScreen
        config={runtimeConfig}
        error={sessionState.expired ? "Your session expired. Sign in again." : sessionError}
        onSignedIn={(nextSession) => {
          setSessionState({ session: nextSession, expired: false });
          setSessionError("");
        }}
      />
    );
  }

  return (
    <div className="operations-app-root">
      <section className="session-banner panel panel-dense" aria-label="Authenticated session">
        <div>
          <p className="eyebrow">Authenticated operator session</p>
          <strong>{sessionState.session.userId}</strong>
          <p className="muted">{sessionState.session.role} · {sessionState.session.tenantId} · {sessionState.session.region}</p>
        </div>
        <button type="button" className="action-button secondary" onClick={handleLogout}>
          Sign out
        </button>
      </section>
      <ResilienceAvailabilityWindow api={operationsApi} config={runtimeConfig} />
    </div>
  );
}

const container = document.getElementById("root");

if (!container) {
  throw new Error("root container missing");
}

createRoot(container).render(
  <React.StrictMode>
    <AppShell />
  </React.StrictMode>,
);
