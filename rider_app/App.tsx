import React, { useEffect, useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { DriverAssignedScreen } from "./ui/screens/DriverAssignedScreen";
import { EvidenceScreen } from "./ui/screens/EvidenceScreen";
import { LiveTrackingScreen } from "./ui/screens/LiveTrackingScreen";
import { PriceExplanationScreen } from "./ui/screens/PriceExplanationScreen";
import { ReceiptScreen } from "./ui/screens/ReceiptScreen";
import { ReplayScreen } from "./ui/screens/ReplayScreen";
import { RideConfirmationScreen } from "./ui/screens/RideConfirmationScreen";
import { RideHistoryScreen } from "./ui/screens/RideHistoryScreen";
import { RiderLoginScreen } from "./ui/screens/RiderLoginScreen";
import { RiderNotificationsScreen } from "./ui/screens/RiderNotificationsScreen";
import { RiderProfileScreen } from "./ui/screens/RiderProfileScreen";
import { RiderTrustPanelScreen } from "./ui/screens/RiderTrustPanelScreen";
import { RiderHomeScreen } from "./ui/screens/RiderHomeScreen";
import { WalletScreen } from "./ui/screens/WalletScreen";
import { ActivityScreen } from "./ui/screens/ActivityScreen";
import { WaitingForDriverScreen } from "./ui/screens/WaitingForDriverScreen";
import {
  APP_LOCALE,
  ORGANIZATION_ID,
  REGION_ID,
  TEST_MODE,
} from "./core/config/environment";
import { loginPilot } from "./core/api/auth.service";
import { apiRequest } from "./core/api/client";
import {
  clearSession,
  requireBiometricUnlock,
  restoreSession,
} from "./core/api/session";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";
import { useRideFlow } from "./state/providers/useRideFlow";
import { ProductTabs } from "./ui/widgets/ProductTabs";
import { BottomTabs } from "./ui/widgets/BottomTabs";
import { InteractiveRideMap } from "./ui/widgets/InteractiveRideMap";
import { useRiderMobility } from "./state/providers/useRiderMobility";
import {
  AdaptiveScaffold,
  AnimatedEntrance,
  SkeletonBlock,
  SyncBanner,
} from "../afriride_system/mobile/shared/mobileExcellence";
import { useGlobalRuntime } from "../afriride_system/mobile/shared/globalRuntime";

const RIDER_ID = "rider-demo-001";
type RiderTab = "home" | "trips" | "wallet" | "activity" | "profile";

const riderTabs: Array<{ key: RiderTab; label: string }> = [
  { key: "home", label: "Home" },
  { key: "trips", label: "Trips" },
  { key: "wallet", label: "Wallet" },
  { key: "activity", label: "Activity" },
  { key: "profile", label: "Profile" },
];

export default function App() {
  return (
    <RiderErrorBoundary>
      <RiderApp />
    </RiderErrorBoundary>
  );
}

function RiderApp() {
  const [activeTab, setActiveTab] = useState<RiderTab>("home");
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState("rider@novaride.test");
  const [password, setPassword] = useState("pilot");
  const [authenticating, setAuthenticating] = useState(false);
  const [loginError, setLoginError] = useState("");
  const globalRuntime = useGlobalRuntime(
    apiRequest,
    ORGANIZATION_ID,
    REGION_ID,
    APP_LOCALE || undefined,
  );
  const localizedRiderTabs: Array<{ key: RiderTab; label: string }> = [
    { key: "home", label: globalRuntime.t("nav.home") },
    { key: "trips", label: globalRuntime.t("nav.trips") },
    { key: "wallet", label: globalRuntime.t("nav.wallet") },
    { key: "activity", label: globalRuntime.t("nav.activity") },
    { key: "profile", label: globalRuntime.t("nav.profile") },
  ];
  const mobility = useRiderMobility(RIDER_ID, authenticated);
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
  const receipt = evidence?.receipt ?? null;
  const replay = evidence?.replay ?? null;
  const ledgerReceipt = evidence?.ledgerReceipt ?? null;
  const priceExplanation = evidence?.priceExplanation ?? null;

  useEffect(() => {
    let active = true;
    void (async () => {
      const restored = await restoreSession();
      if (!restored.token || !active) return;
      const unlock = TEST_MODE
        ? { success: true }
        : await requireBiometricUnlock("Unlock AfriRide Rider");
      if (active && unlock.success) setAuthenticated(true);
      else if (!unlock.success) await clearSession();
    })();
    return () => {
      active = false;
    };
  }, []);

  function handleRequestRide() {
    submitRideRequest({
      riderId: RIDER_ID,
      pickup,
      dropoff,
    });
    setActiveTab("trips");
  }

  const history = requestedRide
    ? [
        {
          rideId: requestedRide.rideId,
          status: receipt?.status || statusSnapshot?.status || requestedRide.status,
          trustScore:
            receipt?.trustScore ||
            statusSnapshot?.trustScore ||
            requestedRide.trustScore,
          verificationStatus:
            receipt?.verificationStatus ||
            (statusSnapshot ? "PASSED" as const : undefined),
        },
      ]
    : [];
  const riderTrustScore =
    receipt?.trustScore || statusSnapshot?.trustScore || requestedRide?.trustScore || 92;
  const hasAssignedDriver = Boolean(
    statusSnapshot?.driverName ||
      statusSnapshot?.status === "driver_assigned" ||
      statusSnapshot?.status === "matched" ||
      statusSnapshot?.status === "arriving" ||
      statusSnapshot?.status === "arrived" ||
      statusSnapshot?.status === "in_progress" ||
      statusSnapshot?.status === "completed",
  );
  const notifications = [
    {
      id: "rider-login",
      title: "Account ready",
      detail: authenticated ? "Rider profile is active for pilot testing." : "Login required.",
      tone: "info" as const,
    },
    requestedRide
      ? {
          id: "ride-requested",
          title: "Ride requested",
          detail: "Your ride is in the verified lifecycle.",
          tone: "success" as const,
        }
      : null,
    hasAssignedDriver && statusSnapshot
      ? {
          id: "driver-assigned",
          title: "Driver assigned",
          detail: `${statusSnapshot.driverName || "Driver"} is on the live route with ETA ${statusSnapshot.etaText || "pending"}.`,
          tone: "success" as const,
        }
      : null,
    statusSnapshot?.locationText
      ? {
          id: "live-location",
          title: "Live tracking active",
          detail: statusSnapshot.locationText,
          tone: "info" as const,
        }
      : null,
    evidence
      ? {
          id: "trust-verified",
          title: "Trust verified",
          detail: "Receipt, replay, and payment checks are available.",
          tone: "success" as const,
        }
      : null,
  ].filter((item): item is { id: string; title: string; detail: string; tone: "success" | "info" } =>
    Boolean(item),
  );

  return (
    <SafeAreaView style={styles.screen}>
      <AdaptiveScaffold
        testID="rider-adaptive-scaffold"
        brandColor={globalRuntime.brand.primary_color}
        navigation={
          authenticated ? (
            <View style={styles.bottomNav}>
              <BottomTabs tabs={localizedRiderTabs} activeTab={activeTab} onChange={setActiveTab} />
            </View>
          ) : undefined
        }
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <View style={styles.headerTop}>
              <Text style={styles.title}>
                {globalRuntime.brand.name} {globalRuntime.t("app.rider")}
              </Text>
              <Text style={styles.modePill}>
                {globalRuntime.t(TEST_MODE ? "mode.pilot" : "mode.live")}
              </Text>
            </View>
            <Text style={styles.subtitle}>Simple booking, live tracking, and verified receipts.</Text>
            <Text style={styles.orgLabel}>
              {globalRuntime.region.region_id} · {globalRuntime.region.currency} · {globalRuntime.locale}
            </Text>
          </View>
          <SyncBanner
            online={mobility.health?.networkConnected !== false}
            pending={mobility.health?.pendingSync || 0}
          />

          {loginError ? <Text style={styles.error}>{loginError}</Text> : null}
          {authenticating ? <SkeletonBlock height={132} /> : null}

          {!authenticated ? (
            <RiderLoginScreen
              email={email}
              password={password}
              onEmailChange={setEmail}
              onPasswordChange={setPassword}
              loading={authenticating}
              onContinue={async () => {
                setAuthenticating(true);
                setLoginError("");
                try {
                  await loginPilot("rider-demo-001", "CUSTOMER", ORGANIZATION_ID);
                  setAuthenticated(true);
                } catch (error) {
                  if (TEST_MODE) {
                    setAuthenticated(true);
                  } else {
                    setLoginError(
                      error instanceof Error ? error.message : "login_failed",
                    );
                  }
                } finally {
                  setAuthenticating(false);
                }
              }}
            />
          ) : (
            <AnimatedEntrance>
              {activeTab === "home" ? (
                <>
                  <InteractiveRideMap
                    rider={mobility.location}
                    driver={
                      statusSnapshot?.driverLatitude != null &&
                      statusSnapshot?.driverLongitude != null
                        ? {
                            latitude: statusSnapshot.driverLatitude,
                            longitude: statusSnapshot.driverLongitude,
                          }
                        : null
                    }
                  />
                  <RiderHomeScreen
                    pickup={pickup}
                    dropoff={dropoff}
                    loading={loading}
                    onPickupChange={setPickup}
                    onDropoffChange={setDropoff}
                    onRequestRide={handleRequestRide}
                  />
                  {requestedRide && !hasAssignedDriver ? <RideConfirmationScreen ride={requestedRide} /> : null}
                  {requestedRide && !hasAssignedDriver ? <WaitingForDriverScreen /> : null}
                </>
              ) : null}
              {activeTab === "trips" ? (
                <>
                  {requestedRide && !hasAssignedDriver ? <RideConfirmationScreen ride={requestedRide} /> : null}
                  {requestedRide && !hasAssignedDriver ? <WaitingForDriverScreen /> : null}
                  {statusSnapshot && hasAssignedDriver ? <DriverAssignedScreen status={statusSnapshot} /> : null}
                  {statusSnapshot && hasAssignedDriver ? <LiveTrackingScreen status={statusSnapshot} /> : null}
                  {requestedRide ? (
                    <RiderTrustPanelScreen
                      status={statusSnapshot}
                      receipt={receipt}
                    />
                  ) : null}
                  <EvidenceScreen
                    receipt={receipt}
                    replay={replay}
                    ledgerReceipt={ledgerReceipt}
                  />
                  {evidence ? (
                    <>
                      <ReceiptScreen
                        receipt={receipt}
                        ledgerReceipt={ledgerReceipt}
                      />
                      <ReplayScreen replay={replay} />
                      <PriceExplanationScreen explanation={priceExplanation} />
                    </>
                  ) : null}
                </>
              ) : null}
              {activeTab === "wallet" ? <WalletScreen /> : null}
              {activeTab === "activity" ? (
                <ActivityScreen history={history} notifications={notifications} />
              ) : null}
              {activeTab === "profile" ? (
                <RiderProfileScreen
                  name="Pilot Rider"
                  email={email}
                  trips={history.length}
                  verifiedTrips={evidence ? history.length : 0}
                  replaySuccessPct={evidence ? 100 : 0}
                  trustScore={riderTrustScore}
                />
              ) : null}
            </AnimatedEntrance>
          )}
        </ScrollView>
      </AdaptiveScaffold>
    </SafeAreaView>
  );
}

type RiderErrorBoundaryState = {
  hasError: boolean;
};

class RiderErrorBoundary extends React.Component<React.PropsWithChildren, RiderErrorBoundaryState> {
  state: RiderErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): RiderErrorBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <SafeAreaView style={styles.screen}>
          <View style={styles.shell}>
            <ScrollView contentContainerStyle={styles.content}>
              <View style={styles.header}>
                <Text style={styles.title}>AfriRide Rider</Text>
                <Text style={styles.subtitle}>The rider view hit a sync issue. Reload the app to continue.</Text>
              </View>
            </ScrollView>
          </View>
        </SafeAreaView>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  content: {
    gap: spacing.lg,
    padding: spacing.lg,
    paddingBottom: spacing.xl,
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
  orgLabel: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  bottomNav: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    padding: spacing.md,
  },
  shell: {
    flex: 1,
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
