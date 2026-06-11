import React, { useState } from "react";
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
  acceptRide,
  arriveRide,
  authenticateUser,
  completeTrip,
  getApiBaseUrl,
  getDriverAssignedRides,
  getDriverEarnings,
  getRideReceipt,
  getRideReplay,
  setApiBaseUrl,
  setDriverStatus,
  startTrip,
  updateLocalProfile,
} from "../shared/apiClient";

const DEFAULT_DRIVER_ID = "driver-1";

export default function App() {
  const [apiBaseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [driverId, setDriverId] = useState(DEFAULT_DRIVER_ID);
  const [displayName, setDisplayName] = useState("Driver One");
  const [vehicle, setVehicle] = useState("Toyota Pilot");
  const [rideId, setRideId] = useState("");
  const [online, setOnline] = useState(false);
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [rides, setRides] = useState([]);
  const [trip, setTrip] = useState(null);
  const [earnings, setEarnings] = useState(null);
  const [replay, setReplay] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  async function handleLogin() {
    await run("driver_login", async () => {
      const authenticated = await authenticateUser({
        role: "DRIVER",
        userId: driverId.trim(),
      });
      setSession(authenticated);
    });
  }

  async function handleProfileSave() {
    await run("driver_profile", async () => {
      const updated = await updateLocalProfile({
        role: "DRIVER",
        userId: driverId.trim(),
        profile: {
          driver_id: driverId.trim(),
          display_name: displayName.trim(),
          vehicle: vehicle.trim(),
        },
      });
      setProfile(updated.profile);
    });
  }

  async function handleAvailability(nextOnline) {
    await run("set_availability", async () => {
      const status = await setDriverStatus({
        driverId: driverId.trim(),
        online: nextOnline,
      });
      setOnline(Boolean(status.online));
      if (!nextOnline) {
        setRides([]);
      }
    });
  }

  async function handleLoadRides() {
    await run("load_rides", async () => {
      const assigned = await getDriverAssignedRides({ driverId: driverId.trim() });
      setRides(assigned.rides || []);
    });
  }

  async function handleAcceptRide(selectedRideId) {
    await run("accept_ride", async () => {
      const accepted = await acceptRide({
        driverId: driverId.trim(),
        rideId: selectedRideId,
      });
      setTrip(accepted);
      setRideId(selectedRideId);
      setRides((current) => current.filter((ride) => ride.ride_id !== selectedRideId));
      setReplay(null);
      setReceipt(null);
    });
  }

  async function handleArriveRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("arrive_trip", async () => {
      const arrived = await arriveRide({
        driverId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setTrip(arrived);
    });
  }

  async function handleStartRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("start_trip", async () => {
      const started = await startTrip({
        driverId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setTrip(started);
    });
  }

  async function handleCompleteRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("complete_trip", async () => {
      const completed = await completeTrip({
        driverId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setTrip(completed);
    });
  }

  async function handleLoadEarnings() {
    await run("driver_earnings", async () => {
      const snapshot = await getDriverEarnings({ driverId: driverId.trim() });
      setEarnings(snapshot);
    });
  }

  async function handleLoadReplay() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("driver_replay", async () => {
      const snapshot = await getRideReplay({
        role: "DRIVER",
        userId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setReplay(snapshot);
    });
  }

  async function handleLoadReceipt() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("driver_receipt", async () => {
      const snapshot = await getRideReceipt({
        riderId: driverId.trim(),
        rideId: rideId.trim(),
      });
      setReceipt(snapshot);
    });
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AfriRide Driver</Text>
        <Text style={styles.subtle}>Real execution surface over driver trust endpoints.</Text>

        <Panel title="Login">
          <Field label="API base URL" value={apiBaseUrl} onChangeText={updateBaseUrl} />
          <Field label="Driver ID" value={driverId} onChangeText={setDriverId} />
          <ActionButton title="Login" disabled={loading} onPress={handleLogin} />
          <Text style={styles.muted}>Session: {session?.role || "anonymous"}</Text>
        </Panel>

        <Panel title="Profile">
          <Field label="Display name" value={displayName} onChangeText={setDisplayName} />
          <Field label="Vehicle" value={vehicle} onChangeText={setVehicle} />
          <ActionButton title="Manage profile" disabled={loading} tone="secondary" onPress={handleProfileSave} />
          <JsonText value={profile} empty="No profile saved yet." />
        </Panel>

        <Panel title="Available Rides">
          <Text style={styles.status}>Status: {online ? "ONLINE" : "OFFLINE"}</Text>
          <View style={styles.buttonRow}>
            <ActionButton title="Go online" disabled={loading} onPress={() => handleAvailability(true)} />
            <ActionButton title="Go offline" disabled={loading} tone="danger" onPress={() => handleAvailability(false)} />
          </View>
          <ActionButton title="Refresh ride queue" disabled={loading} tone="secondary" onPress={handleLoadRides} />
          {rides.length === 0 ? (
            <Text style={styles.muted}>No rides loaded.</Text>
          ) : (
            rides.map((ride) => (
              <View key={ride.ride_id} style={styles.card}>
                <Text style={styles.cardTitle}>{ride.ride_id}</Text>
                <Text style={styles.muted}>{ride.pickup} to {ride.dropoff}</Text>
                <ActionButton title="Accept" disabled={loading} onPress={() => handleAcceptRide(ride.ride_id)} />
              </View>
            ))
          )}
        </Panel>

        <Panel title="Assigned Ride">
          <Field label="Ride ID" value={rideId} onChangeText={setRideId} />
          <Text style={styles.muted}>Current ride: {trip?.ride_id || rideId || "none"}</Text>
          <Text style={styles.muted}>Trip state: {trip?.status || "not started"}</Text>
          <Text style={styles.muted}>Assigned driver: {trip?.assigned_driver || driverId}</Text>
        </Panel>

        <Panel title="Trip Lifecycle">
          <View style={styles.buttonWrap}>
            <ActionButton title="Accept" disabled={loading || rides.length === 0} onPress={() => handleAcceptRide(rideId.trim())} />
            <ActionButton title="Arrive" disabled={loading} tone="secondary" onPress={handleArriveRide} />
            <ActionButton title="Start" disabled={loading} tone="secondary" onPress={handleStartRide} />
            <ActionButton title="Complete" disabled={loading} onPress={handleCompleteRide} />
          </View>
        </Panel>

        <Panel title="Earnings">
          <ActionButton title="View earnings" disabled={loading} tone="secondary" onPress={handleLoadEarnings} />
          <JsonText value={earnings} empty="No earnings snapshot loaded." />
        </Panel>

        <Panel title="Replay">
          <ActionButton title="View replay" disabled={loading} tone="secondary" onPress={handleLoadReplay} />
          <JsonText value={replay} empty="No replay loaded." />
        </Panel>

        <Panel title="Receipt">
          <ActionButton title="View receipts" disabled={loading} tone="secondary" onPress={handleLoadReceipt} />
          <JsonText value={receipt} empty="No receipt loaded." />
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
      <TextInput autoCapitalize="none" autoCorrect={false} style={styles.input} {...props} />
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
        tone === "primary"
          ? styles.primaryButton
          : tone === "danger"
            ? styles.dangerButton
            : styles.secondaryButton,
      ]}
    >
      <Text style={[styles.buttonText, tone === "secondary" ? styles.secondaryButtonText : null]}>
        {title}
      </Text>
    </TouchableOpacity>
  );
}

function JsonText({ value, empty }) {
  return <Text style={styles.jsonText}>{value ? JSON.stringify(value, null, 2) : empty}</Text>;
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#f6f7f9",
  },
  content: {
    gap: 14,
    padding: 18,
  },
  title: {
    color: "#15212f",
    fontSize: 26,
    fontWeight: "700",
  },
  subtle: {
    color: "#607086",
    fontSize: 13,
  },
  panel: {
    backgroundColor: "#ffffff",
    borderRadius: 8,
    gap: 10,
    padding: 14,
  },
  sectionTitle: {
    color: "#15212f",
    fontSize: 18,
    fontWeight: "700",
  },
  field: {
    gap: 4,
  },
  label: {
    color: "#334155",
    fontWeight: "600",
  },
  input: {
    borderColor: "#cbd5e1",
    borderRadius: 6,
    borderWidth: 1,
    padding: 10,
  },
  status: {
    color: "#0f766e",
    fontSize: 16,
    fontWeight: "700",
  },
  buttonRow: {
    flexDirection: "row",
    gap: 8,
  },
  buttonWrap: {
    gap: 8,
  },
  button: {
    borderRadius: 6,
    padding: 12,
    alignItems: "center",
  },
  primaryButton: {
    backgroundColor: "#0f766e",
  },
  secondaryButton: {
    backgroundColor: "#ccfbf1",
  },
  dangerButton: {
    backgroundColor: "#b42318",
  },
  buttonText: {
    color: "#ffffff",
    fontWeight: "700",
  },
  secondaryButtonText: {
    color: "#0f5132",
  },
  card: {
    borderColor: "#d6dbe2",
    borderRadius: 6,
    borderWidth: 1,
    padding: 10,
    gap: 6,
  },
  cardTitle: {
    color: "#15212f",
    fontWeight: "700",
  },
  muted: {
    color: "#344356",
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
