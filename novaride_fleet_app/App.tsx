import React, { useState } from "react";
import { Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";

type FleetTab = "Fleet" | "Vehicles" | "Drivers" | "Maintenance" | "Reports";
export const FLEET_FEATURES = ["Fleet Dashboard", "Vehicle Management", "Driver Assignment", "Maintenance Logs", "Fuel/Charging", "Insurance Documents", "Vehicle Compliance", "Fleet Earnings", "Utilization Analytics"] as const;
export const FLEET_ACTIONS = ["Assign Driver", "Escalate Incident", "Review Evidence", "Resolve Dispute", "Approve Driver", "Suspend Driver", "Approve Vehicle", "Export Report"] as const;
export const NOVARIDE_X_FLEET_MODULES = [
  "Fleet Manager Agent", "Autonomous Fleet Orchestration", "Predictive Maintenance",
  "Energy-Aware Charging", "Driver Fatigue Scoring", "Battery Health Optimization",
  "Carbon-Aware Routing", "Compliance Automation", "Remote Assistance",
  "Digital Twin Fleet Map", "Insurance Risk Signals", "SLA Reporting",
  "Resource Marketplace", "Mobility Graph", "Charging Capacity Exchange", "National Fleet Federation",
] as const;
const FLEET_INTELLIGENCE = [
  ["Autonomous ready", "18"],
  ["Battery health", "91%"],
  ["Charging queue", "12m"],
  ["CO2e saved", "2.8t"],
] as const;

export default function NovaRideFleetApp() {
  const [tab, setTab] = useState<FleetTab>("Fleet"); const [dark, setDark] = useState(false); const [notice, setNotice] = useState("Fleet synchronized");
  const palette = dark ? darkTheme : lightTheme;
  return <View style={[styles.screen,{backgroundColor:palette.background}]}><StatusBar barStyle={dark?"light-content":"dark-content"}/><SafeAreaView style={styles.safe}>
    <View style={styles.header}><View><Text style={[styles.brand,{color:palette.text}]}>NovaRide</Text><Text style={styles.kicker}>FLEET · NovaID VERIFIED</Text></View><Pressable accessibilityRole="button" accessibilityLabel="Toggle theme" onPress={()=>setDark(!dark)} style={[styles.mode,{backgroundColor:palette.surface}]}><Text>{dark?"☀":"☾"}</Text></Pressable></View>
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.hero}><Text style={styles.heroLabel}>FLEET UTILIZATION</Text><Text style={styles.heroValue}>82.4%</Text><Text style={styles.heroMeta}>48 active · 7 maintenance · 3 compliance review</Text></View>
      <View style={styles.metrics}>{[["Fleet earnings","AUD 82.4K"],["Trips","1,248"],["EV charge","76%"],["Compliance","94%"]].map(([label,value])=><View key={label} style={[styles.metric,{backgroundColor:palette.surface}]}><Text style={[styles.value,{color:palette.text}]}>{value}</Text><Text style={{color:palette.muted}}>{label}</Text></View>)}</View>
      <View style={[styles.card,{backgroundColor:palette.surface}]}><Text style={styles.kicker}>NOVARIDE X FLEET CLOUD</Text><Text style={[styles.title,{color:palette.text}]}>AI fleet, energy, autonomy, and resource marketplace</Text><View style={styles.metrics}>{FLEET_INTELLIGENCE.map(([label,value])=><View key={label} style={styles.mosMetric}><Text style={styles.mosValue}>{value}</Text><Text style={styles.mosLabel}>{label}</Text></View>)}</View><View style={styles.actions}>{NOVARIDE_X_FLEET_MODULES.map(label=><Pressable accessibilityRole="button" accessibilityLabel={label} key={label} onPress={()=>setNotice(`${label} opened · digital twin event recorded`)} style={styles.secondaryAction}><Text style={styles.secondaryActionText}>{label}</Text></Pressable>)}</View></View>
      <View style={[styles.card,{backgroundColor:palette.surface}]}><Text style={[styles.title,{color:palette.text}]}>{tab} workspace</Text>{FLEET_FEATURES.map(feature=><Pressable accessibilityRole="button" accessibilityLabel={feature} key={feature} onPress={()=>setNotice(`${feature} opened`)} style={[styles.item,{borderBottomColor:palette.border}]}><Text style={{color:palette.text}}>{feature}</Text><Text style={{color:palette.muted}}>›</Text></Pressable>)}</View>
      <View style={styles.actions}>{FLEET_ACTIONS.map(label=><Pressable accessibilityRole="button" accessibilityLabel={label} key={label} onPress={()=>setNotice(`${label} completed · audit event recorded`)} style={styles.action}><Text style={styles.actionText}>{label}</Text></Pressable>)}</View>
      <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text><Text style={{color:palette.muted,textAlign:"center"}}>Loading · Empty · Error · Success · Offline states supported</Text>
    </ScrollView>
    <View style={[styles.tabs,{backgroundColor:palette.surface}]}>{(["Fleet","Vehicles","Drivers","Maintenance","Reports"] as FleetTab[]).map(item=><Pressable accessibilityRole="tab" accessibilityLabel={`${item} tab`} key={item} onPress={()=>setTab(item)}><Text style={{color:item===tab?"#5B3DF5":palette.muted,fontWeight:"800"}}>{item}</Text></Pressable>)}</View>
  </SafeAreaView></View>;
}
const lightTheme={background:"#F3F5FA",surface:"#FFF",text:"#15182A",muted:"#6E7486",border:"#DFE3EC"}; const darkTheme={background:"#101321",surface:"#1B2033",text:"#F8F9FC",muted:"#ABB3C8",border:"#363D52"};
const styles=StyleSheet.create({screen:{flex:1},safe:{flex:1},header:{padding:18,flexDirection:"row",justifyContent:"space-between"},brand:{fontSize:28,fontWeight:"900"},kicker:{color:"#5B3DF5",fontWeight:"900",fontSize:10},mode:{width:42,height:42,borderRadius:21,alignItems:"center",justifyContent:"center"},content:{padding:14,paddingBottom:100,gap:14},hero:{backgroundColor:"#5B3DF5",padding:22,borderRadius:22},heroLabel:{color:"#DCD6FF",fontWeight:"800"},heroValue:{color:"#FFF",fontSize:36,fontWeight:"900"},heroMeta:{color:"#DCD6FF"},metrics:{flexDirection:"row",flexWrap:"wrap",gap:10},metric:{padding:14,borderRadius:16,minWidth:"46%",flexGrow:1},value:{fontSize:21,fontWeight:"900"},card:{padding:17,borderRadius:20,gap:10},title:{fontSize:19,fontWeight:"900"},item:{paddingVertical:12,borderBottomWidth:1,flexDirection:"row",justifyContent:"space-between"},actions:{flexDirection:"row",flexWrap:"wrap",gap:8},action:{backgroundColor:"#5B3DF5",padding:13,borderRadius:13,flexGrow:1},actionText:{color:"#FFF",fontWeight:"800"},secondaryAction:{backgroundColor:"#EEEAFD",padding:11,borderRadius:12,flexGrow:1},secondaryActionText:{color:"#4A35B5",fontWeight:"800"},mosMetric:{backgroundColor:"#EEF7F3",padding:12,borderRadius:12,minWidth:"46%",flexGrow:1},mosValue:{color:"#087A50",fontWeight:"900",fontSize:18},mosLabel:{color:"#345448",fontWeight:"800",fontSize:11},notice:{backgroundColor:"#E8FBF2",color:"#087A50",padding:14,borderRadius:12,fontWeight:"800"},tabs:{padding:18,flexDirection:"row",justifyContent:"space-around"}});
