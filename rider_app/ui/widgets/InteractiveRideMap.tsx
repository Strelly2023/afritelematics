import React from "react";
import { StyleSheet, Text, View } from "react-native";
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
});
