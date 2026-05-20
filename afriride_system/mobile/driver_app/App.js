import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import {
  API_BASE_URL,
  acceptRide,
  completeTrip,
  getDriverRequests,
  setDriverStatus,
  startTrip,
} from "../shared/apiClient";

const DRIVER_ID = "A";

export default function App() {
  const [online, setOnline] = useState(false);
  const [requests, setRequests] = useState([]);
  const [activeRide, setActiveRide] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!online) {
      return undefined;
    }

    const interval = setInterval(loadRequests, 3000);
    loadRequests();
    return () => clearInterval(interval);
  }, [online]);

  async function loadRequests() {
    try {
      const pending = await getDriverRequests(DRIVER_ID);
      setRequests(pending);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleOnline() {
    setLoading(true);
    setError("");

    try {
      const nextOnline = !online;
      await setDriverStatus({ driverId: DRIVER_ID, online: nextOnline });
      setOnline(nextOnline);
      if (!nextOnline) {
        setRequests([]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function runAction(action, rideId) {
    setLoading(true);
    setError("");

    try {
      const updated = await action({ driverId: DRIVER_ID, rideId });
      setActiveRide(updated);
      await loadRequests();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const candidateRide = activeRide || requests[0] || null;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>AfriRide Driver</Text>
        <Text style={styles.subtle}>{API_BASE_URL}</Text>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Driver {DRIVER_ID}</Text>
          <Text style={styles.status}>{online ? "ONLINE" : "OFFLINE"}</Text>
          <TouchableOpacity style={styles.primaryButton} onPress={toggleOnline}>
            <Text style={styles.primaryButtonText}>
              {online ? "Go Offline" : "Go Online"}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Requests</Text>
          {requests.length === 0 ? (
            <Text style={styles.detail}>No pending requests</Text>
          ) : (
            requests.map((ride) => (
              <View key={ride.ride_id} style={styles.requestRow}>
                <View>
                  <Text style={styles.detail}>{ride.ride_id}</Text>
                  <Text style={styles.subtle}>
                    {ride.pickup} to {ride.destination}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.smallButton}
                  onPress={() => runAction(acceptRide, ride.ride_id)}
                >
                  <Text style={styles.smallButtonText}>Accept</Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>

        <View style={styles.panel}>
          <Text style={styles.sectionTitle}>Trip Flow</Text>
          <Text style={styles.status}>{candidateRide?.status || "IDLE"}</Text>
          {candidateRide ? (
            <>
              <Text style={styles.detail}>Ride: {candidateRide.ride_id}</Text>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => runAction(startTrip, candidateRide.ride_id)}
              >
                <Text style={styles.secondaryButtonText}>Start Trip</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => runAction(completeTrip, candidateRide.ride_id)}
              >
                <Text style={styles.secondaryButtonText}>Complete Trip</Text>
              </TouchableOpacity>
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
  status: {
    fontSize: 22,
    fontWeight: "700",
    color: "#0f6b4f",
  },
  detail: {
    color: "#344356",
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
  secondaryButton: {
    borderRadius: 6,
    padding: 12,
    backgroundColor: "#e6f1ed",
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#0f6b4f",
    fontWeight: "700",
  },
  smallButton: {
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#0f6b4f",
  },
  smallButtonText: {
    color: "#ffffff",
    fontWeight: "700",
  },
  requestRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderColor: "#e1e7ef",
    borderTopWidth: 1,
    paddingTop: 12,
  },
  error: {
    color: "#b42318",
    fontWeight: "600",
  },
});
