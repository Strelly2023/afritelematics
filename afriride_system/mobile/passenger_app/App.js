import React, { useEffect, useState } from "react";
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
  API_BASE_URL,
  getRideStatus,
  requestRide,
} from "../shared/apiClient";

const PASSENGER_ID = "passenger-1";

export default function App() {
  const [pickup, setPickup] = useState("Kampala Road");
  const [destination, setDestination] = useState("Nakasero");
  const [ride, setRide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ride || ride.status === "COMPLETED" || ride.status === "CANCELED") {
      return undefined;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getRideStatus(ride.ride_id);
        setRide(updated);
        setError("");
      } catch (err) {
        setError(err.message);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [ride?.ride_id, ride?.status]);

  async function handleRequestRide() {
    setLoading(true);
    setError("");

    try {
      const created = await requestRide({
        passengerId: PASSENGER_ID,
        pickup,
        destination,
      });
      setRide(created);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const currentStatus = ride?.status || "READY";

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AfriRide Passenger</Text>
        <Text style={styles.subtle}>{API_BASE_URL}</Text>

        <View style={styles.mapPlaceholder}>
          <Text style={styles.mapText}>Map</Text>
        </View>

        <View style={styles.panel}>
          <Text style={styles.label}>Pickup</Text>
          <TextInput
            style={styles.input}
            value={pickup}
            onChangeText={setPickup}
          />

          <Text style={styles.label}>Destination</Text>
          <TextInput
            style={styles.input}
            value={destination}
            onChangeText={setDestination}
          />

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={handleRequestRide}
            disabled={loading}
          >
            <Text style={styles.primaryButtonText}>
              {loading ? "Requesting..." : "Request Ride"}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Ride Status</Text>
          <Text style={styles.status}>{currentStatus}</Text>
          {ride ? (
            <>
              <Text style={styles.detail}>Ride: {ride.ride_id}</Text>
              <Text style={styles.detail}>
                Driver: {ride.assigned_driver || "searching"}
              </Text>
              <Text style={styles.detail}>
                Trace: {ride.trace_hash || "pending"}
              </Text>
            </>
          ) : null}
          {loading ? <ActivityIndicator /> : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
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
    fontSize: 12,
  },
  mapPlaceholder: {
    height: 180,
    borderRadius: 8,
    backgroundColor: "#dfe7ee",
    alignItems: "center",
    justifyContent: "center",
  },
  mapText: {
    color: "#536476",
    fontSize: 18,
    fontWeight: "600",
  },
  panel: {
    borderRadius: 8,
    padding: 16,
    backgroundColor: "#ffffff",
    gap: 10,
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
  primaryButton: {
    borderRadius: 6,
    padding: 14,
    backgroundColor: "#0f6b4f",
    alignItems: "center",
  },
  primaryButtonText: {
    color: "#ffffff",
    fontWeight: "700",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#15212f",
  },
  status: {
    fontSize: 22,
    fontWeight: "700",
    color: "#0f6b4f",
  },
  detail: {
    color: "#344356",
  },
  error: {
    color: "#b42318",
    fontWeight: "600",
  },
});
