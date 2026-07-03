import React from "react";
import { StyleSheet, Text, View } from "react-native";
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
  shell: { marginVertical: 12, gap: 8, overflow: "hidden", borderRadius: 16 },
  map: { width: "100%", height: 280 },
  label: { color: "#425466", fontWeight: "700" },
});
