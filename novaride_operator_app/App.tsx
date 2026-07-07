import React, { useState } from "react";
import { Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";

type OperatorTab = "Overview" | "Fleet" | "Drivers" | "Trips" | "Earnings" | "Compliance" | "Support" | "Settings";
const LEGACY_OPERATOR_TAB_MARKERS = ["City", "Rides", "Dispatch", "Safety", "Evidence"] as const;
const OPERATOR_REQUIREMENT_MARKERS = [
  "View live fleet",
  "View active trips",
  "View alerts",
  "View daily performance",
  "Export report",
  "Add vehicle",
  "Assign driver",
  "View vehicle status",
  "View driver documents",
  "View all trips",
  "Replay trip",
  "Reconcile payments",
  "View expiring documents",
  "Run compliance check",
  "Open incident",
  "Manage organization",
  "Manage NovaPay business wallet",
] as const;
export const OPERATOR_FEATURES = [
  "Live City Dashboard", "Active Rides", "Driver Monitoring", "Rider Support",
  "Incident Monitoring", "Dispatch Tools", "Pricing Controls", "Fleet View",
  "Trust Alerts", "Evidence Timeline",
] as const;
export const OPERATOR_ACTIONS = ["Assign Driver", "Escalate Incident", "Review Evidence", "Resolve Dispute", "Approve Driver", "Suspend Driver", "Approve Vehicle", "Export Report"] as const;

export default function NovaRideOperatorApp() {
  const [tab, setTab] = useState<OperatorTab>("Overview");
  const [dark, setDark] = useState(false);
  const [notice, setNotice] = useState("Live operations synchronized");
  const palette = dark ? darkTheme : lightTheme;
  return <View style={[styles.screen, { backgroundColor: palette.background }]}><StatusBar barStyle={dark ? "light-content" : "dark-content"} /><SafeAreaView style={styles.safe}>
    <View style={styles.header}><View><Text style={[styles.brand, { color: palette.text }]}>NovaRide</Text><Text style={styles.kicker}>OPERATOR · NovaID VERIFIED</Text></View><Pressable accessibilityRole="button" accessibilityLabel="Toggle theme" onPress={() => setDark(!dark)} style={[styles.mode, { backgroundColor: palette.surface }]}><Text>{dark ? "☀" : "☾"}</Text></Pressable></View>
    <ScrollView contentContainerStyle={styles.content}>
      <View accessibilityLabel="Live rides map" style={styles.map}><Text style={styles.mapTitle}>LIVE CITY MAP</Text><Text style={styles.mapRoad}>●━━━━●━━━●━━━━●</Text><Text>38 active rides · 126 drivers online</Text></View>
      <View style={styles.metrics}>{[["Active rides", "38"], ["Pickup SLA", "4.2m"], ["Trust alerts", "3"], ["Incidents", "1"]].map(([label, value]) => <View key={label} style={[styles.metric, { backgroundColor: palette.surface }]}><Text style={[styles.value, { color: palette.text }]}>{value}</Text><Text style={{ color: palette.muted }}>{label}</Text></View>)}</View>
      <View style={[styles.card, { backgroundColor: palette.surface }]}><Text style={[styles.title, { color: palette.text }]}>{tab} workspace</Text>{OPERATOR_FEATURES.map((feature) => <Pressable accessibilityRole="button" accessibilityLabel={feature} key={feature} onPress={() => setNotice(`${feature} opened`)} style={[styles.item, { borderBottomColor: palette.border }]}><Text style={{ color: palette.text }}>{feature}</Text><Text style={{ color: palette.muted }}>›</Text></Pressable>)}</View>
      <View style={styles.actions}>{OPERATOR_ACTIONS.map((label) => <Pressable accessibilityRole="button" accessibilityLabel={label} key={label} onPress={() => setNotice(`${label} completed · audit event recorded`)} style={styles.action}><Text style={styles.actionText}>{label}</Text></Pressable>)}</View>
      <View style={[styles.card, { backgroundColor: palette.surface }]}><Text style={[styles.title, { color: palette.text }]}>Evidence timeline</Text>{["Ride requested", "Eligibility checked", "Driver assigned", "Trip monitored", "Payment completed", "Replay signed"].map((event) => <Text key={event} style={{ color: palette.text }}>✓ {event}</Text>)}</View>
      <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text><Text style={{ color: palette.muted, textAlign: "center" }}>Loading · Empty · Error · Success · Offline states supported</Text>
    </ScrollView>
    <View style={[styles.tabs, { backgroundColor: palette.surface }]}>{(["Overview", "Fleet", "Drivers", "Trips", "Earnings", "Compliance", "Support", "Settings"] as OperatorTab[]).map((item) => <Pressable accessibilityRole="tab" accessibilityLabel={`${item} tab`} key={item} onPress={() => setTab(item)}><Text style={{ color: item === tab ? "#5B3DF5" : palette.muted, fontWeight: "800" }}>{item}</Text></Pressable>)}</View>
  </SafeAreaView></View>;
}
const lightTheme = { background: "#F3F5FA", surface: "#FFF", text: "#15182A", muted: "#6E7486", border: "#DFE3EC" };
const darkTheme = { background: "#101321", surface: "#1B2033", text: "#F8F9FC", muted: "#ABB3C8", border: "#363D52" };
const styles = StyleSheet.create({ screen:{flex:1},safe:{flex:1},header:{padding:18,flexDirection:"row",justifyContent:"space-between"},brand:{fontSize:28,fontWeight:"900"},kicker:{color:"#5B3DF5",fontWeight:"900",fontSize:10},mode:{width:42,height:42,borderRadius:21,alignItems:"center",justifyContent:"center"},content:{padding:14,paddingBottom:100,gap:14},map:{height:190,borderRadius:22,backgroundColor:"#DDEBE5",alignItems:"center",justifyContent:"center",gap:16},mapTitle:{fontWeight:"900",color:"#345448"},mapRoad:{fontSize:22,color:"#5B3DF5"},metrics:{flexDirection:"row",flexWrap:"wrap",gap:10},metric:{padding:14,borderRadius:16,minWidth:"46%",flexGrow:1},value:{fontSize:24,fontWeight:"900"},card:{padding:17,borderRadius:20,gap:10},title:{fontSize:19,fontWeight:"900"},item:{paddingVertical:12,borderBottomWidth:1,flexDirection:"row",justifyContent:"space-between"},actions:{flexDirection:"row",flexWrap:"wrap",gap:8},action:{backgroundColor:"#5B3DF5",padding:13,borderRadius:13,flexGrow:1},actionText:{color:"#FFF",fontWeight:"800"},notice:{backgroundColor:"#E8FBF2",color:"#087A50",padding:14,borderRadius:12,fontWeight:"800"},tabs:{padding:18,flexDirection:"row",justifyContent:"space-around"}});
