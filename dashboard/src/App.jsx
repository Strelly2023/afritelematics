import { useEffect, useState } from "react";

const API_BASE_URL =
  import.meta?.env?.VITE_AFRIRIDE_API_URL || "http://127.0.0.1:8000";
const TEST_MODE = import.meta?.env?.VITE_AFRIRIDE_TEST_MODE !== "false";
const APP_VERSION = import.meta?.env?.VITE_AFRIRIDE_APP_VERSION || "0.1";
const DEVICE_ID = import.meta?.env?.VITE_AFRIRIDE_DEVICE_ID || "operator-test-device";

const EMPTY_OPERATOR_STATE = {
  activeRides: [],
  replayHealth: {
    replay_success_rate: "0%",
    failures: 0,
    status: "NO_DATA",
  },
  evidence: {
    receipts_count: 0,
    trace_count: 0,
    missing_traces: 0,
  },
  guards: [],
};

function clientHeaders() {
  const eventId =
    globalThis.crypto && "randomUUID" in globalThis.crypto
      ? globalThis.crypto.randomUUID()
      : `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`;

  return {
    "X-AfriRide-Device-Id": DEVICE_ID,
    "X-AfriRide-App-Version": APP_VERSION,
    "X-AfriRide-Event-Id": eventId,
    "X-AfriRide-Client-Timestamp": new Date().toISOString(),
    "X-AfriRide-Test-Mode": String(TEST_MODE),
  };
}

async function readJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: clientHeaders(),
  });
  if (!response.ok) {
    throw new Error(`operator_fetch_failed:${path}`);
  }
  return response.json();
}

function normalizeActiveRides(payload) {
  const rides = payload.rides || payload.active_rides || [];
  return rides.map((ride) => ({
    rideId: ride.ride_id || ride.rideId,
    state: ride.state || ride.status,
    driverId: ride.driver_id || ride.driverId || ride.assigned_driver_id,
    riderId: ride.rider_id || ride.riderId || ride.passenger_id,
  }));
}

function normalizeGuards(payload) {
  const violations = payload.violations || payload.guards || [];
  return violations.map((violation, index) => ({
    id: violation.id || `${violation.type || "guard"}-${index}`,
    type: violation.type || violation.violation_type || "UNKNOWN",
    timestamp: violation.timestamp || violation.created_at || "unavailable",
    severity: violation.severity || "INFO",
  }));
}

export default function OperatorDashboard() {
  const [state, setState] = useState(EMPTY_OPERATOR_STATE);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOperatorState();
    const interval = setInterval(fetchOperatorState, 3000);
    return () => clearInterval(interval);
  }, []);

  async function fetchOperatorState() {
    try {
      const [activeRides, replayHealth, evidence, guards] = await Promise.all([
        readJson("/rides/active"),
        readJson("/system/replay/health"),
        readJson("/system/evidence"),
        readJson("/system/guards"),
      ]);

      setState({
        activeRides: normalizeActiveRides(activeRides),
        replayHealth,
        evidence,
        guards: normalizeGuards(guards),
      });
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "operator_fetch_failed");
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-cyan-300">
            AfriRide GA Elite Test Operator
          </p>
          <h1 className="text-3xl font-semibold">Replay & Evidence Control</h1>
        </div>
        <div className="text-right text-sm text-slate-300">
          <div>Device: {DEVICE_ID}</div>
          <div>Mode: {TEST_MODE ? "TEST_MODE" : "STANDARD"}</div>
          <div>Updated: {lastUpdated || "pending"}</div>
        </div>
      </header>

      {error && (
        <section className="mb-4 border border-red-500 bg-red-950 p-3 text-sm">
          {error}
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-4">
        <SummaryTile label="Active rides" value={state.activeRides.length} />
        <SummaryTile
          label="Replay success"
          value={state.replayHealth.replay_success_rate || "0%"}
        />
        <SummaryTile
          label="Receipts"
          value={state.evidence.receipts_count || 0}
        />
        <SummaryTile
          label="Missing traces"
          value={state.evidence.missing_traces || 0}
          danger={Number(state.evidence.missing_traces || 0) > 0}
        />
      </section>

      <section className="mt-4 grid gap-4 lg:grid-cols-2">
        <Panel title="Active Rides">
          {state.activeRides.length === 0 ? (
            <EmptyState label="No active rides" />
          ) : (
            <div className="space-y-2">
              {state.activeRides.map((ride) => (
                <div key={ride.rideId} className="border border-slate-700 p-3">
                  <div className="flex justify-between gap-3">
                    <strong>{ride.rideId}</strong>
                    <span>{ride.state}</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-300">
                    Driver: {ride.driverId || "unassigned"} | Rider:{" "}
                    {ride.riderId || "unknown"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        <Panel title="Replay Health">
          <KeyValue label="Status" value={state.replayHealth.status || "NO_DATA"} />
          <KeyValue
            label="Replay Success Rate"
            value={state.replayHealth.replay_success_rate || "0%"}
          />
          <KeyValue label="Failures" value={state.replayHealth.failures || 0} />
        </Panel>

        <Panel title="Evidence Pipeline">
          <KeyValue label="Receipts Count" value={state.evidence.receipts_count || 0} />
          <KeyValue label="Trace Count" value={state.evidence.trace_count || 0} />
          <KeyValue label="Missing Traces" value={state.evidence.missing_traces || 0} />
        </Panel>

        <Panel title="Guard Violations">
          {state.guards.length === 0 ? (
            <EmptyState label="No guard violations" />
          ) : (
            <div className="space-y-2">
              {state.guards.map((violation) => (
                <div key={violation.id} className="border border-slate-700 p-3">
                  <div className="flex justify-between gap-3">
                    <strong>{violation.type}</strong>
                    <span>{violation.severity}</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-300">
                    {violation.timestamp}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </section>
    </main>
  );
}

function SummaryTile({ label, value, danger = false }) {
  return (
    <div className="border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className={danger ? "mt-1 text-2xl text-red-300" : "mt-1 text-2xl"}>
        {value}
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <section className="border border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function KeyValue({ label, value }) {
  return (
    <div className="flex justify-between border-b border-slate-800 py-2 text-sm">
      <span className="text-slate-400">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ label }) {
  return <div className="border border-dashed border-slate-700 p-4 text-slate-400">{label}</div>;
}
