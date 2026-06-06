import React, { useEffect } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useDriverFlow } from "./state/providers/useDriverFlow";
import { usePilotEvidence } from "./state/providers/usePilotEvidence";
import { AvailabilityScreen } from "./ui/screens/AvailabilityScreen";
import { DiagnosticsScreen } from "./ui/screens/DiagnosticsScreen";
import { EarningsScreen } from "./ui/screens/EarningsScreen";
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
  if (!TEST_MODE) {
    throw new Error("Test mode required");
  }

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
          <Text style={styles.title}>AfriRide Driver</Text>
          <Text style={styles.subtitle}>Execution state, projected clearly.</Text>
        </View>

        {error ? <Text style={styles.error}>{error}</Text> : null}

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
