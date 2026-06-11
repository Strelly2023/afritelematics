import React, { useMemo, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import {
  getActiveRides,
  getApiBaseUrl,
  getDriversSnapshot,
  getEvidenceHealth,
  getGuardViolations,
  getPilotMetrics,
  getReplayHealth,
  getSystemHealth,
  getTrustMetrics,
  setApiBaseUrl,
  setDriverStatus,
} from "../shared/apiClient";

const DEFAULT_OPERATOR_ID = "operator-1";

const EMPTY_STATE = {
  systemHealth: null,
  activeRides: [],
  drivers: [],
  replayHealth: null,
  evidenceHealth: null,
  trustMetrics: null,
  pilotMetrics: null,
  guardViolations: [],
};

export default function App() {
  const [apiBaseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [operatorId, setOperatorId] = useState(DEFAULT_OPERATOR_ID);
  const [managedDriverId, setManagedDriverId] = useState("driver-1");
  const [state, setState] = useState(EMPTY_STATE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const summary = useMemo(() => {
    const guards = state.guardViolations.length;
    const driversOnline = state.systemHealth?.drivers_online ?? state.trustMetrics?.drivers_online ?? 0;
    const activeRides = state.systemHealth?.active_rides ?? state.activeRides.length;
    return { guards, driversOnline, activeRides };
  }, [state]);

  function updateBaseUrl(value) {
    setBaseUrlState(value);
    setApiBaseUrl(value);
  }

  async function run(label, action) {
    setLoading(true);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label}_failed`);
    } finally {
      setLoading(false);
    }
  }

  async function refresh() {
    await run("operator_refresh", async () => {
      const nextOperatorId = operatorId.trim();
      const [
        systemHealth,
        activeRidesPayload,
        driversPayload,
        replayHealth,
        evidenceHealth,
        trustMetrics,
        pilotMetrics,
        guardsPayload,
      ] = await Promise.all([
        getSystemHealth({ operatorId: nextOperatorId }),
        getActiveRides({ operatorId: nextOperatorId }),
        getDriversSnapshot({ operatorId: nextOperatorId }),
        getReplayHealth({ operatorId: nextOperatorId }),
        getEvidenceHealth({ operatorId: nextOperatorId }),
        getTrustMetrics({ operatorId: nextOperatorId }),
        getPilotMetrics({ operatorId: nextOperatorId }),
        getGuardViolations({ operatorId: nextOperatorId }),
      ]);

      setState({
        systemHealth,
        activeRides: activeRidesPayload.rides || [],
        drivers: driversPayload.drivers || [],
        replayHealth,
        evidenceHealth,
        trustMetrics,
        pilotMetrics,
        guardViolations: guardsPayload.violations || [],
      });
    });
  }

  async function setManagedDriverOnline(online) {
    await run("driver_management", async () => {
      await setDriverStatus({
        driverId: managedDriverId.trim(),
        online,
      });
      await refresh();
    });
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AfriRide Operator</Text>
        <Text style={styles.subtle}>
          Field operations, dispatch, monitoring, driver management, and incident handling over the authoritative trust surface.
        </Text>

        <Panel title="Login">
          <Field label="API base URL" value={apiBaseUrl} onChangeText={updateBaseUrl} />
          <Field label="Operator ID" value={operatorId} onChangeText={setOperatorId} />
          <ActionButton title="Refresh operator state" disabled={loading} onPress={refresh} />
        </Panel>

        <Panel title="Dispatch">
          <Text style={styles.metric}>Active rides: {summary.activeRides}</Text>
          <Text style={styles.metric}>Drivers online: {summary.driversOnline}</Text>
          <Text style={styles.metric}>Open incidents: {summary.guards}</Text>
        </Panel>

        <Panel title="Active Rides">
          {state.activeRides.length === 0 ? (
            <Text style={styles.muted}>No active rides.</Text>
          ) : (
            state.activeRides.map((ride) => (
              <View key={ride.ride_id} style={styles.card}>
                <Text style={styles.cardTitle}>{ride.ride_id}</Text>
                <Text style={styles.muted}>State: {ride.state}</Text>
                <Text style={styles.muted}>Driver: {ride.driver_id || "unassigned"}</Text>
                <Text style={styles.muted}>Rider: {ride.rider_id || "unknown"}</Text>
              </View>
            ))
          )}
        </Panel>

        <Panel title="Drivers">
          <Field label="Managed driver ID" value={managedDriverId} onChangeText={setManagedDriverId} />
          <View style={styles.buttonRow}>
            <ActionButton title="Set online" disabled={loading} onPress={() => setManagedDriverOnline(true)} />
            <ActionButton
              title="Set offline"
              disabled={loading}
              tone="danger"
              onPress={() => setManagedDriverOnline(false)}
            />
          </View>
          {state.drivers.length === 0 ? (
            <Text style={styles.muted}>No driver snapshot loaded.</Text>
          ) : (
            state.drivers.map((driver) => (
              <View key={driver.driver_id} style={styles.card}>
                <Text style={styles.cardTitle}>{driver.driver_id}</Text>
                <Text style={styles.muted}>Status: {driver.status}</Text>
                <Text style={styles.muted}>
                  Active rides: {(driver.active_ride_ids || []).join(", ") || "none"}
                </Text>
                <Text style={styles.muted}>Completed rides: {driver.completed_rides}</Text>
              </View>
            ))
          )}
        </Panel>

        <Panel title="Replay Health">
          <JsonText value={state.replayHealth} empty="No replay health loaded." />
        </Panel>

        <Panel title="Evidence">
          <JsonText value={state.evidenceHealth} empty="No evidence health loaded." />
        </Panel>

        <Panel title="Operations">
          <JsonText
            value={{
              systemHealth: state.systemHealth,
              trustMetrics: state.trustMetrics,
              pilotMetrics: state.pilotMetrics,
              guardViolations: state.guardViolations,
            }}
            empty="No operations surface loaded."
          />
        </Panel>

        {loading ? <ActivityIndicator /> : null}
        {error ? <Text style={styles.error}>{error}</Text> : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function Panel({ title, children }) {
  return (
    <View style={styles.panel}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Field({ label, ...props }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        autoCapitalize="none"
        autoCorrect={false}
        style={styles.input}
        {...props}
      />
    </View>
  );
}

function ActionButton({ title, onPress, disabled, tone = "primary" }) {
  return (
    <TouchableOpacity
      disabled={disabled}
      onPress={onPress}
      style={[
        styles.button,
        tone === "danger" ? styles.dangerButton : styles.primaryButton,
      ]}
    >
      <Text style={styles.buttonText}>{title}</Text>
    </TouchableOpacity>
  );
}

function JsonText({ value, empty }) {
  return (
    <Text style={styles.jsonText}>{value ? JSON.stringify(value, null, 2) : empty}</Text>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f4f6f8",
  },
  content: {
    gap: 14,
    padding: 18,
  },
  title: {
    color: "#0d2235",
    fontSize: 28,
    fontWeight: "700",
  },
  subtle: {
    color: "#536579",
    fontSize: 14,
    lineHeight: 20,
  },
  panel: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    gap: 10,
    padding: 16,
  },
  sectionTitle: {
    color: "#0d2235",
    fontSize: 18,
    fontWeight: "700",
  },
  field: {
    gap: 6,
  },
  label: {
    color: "#425468",
    fontSize: 13,
    fontWeight: "600",
  },
  input: {
    borderColor: "#d5dce3",
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  buttonRow: {
    flexDirection: "row",
    gap: 10,
  },
  button: {
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  primaryButton: {
    backgroundColor: "#0b6cff",
  },
  dangerButton: {
    backgroundColor: "#b42318",
  },
  buttonText: {
    color: "#ffffff",
    fontWeight: "700",
  },
  metric: {
    color: "#0d2235",
    fontSize: 15,
    fontWeight: "600",
  },
  card: {
    borderColor: "#dfe5eb",
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
    padding: 12,
  },
  cardTitle: {
    color: "#0d2235",
    fontWeight: "700",
  },
  muted: {
    color: "#55687d",
  },
  error: {
    color: "#b42318",
    fontWeight: "600",
  },
  jsonText: {
    color: "#344356",
    fontFamily: "Courier",
  },
});
