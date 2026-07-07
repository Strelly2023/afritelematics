import React from "react";
import { StyleSheet, Text, View } from "react-native";
import Constants from "expo-constants";
import MapView, { Marker } from "react-native-maps";

import { openDriverNavigation } from "../../core/services/mobility.service";
import { PrimaryButton } from "./PrimaryButton";

export function DriverNavigationMap({
  location,
  destination,
}: {
  location?: { latitude: number; longitude: number } | null;
  destination?: string;
}) {
  const center = location || { latitude: 0.3476, longitude: 32.5825 };
  const mapsApiKey =
    Constants.expoConfig?.android?.config?.googleMaps?.apiKey?.trim();

  // Google Maps can hard-fail the app when the native key is missing.
  // Keep the driver shell usable and surface a safe fallback instead.
  if (!mapsApiKey) {
    return (
      <View style={styles.shell}>
        <View style={styles.fallbackCard}>
          <View style={styles.fallbackHeader}>
            <View>
              <Text style={styles.fallbackTitle}>Driver navigation</Text>
              <Text style={styles.fallbackSubtitle}>Map preview unavailable</Text>
            </View>
            <Text style={styles.safeBadge}>APP SAFE</Text>
          </View>
          <View style={styles.routeLine}>
            <View style={[styles.routeDot, styles.routeDotOrigin]} />
            <View style={styles.routeTrack} />
            <View style={[styles.routeDot, styles.routeDotDestination]} />
          </View>
          <View style={styles.routeLabels}>
            <Text style={styles.routeLabel}>
              {location
                ? `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`
                : "Current position pending"}
            </Text>
            <Text style={[styles.routeLabel, styles.routeLabelRight]}>
              {destination || "Destination pending"}
            </Text>
          </View>
          <Text style={styles.fallbackHelp}>
            Live dispatch remains available. Add a Google Maps API key to enable the interactive map.
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.shell}>
      <MapView
        style={styles.map}
        region={{ ...center, latitudeDelta: 0.025, longitudeDelta: 0.025 }}
        showsUserLocation
        followsUserLocation
        showsTraffic
        accessibilityLabel="Driver navigation map"
      >
        {location ? <Marker coordinate={location} title="Current position" /> : null}
      </MapView>
      <Text style={styles.label}>{destination || "Destination pending"}</Text>
      {destination ? (
        <PrimaryButton label="Start turn-by-turn navigation" onPress={() => void openDriverNavigation(destination)} />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  fallbackCard: {
    backgroundColor: "#eef6f3",
    borderColor: "#bddbcf",
    borderRadius: 20,
    borderWidth: 1,
    gap: 12,
    padding: 16,
  },
  fallbackHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  fallbackHelp: {
    color: "#587167",
    fontSize: 12,
    lineHeight: 18,
  },
  fallbackSubtitle: {
    color: "#5f726b",
    fontSize: 12,
    marginTop: 2,
  },
  fallbackTitle: {
    color: "#163d33",
    fontSize: 18,
    fontWeight: "900",
  },
  label: { color: "#425466", fontWeight: "700" },
  map: { width: "100%", height: 280 },
  routeDot: {
    borderColor: "#ffffff",
    borderRadius: 10,
    borderWidth: 3,
    height: 20,
    width: 20,
  },
  routeDotDestination: {
    backgroundColor: "#ef7c45",
  },
  routeDotOrigin: {
    backgroundColor: "#167d5a",
  },
  routeLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  routeLabel: {
    color: "#425466",
    fontSize: 11,
    width: "48%",
  },
  routeLabelRight: {
    textAlign: "right",
  },
  routeLine: {
    alignItems: "center",
    flexDirection: "row",
    marginTop: 18,
  },
  routeTrack: {
    backgroundColor: "#7eab9d",
    flex: 1,
    height: 3,
  },
  safeBadge: {
    backgroundColor: "#d7f1e7",
    borderRadius: 999,
    color: "#167d5a",
    fontSize: 10,
    fontWeight: "900",
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  shell: { marginVertical: 12, gap: 8, overflow: "hidden", borderRadius: 16 },
});
