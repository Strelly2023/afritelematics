import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { DriverRideRequest } from "../../core/models/driver";
import { PrimaryButton } from "../widgets/PrimaryButton";
import { SurfacePanel } from "../widgets/SurfacePanel";
import { colors } from "../theme/colors";
import { spacing } from "../theme/spacing";

type RideRequestsScreenProps = {
  requests: DriverRideRequest[];
  loading: boolean;
  onAccept: (rideId: string) => void;
  onReject: (rideId: string) => void;
};

export function RideRequestsScreen({
  requests,
  loading,
  onAccept,
  onReject,
}: RideRequestsScreenProps) {
  return (
    <SurfacePanel>
      <Text style={styles.title}>Ride requests</Text>
      {requests.length === 0 ? <Text style={styles.muted}>No requests</Text> : null}
      {requests.map((request) => (
        <View key={request.rideId} style={styles.request}>
          <Text style={styles.route}>
            {request.pickupText} to {request.dropoffText}
          </Text>
          <Text style={styles.muted}>Ride: {request.rideId}</Text>
          {request.riderName ? (
            <Text style={styles.muted}>Rider: {request.riderName}</Text>
          ) : null}
          {request.quotedTotalText ? (
            <Text style={styles.total}>{request.quotedTotalText}</Text>
          ) : null}
          <View style={styles.actions}>
            <PrimaryButton
              label="Accept"
              onPress={() => onAccept(request.rideId)}
              disabled={loading}
              style={styles.actionButton}
            />
            <PrimaryButton
              label="Reject"
              onPress={() => onReject(request.rideId)}
              disabled={loading}
              tone="danger"
              style={styles.actionButton}
            />
          </View>
        </View>
      ))}
    </SurfacePanel>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    flex: 1,
  },
  actions: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  muted: {
    color: colors.muted,
    fontSize: 14,
  },
  request: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    gap: spacing.sm,
    paddingTop: spacing.md,
  },
  route: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "800",
  },
  title: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "900",
  },
  total: {
    color: colors.secondary,
    fontSize: 16,
    fontWeight: "800",
  },
});
