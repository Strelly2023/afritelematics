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
  authenticateUser,
  cancelRide,
  getApiBaseUrl,
  getRideEvidence,
  getRideReceipt,
  getRideReplay,
  getRideStatus,
  registerRider,
  requestRide,
  setApiBaseUrl,
  updateLocalProfile,
} from "../shared/apiClient";

const DEFAULT_RIDER_ID = "rider-1";

export default function App() {
  const [apiBaseUrl, setBaseUrlState] = useState(getApiBaseUrl());
  const [riderId, setRiderId] = useState(DEFAULT_RIDER_ID);
  const [fullName, setFullName] = useState("Rider One");
  const [phoneNumber, setPhoneNumber] = useState("+61-400-000-000");
  const [pickup, setPickup] = useState("Point A");
  const [destination, setDestination] = useState("Point B");
  const [rideId, setRideId] = useState("");
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [ride, setRide] = useState(null);
  const [history, setHistory] = useState([]);
  const [receipt, setReceipt] = useState(null);
  const [replay, setReplay] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const [settings, setSettings] = useState({
    notifications: "ENABLED",
    replay_view: "JSON",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const trackingSummary = useMemo(
    () => ({
      rideId: ride?.ride_id || rideId || "none",
      status: ride?.status || "not loaded",
      assignedDriver: ride?.assigned_driver || "searching",
    }),
    [ride, rideId],
  );

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
    await run("login_rider", async () => {
      const authenticated = await authenticateUser({
        role: "RIDER",
        userId: riderId.trim(),
      });
      setSession(authenticated);
    });
  }

  async function handleRegister() {
    await run("register_rider", async () => {
      const registered = await registerRider({
        riderId: riderId.trim(),
        fullName: fullName.trim(),
        phoneNumber: phoneNumber.trim(),
      });
      setSession(registered);
      setProfile(registered.profile);
    });
  }

  async function handleProfileSave() {
    await run("update_profile", async () => {
      const updated = await updateLocalProfile({
        role: "RIDER",
        userId: riderId.trim(),
        profile: {
          rider_id: riderId.trim(),
          full_name: fullName.trim(),
          phone_number: phoneNumber.trim(),
        },
      });
      setProfile(updated.profile);
    });
  }

  async function handleRequestRide() {
    await run("request_ride", async () => {
      const created = await requestRide({
        passengerId: riderId.trim(),
        pickup,
        destination,
        rideId: rideId.trim() || undefined,
      });
      setRide(created);
      setRideId(created.ride_id);
      setReceipt(null);
      setReplay(null);
      setEvidence(null);
      setHistory((current) => [created, ...current.filter((item) => item.ride_id !== created.ride_id)]);
    });
  }

  async function handleRefreshStatus() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("refresh_status", async () => {
      const current = await getRideStatus({
        riderId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setRide(current);
      setHistory((existing) => [current, ...existing.filter((item) => item.ride_id !== current.ride_id)]);
    });
  }

  async function handleCancelRide() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("cancel_ride", async () => {
      const cancelled = await cancelRide({
        passengerId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setRide(cancelled);
      setReceipt(null);
      setReplay(null);
      setEvidence(null);
    });
  }

  async function handleFetchReceipt() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("fetch_receipt", async () => {
      const fetched = await getRideReceipt({
        riderId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setReceipt(fetched);
    });
  }

  async function handleFetchReplay() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("fetch_replay", async () => {
      const fetched = await getRideReplay({
        role: "RIDER",
        userId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setReplay(fetched);
    });
  }

  async function handleFetchEvidence() {
    if (!rideId.trim()) {
      setError("ride_id_required");
      return;
    }
    await run("fetch_evidence", async () => {
      const fetched = await getRideEvidence({
        role: "RIDER",
        userId: riderId.trim(),
        rideId: rideId.trim(),
      });
      setEvidence(fetched);
    });
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AfriRide Rider</Text>
        <Text style={styles.subtle}>Real execution surface over rider trust endpoints.</Text>

        <Panel title="Login">
          <Field label="API base URL" value={apiBaseUrl} onChangeText={updateBaseUrl} />
          <Field label="Rider ID" value={riderId} onChangeText={setRiderId} />
          <View style={styles.buttonRow}>
            <ActionButton title="Login" disabled={loading} onPress={handleLogin} />
            <ActionButton title="Register" disabled={loading} tone="secondary" onPress={handleRegister} />
          </View>
          <Text style={styles.muted}>Session: {session?.role || "anonymous"}</Text>
        </Panel>

        <Panel title="Home">
          <Field label="Pickup" value={pickup} onChangeText={setPickup} />
          <Field label="Destination" value={destination} onChangeText={setDestination} />
          <Field label="Ride ID (optional)" value={rideId} onChangeText={setRideId} placeholder="auto-generated if empty" />
        </Panel>

        <Panel title="Request Ride">
          <ActionButton title={loading ? "Requesting..." : "Request Ride"} disabled={loading} onPress={handleRequestRide} />
        </Panel>

        <Panel title="Ride Tracking">
          <View style={styles.buttonRow}>
            <ActionButton title="Track rides" disabled={loading} tone="secondary" onPress={handleRefreshStatus} />
            <ActionButton title="Cancel ride" disabled={loading} tone="danger" onPress={handleCancelRide} />
          </View>
          <Text style={styles.muted}>Current ride: {trackingSummary.rideId}</Text>
          <Text style={styles.muted}>State: {trackingSummary.status}</Text>
          <Text style={styles.muted}>Assigned driver: {trackingSummary.assignedDriver}</Text>
        </Panel>

        <Panel title="Ride History">
          {history.length === 0 ? (
            <Text style={styles.muted}>No ride history loaded.</Text>
          ) : (
            history.map((entry) => (
              <View key={entry.ride_id} style={styles.card}>
                <Text style={styles.cardTitle}>{entry.ride_id}</Text>
                <Text style={styles.muted}>{entry.pickup} to {entry.destination}</Text>
                <Text style={styles.muted}>State: {entry.status}</Text>
              </View>
            ))
          )}
        </Panel>

        <Panel title="Receipt">
          <ActionButton title="View receipts" disabled={loading} tone="secondary" onPress={handleFetchReceipt} />
          <JsonText value={receipt} empty="No receipt loaded." />
        </Panel>

        <Panel title="Replay Viewer">
          <ActionButton title="View replay" disabled={loading} tone="secondary" onPress={handleFetchReplay} />
          <JsonText value={replay} empty="No replay loaded." />
        </Panel>

        <Panel title="Evidence Viewer">
          <ActionButton title="View replay/evidence" disabled={loading} tone="secondary" onPress={handleFetchEvidence} />
          <JsonText value={evidence} empty="No evidence loaded." />
        </Panel>

        <Panel title="Profile">
          <Field label="Full name" value={fullName} onChangeText={setFullName} />
          <Field label="Phone number" value={phoneNumber} onChangeText={setPhoneNumber} />
          <ActionButton title="Manage profile" disabled={loading} onPress={handleProfileSave} />
          <JsonText value={profile} empty="No profile saved yet." />
        </Panel>

        <Panel title="Settings">
          <Field
            label="Notifications"
            value={settings.notifications}
            onChangeText={(value) => setSettings((current) => ({ ...current, notifications: value }))}
          />
          <Field
            label="Replay display"
            value={settings.replay_view}
            onChangeText={(value) => setSettings((current) => ({ ...current, replay_view: value }))}
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
    padding: 20,
    gap: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: "700",
    color: "#15212f",
  },
  subtle: {
    color: "#607086",
    fontSize: 13,
  },
  panel: {
    borderRadius: 8,
    padding: 16,
    backgroundColor: "#ffffff",
    gap: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#15212f",
  },
  field: {
    gap: 4,
  },
  label: {
    color: "#344356",
    fontWeight: "600",
  },
  input: {
    borderColor: "#c9d3df",
    borderRadius: 6,
    borderWidth: 1,
    padding: 12,
    backgroundColor: "#fbfcfd",
  },
  button: {
    borderRadius: 6,
    padding: 14,
    alignItems: "center",
    flex: 1,
  },
  primaryButton: {
    backgroundColor: "#0f6b4f",
  },
  secondaryButton: {
    backgroundColor: "#d7efe7",
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
  buttonRow: {
    flexDirection: "row",
    gap: 10,
  },
  muted: {
    color: "#344356",
  },
  card: {
    borderColor: "#d6dbe2",
    borderRadius: 6,
    borderWidth: 1,
    padding: 10,
    gap: 4,
  },
  cardTitle: {
    color: "#15212f",
    fontWeight: "700",
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
