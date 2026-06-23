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
import { WaitingForDriverScreen } from "./ui/screens/WaitingForDriverScreen";
import { TEST_MODE } from "./core/config/environment";
import { colors } from "./ui/theme/colors";
import { spacing } from "./ui/theme/spacing";
import { useRideFlow } from "./state/providers/useRideFlow";
import { ProductTabs } from "./ui/widgets/ProductTabs";

const RIDER_ID = "rider-demo-001";
type RiderTab = "book" | "track" | "history" | "profile" | "alerts";

const riderTabs: Array<{ key: RiderTab; label: string }> = [
  { key: "book", label: "Book" },
  { key: "track", label: "Track" },
  { key: "history", label: "History" },
  { key: "profile", label: "Profile" },
  { key: "alerts", label: "Alerts" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<RiderTab>("book");
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState("rider@novaride.test");
  const [password, setPassword] = useState("pilot");
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
    setActiveTab("track");
  }

  const history = requestedRide
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
            (statusSnapshot ? "PASSED" as const : undefined),
        },
      ]
    : [];
  const riderTrustScore =
    evidence?.receipt.trustScore || statusSnapshot?.trustScore || requestedRide?.trustScore || 92;
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
    statusSnapshot
      ? {
          id: "driver-assigned",
          title: "Driver assigned",
          detail: "Driver, route, and trust checks are visible in tracking.",
          tone: "success" as const,
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
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <Text style={styles.title}>AfriRide Rider</Text>
            <Text style={styles.modePill}>{TEST_MODE ? "Pilot" : "Live"}</Text>
          </View>
          <Text style={styles.subtitle}>Simple booking with visible verification.</Text>
        </View>

        {!authenticated ? (
          <RiderLoginScreen
            email={email}
            password={password}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onContinue={() => setAuthenticated(true)}
          />
        ) : (
          <>
            <ProductTabs
              tabs={riderTabs}
              activeTab={activeTab}
              onChange={setActiveTab}
            />
            {activeTab === "book" ? (
              <>
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
              </>
            ) : null}
            {activeTab === "track" ? (
              <>
                {statusSnapshot ? <DriverAssignedScreen status={statusSnapshot} /> : null}
                {statusSnapshot ? <LiveTrackingScreen status={statusSnapshot} /> : null}
                {requestedRide ? (
                  <RiderTrustPanelScreen
                    status={statusSnapshot}
                    receipt={evidence?.receipt || null}
                  />
                ) : null}
                <EvidenceScreen
                  receipt={evidence?.receipt || null}
                  replay={evidence?.replay || null}
                  ledgerReceipt={evidence?.ledgerReceipt || null}
                />
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
              </>
            ) : null}
            {activeTab === "history" ? <RideHistoryScreen history={history} /> : null}
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
            {activeTab === "alerts" ? (
              <RiderNotificationsScreen notifications={notifications} />
            ) : null}
          </>
        )}
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
