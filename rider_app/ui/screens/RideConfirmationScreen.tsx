import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { RideRequestResult } from "../../core/models/ride";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RideConfirmationScreenProps = {
  ride: RideRequestResult;
};

export function RideConfirmationScreen({ ride }: RideConfirmationScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Ride requested</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Ride</Text>
        <Text style={styles.value}>{ride.rideId}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Status</Text>
        <Text style={styles.value}>{ride.status}</Text>
      </View>
      {ride.quotedTotal ? (
        <View style={styles.row}>
          <Text style={styles.label}>Quoted total</Text>
          <Text style={styles.value}>{ride.quotedTotal}</Text>
        </View>
      ) : null}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  row: {
    gap: spacing.xs,
  },
  title: {
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800",
  },
  value: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "700",
  },
});
