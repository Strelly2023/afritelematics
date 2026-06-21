import React, { useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { BookingScreen } from "./ui/screens/BookingScreen";
import { DriverAssignedScreen } from "./ui/screens/DriverAssignedScreen";
import { LiveTrackingScreen } from "./ui/screens/LiveTrackingScreen";
import { PriceExplanationScreen } from "./ui/screens/PriceExplanationScreen";
import { ReceiptScreen } from "./ui/screens/ReceiptScreen";
import { ReplayScreen } from "./ui/screens/ReplayScreen";
import { RideConfirmationScreen } from "./ui/screens/RideConfirmationScreen";
import { RideHistoryScreen } from "./ui/screens/RideHistoryScreen";
import { RiderTrustPanelScreen } from "./ui/screens/RiderTrustPanelScreen";
import { WaitingForDriverScreen } from "./ui/screens/WaitingForDriverScreen";
import { TEST_MODE } from "./core/config/environment";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";
import { useRideFlow } from "./state/providers/useRideFlow";

const RIDER_ID = "rider-demo-001";

export default function App() {
  const [pickup, setPickup] = useState("Kampala Road");
  const [dropoff, setDropoff] = useState("Nakasero");
  const {
    error,
    evidence,
    loading,
    requestedRide,
    statusSnapshot,
    submitRideRequest,
  } = useRideFlow();

  function handleRequestRide() {
    submitRideRequest({
      riderId: RIDER_ID,
      pickup,
      dropoff,
    });
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <Text style={styles.title}>AfriRide Rider</Text>
            <Text style={styles.modePill}>{TEST_MODE ? "Pilot" : "Live"}</Text>
          </View>
          <Text style={styles.subtitle}>Simple booking with visible verification.</Text>
        </View>

        <BookingScreen
          pickup={pickup}
          dropoff={dropoff}
          loading={loading}
          error={error}
          onPickupChange={setPickup}
          onDropoffChange={setDropoff}
          onRequestRide={handleRequestRide}
        />

        {requestedRide ? <RideConfirmationScreen ride={requestedRide} /> : null}
        {requestedRide && !statusSnapshot ? <WaitingForDriverScreen /> : null}
        {statusSnapshot ? <DriverAssignedScreen status={statusSnapshot} /> : null}
        {statusSnapshot ? <LiveTrackingScreen status={statusSnapshot} /> : null}
        {requestedRide ? (
          <RiderTrustPanelScreen
            status={statusSnapshot}
            receipt={evidence?.receipt || null}
          />
        ) : null}

        {evidence ? (
          <>
            <ReceiptScreen
              receipt={evidence.receipt}
              ledgerReceipt={evidence.ledgerReceipt}
            />
            <ReplayScreen replay={evidence.replay} />
            <PriceExplanationScreen explanation={evidence.priceExplanation} />
          </>
        ) : null}

        <RideHistoryScreen
          history={
            requestedRide
              ? [
                  {
                    rideId: requestedRide.rideId,
                    status: evidence?.receipt.status || statusSnapshot?.status || requestedRide.status,
                    trustScore:
                      evidence?.receipt.trustScore ||
                      statusSnapshot?.trustScore ||
                      requestedRide.trustScore,
                    verificationStatus:
                      evidence?.receipt.verificationStatus ||
                      (statusSnapshot ? "PASSED" : undefined),
                  },
                ]
              : []
          }
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: spacing.lg,
    padding: spacing.lg,
  },
  header: {
    gap: spacing.xs,
    paddingTop: spacing.md,
  },
  headerTop: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    justifyContent: "space-between",
  },
  modePill: {
    backgroundColor: "#e8f6ef",
    borderColor: "#b7e3cc",
    borderRadius: 8,
    borderWidth: 1,
    color: colors.success,
    fontSize: 12,
    fontWeight: "900",
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    textTransform: "uppercase",
  },
  screen: {
    backgroundColor: colors.background,
    flex: 1,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 15,
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: "900",
  },
});
