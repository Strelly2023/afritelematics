import React from "react";
import { StyleSheet, Text, View } from "react-native";
import Constants from "expo-constants";
import MapView, { Marker, Polyline } from "react-native-maps";

type Coordinate = { latitude: number; longitude: number };

export function InteractiveRideMap({
  rider,
  driver,
}: {
  rider?: Coordinate | null;
  driver?: Coordinate | null;
}) {
  const center = driver || rider || { latitude: 0.3476, longitude: 32.5825 };
  const mapsApiKey =
    Constants.expoConfig?.android?.config?.googleMaps?.apiKey?.trim();

  // Google Maps throws an uncaught native exception when MapView is mounted
  // without an API key. Keep the pilot app usable until a key is configured.
  if (!mapsApiKey) {
    return (
      <View style={[styles.shell, styles.fallback]}>
        <View style={styles.routeHeader}>
          <View>
            <Text style={styles.fallbackTitle}>Live route</Text>
            <Text style={styles.fallbackStatus}>Map preview unavailable</Text>
          </View>
          <Text style={styles.safeBadge}>APP SAFE</Text>
        </View>
        <View style={styles.routeLine}>
          <View style={[styles.routePoint, styles.riderPoint]} />
          <View style={styles.routeTrack} />
          <View style={[styles.routePoint, styles.driverPoint]} />
        </View>
        <View style={styles.routeLabels}>
          <Text style={styles.routeLabel}>
            {rider ? `${rider.latitude.toFixed(4)}, ${rider.longitude.toFixed(4)}` : "Pickup pending"}
          </Text>
          <Text style={[styles.routeLabel, styles.routeLabelRight]}>
            {driver ? `${driver.latitude.toFixed(4)}, ${driver.longitude.toFixed(4)}` : "Driver pending"}
          </Text>
        </View>
        <Text style={styles.fallbackHelp}>
          Booking and live status remain available. Add a Google Maps API key to enable the interactive map.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.shell}>
      <MapView
        style={styles.map}
        region={{ ...center, latitudeDelta: 0.035, longitudeDelta: 0.035 }}
        showsUserLocation
        showsMyLocationButton
        accessibilityLabel="Interactive ride map"
      >
        {rider ? <Marker coordinate={rider} title="Your pickup" pinColor="#167d5a" /> : null}
        {driver ? <Marker coordinate={driver} title="Your driver" /> : null}
        {rider && driver ? (
          <Polyline coordinates={[driver, rider]} strokeColor="#135f4a" strokeWidth={4} />
        ) : null}
      </MapView>
      <Text style={styles.caption}>Drag and zoom · live driver and pickup positions</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { marginTop: 12, overflow: "hidden", borderRadius: 16 },
  map: { width: "100%", height: 260 },
  caption: { padding: 10, color: "#425466", backgroundColor: "#eef5f2" },
  fallback: {
    backgroundColor: "#eaf4f0",
    borderColor: "#b9d7cc",
    borderWidth: 1,
    padding: 16,
  },
  routeHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  fallbackTitle: {
    color: "#153d32",
    fontSize: 18,
    fontWeight: "900",
  },
  fallbackStatus: {
    color: "#5b716a",
    fontSize: 12,
    marginTop: 2,
  },
  safeBadge: {
    backgroundColor: "#d7f1e7",
    borderRadius: 999,
    color: "#167d5a",
    fontSize: 10,
    fontWeight: "900",
    overflow: "hidden",
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  routeLine: {
    alignItems: "center",
    flexDirection: "row",
    marginHorizontal: 8,
    marginTop: 28,
  },
  routePoint: {
    borderColor: "#ffffff",
    borderRadius: 9,
    borderWidth: 3,
    height: 18,
    width: 18,
  },
  riderPoint: { backgroundColor: "#167d5a" },
  driverPoint: { backgroundColor: "#ef7c45" },
  routeTrack: {
    backgroundColor: "#7eab9d",
    flex: 1,
    height: 3,
  },
  routeLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 8,
  },
  routeLabel: {
    color: "#425466",
    fontSize: 11,
    width: "48%",
  },
  routeLabelRight: { textAlign: "right" },
  fallbackHelp: {
    color: "#536b63",
    fontSize: 12,
    lineHeight: 17,
    marginTop: 20,
  },
});
