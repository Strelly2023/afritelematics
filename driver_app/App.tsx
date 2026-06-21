import React, { useEffect } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useDriverFlow } from "./state/providers/useDriverFlow";
import { useOperatorDashboard } from "./state/providers/useOperatorDashboard";
import { usePilotEvidence } from "./state/providers/usePilotEvidence";
import { AvailabilityScreen } from "./ui/screens/AvailabilityScreen";
import { DiagnosticsScreen } from "./ui/screens/DiagnosticsScreen";
import { DriverTrustProfileScreen } from "./ui/screens/DriverTrustProfileScreen";
import { EarningsScreen } from "./ui/screens/EarningsScreen";
import { OperatorDashboardScreen } from "./ui/screens/OperatorDashboardScreen";
import { ReplayHistoryScreen } from "./ui/screens/ReplayHistoryScreen";
import { RideRequestsScreen } from "./ui/screens/RideRequestsScreen";
import { TripLifecycleScreen } from "./ui/screens/TripLifecycleScreen";
import { TEST_MODE } from "./core/config/environment";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";

const DRIVER_ID = "driver-demo-001";

type ErrorUtilsLike = {
  getGlobalHandler?: () => (error: Error, isFatal?: boolean) => void;
  setGlobalHandler?: (
    handler: (error: Error, isFatal?: boolean) => void,
  ) => void;
};

export default function App() {
  const {
    acceptRequest,
    availability,
    completeTrip,
    earnings,
    error,
    loading,
    markArrived,
    rejectRequest,
    replayHistory,
    requests,
    startTrip,
    trip,
    updateAvailability,
  } = useDriverFlow(DRIVER_ID);
  const operator = useOperatorDashboard();
  const { capture, diagnostics, startShift } = usePilotEvidence(DRIVER_ID);

  useEffect(() => {
    const errorUtils = (globalThis as { ErrorUtils?: ErrorUtilsLike }).ErrorUtils;
    const previousHandler = errorUtils?.getGlobalHandler?.();

    errorUtils?.setGlobalHandler?.((error: Error, isFatal?: boolean) => {
      void capture("crash_event", {
        message: error.message,
        stack: error.stack || null,
        is_fatal: Boolean(isFatal),
      });
      previousHandler?.(error, isFatal);
    });

    return () => {
      if (previousHandler) {
        errorUtils?.setGlobalHandler?.(previousHandler);
      }
    };
  }, [capture]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <Text style={styles.title}>AfriRide Driver</Text>
            <Text style={styles.modePill}>{TEST_MODE ? "Pilot" : "Live"}</Text>
          </View>
          <Text style={styles.subtitle}>Trip execution with visible trust evidence.</Text>
        </View>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <OperatorDashboardScreen
          dashboard={operator.dashboard}
          loading={operator.loading}
          error={operator.error}
          onRefresh={operator.refreshDashboard}
        />

        <DiagnosticsScreen
          diagnostics={diagnostics}
          loading={loading}
          onStartShift={startShift}
        />

        <AvailabilityScreen
          availability={availability}
          loading={loading}
          onGoAvailable={() => updateAvailability("available")}
          onGoOffline={() => updateAvailability("offline")}
        />

        <DriverTrustProfileScreen
          availability={availability}
          earnings={earnings}
        />

        <RideRequestsScreen
          requests={requests}
          loading={loading}
          onAccept={acceptRequest}
          onReject={rejectRequest}
        />

        <TripLifecycleScreen
          trip={trip}
          loading={loading}
          onArrived={markArrived}
          onStart={startTrip}
          onComplete={completeTrip}
        />

        <EarningsScreen earnings={earnings} />
        <ReplayHistoryScreen replayHistory={replayHistory} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: spacing.lg,
    padding: spacing.lg,
  },
  error: {
    color: colors.danger,
    fontWeight: "800",
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
