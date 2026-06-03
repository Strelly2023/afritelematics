import CryptoJS from "crypto-js";
import React, { useMemo, useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

const DEFAULT_BASE_URL =
  process.env.EXPO_PUBLIC_AFRIRIDE_API_URL || "http://192.168.1.10:8000";

const EVENT_TYPES = {
  accept: "DRIVER_ACCEPTED_RIDE",
  start: "TRIP_STARTED",
  location: "DRIVER_LOCATION_UPDATE",
  complete: "TRIP_COMPLETED",
};

export default function App() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [deviceId, setDeviceId] = useState("ostrinov_phone_001");
  const [rideId, setRideId] = useState("day_one_002_phone_trip_001");
  const [secret, setSecret] = useState("pilot-secret");
  const [clock, setClock] = useState(0);
  const [pending, setPending] = useState([]);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState([
    "Set API URL to your Mac LAN IP. Do not use localhost from the phone.",
  ]);

  const endpoint = useMemo(() => `${baseUrl.replace(/\/$/, "")}/v1/events`, [baseUrl]);

  async function emit(action) {
    const nextClock = clock + 1;
    setClock(nextClock);
    const event = createEvent({
      action,
      clock: nextClock,
      deviceId: deviceId.trim(),
      rideId: rideId.trim(),
      secret,
    });
    await sendEvents([...pending, event], `${action} ${event.event_id}`);
  }

  async function sendSequence() {
    const actions = ["accept", "start", "location", "complete"];
    const events = actions.map((action, index) =>
      createEvent({
        action,
        clock: clock + index + 1,
        deviceId: deviceId.trim(),
        rideId: rideId.trim(),
        secret,
      }),
    );
    setClock(clock + actions.length);
    await sendEvents([...pending, ...events], "sequence");
  }

  async function syncPending() {
    await sendEvents(pending, "sync pending");
  }

  async function sendEvents(events, label) {
    if (events.length === 0) {
      addLog("no pending events to sync");
      return;
    }
    setBusy(true);
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          received_at_ms: Date.now(),
          events,
        }),
      });
      const payload = await response.json();
      const accepted = new Set(payload.accepted || []);
      const nextPending = events.filter((event) => !accepted.has(event.event_id));
      setPending(nextPending);
      addLog(
        `${label}: accepted=${JSON.stringify(payload.accepted || [])} rejected=${JSON.stringify(
          payload.rejected || [],
        )}`,
      );
    } catch (error) {
      setPending(events);
      addLog(`${label}: sync failed; ${events.length} event(s) pending; ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  function addLog(message) {
    setLog((items) => [`${new Date().toISOString()} ${message}`, ...items].slice(0, 12));
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AfriRide Phone Event Tester</Text>
        <Text style={styles.boundary}>
          Emits signed /v1/events for device-backed rehearsal. It does not define replay
          truth or certify pilot completion.
        </Text>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Connection</Text>
          <Field label="API base URL" value={baseUrl} onChangeText={setBaseUrl} />
          <Field label="Device ID" value={deviceId} onChangeText={setDeviceId} />
          <Field label="Ride ID" value={rideId} onChangeText={setRideId} />
          <Field label="Pilot secret" value={secret} onChangeText={setSecret} secureTextEntry />
          <Text style={styles.subtle}>{endpoint}</Text>
        </View>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Signed Events</Text>
          <View style={styles.grid}>
            <Button disabled={busy} label="Accept" onPress={() => emit("accept")} />
            <Button disabled={busy} label="Start" onPress={() => emit("start")} />
            <Button disabled={busy} label="Location" onPress={() => emit("location")} />
            <Button disabled={busy} label="Complete" onPress={() => emit("complete")} />
            <Button disabled={busy} label="Send Sequence" onPress={sendSequence} secondary />
            <Button disabled={busy} label="Sync Pending" onPress={syncPending} secondary />
          </View>
          <Text style={styles.status}>Pending events: {pending.length}</Text>
        </View>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Receipts</Text>
          {log.map((line) => (
            <Text key={line} style={styles.logLine}>
              {line}
            </Text>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function Field({label, ...props}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput autoCapitalize="none" autoCorrect={false} style={styles.input} {...props} />
    </View>
  );
}

function Button({disabled, label, onPress, secondary = false}) {
  return (
    <TouchableOpacity
      disabled={disabled}
      onPress={onPress}
      style={[styles.button, secondary ? styles.secondaryButton : styles.primaryButton]}
    >
      <Text style={[styles.buttonText, secondary ? styles.secondaryButtonText : null]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function createEvent({action, clock, deviceId, rideId, secret}) {
  const payload =
    action === "location"
      ? {lat: -37.8136, lon: 144.9631, ride_id: rideId}
      : {ride_id: rideId};
  const event = {
    device_id: deviceId,
    entity_id: rideId,
    event_id: `${deviceId}_${clock}`,
    event_type: EVENT_TYPES[action],
    logical_clock: clock,
    payload,
    timestamp: Date.now(),
  };
  return {
    ...event,
    signature: signEvent(event, secret),
  };
}

function signEvent(event, secret) {
  const signedPayload = {
    device_id: event.device_id,
    entity_id: event.entity_id,
    event_id: event.event_id,
    event_type: event.event_type,
    logical_clock: event.logical_clock,
    payload: event.payload,
    timestamp: event.timestamp,
  };
  return CryptoJS.HmacSHA256(stableStringify(signedPayload), secret).toString(CryptoJS.enc.Hex);
}

function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#f6f7f9",
    flex: 1,
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
  boundary: {
    color: "#475569",
    lineHeight: 20,
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
  subtle: {
    color: "#64748b",
    fontSize: 12,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  button: {
    borderRadius: 6,
    minWidth: "46%",
    padding: 12,
  },
  primaryButton: {
    backgroundColor: "#0f766e",
  },
  secondaryButton: {
    backgroundColor: "#ccfbf1",
  },
  buttonText: {
    color: "#ffffff",
    fontWeight: "700",
    textAlign: "center",
  },
  secondaryButtonText: {
    color: "#0f766e",
  },
  status: {
    color: "#0f766e",
    fontWeight: "700",
  },
  logLine: {
    color: "#334155",
    fontSize: 12,
    lineHeight: 17,
  },
});
