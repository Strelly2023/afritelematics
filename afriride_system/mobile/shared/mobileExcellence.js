import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  AccessibilityInfo,
  Animated,
  Appearance,
  Platform,
  PlatformColor,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from "react-native";

export function useMobileExcellence() {
  const { width, height, fontScale } = useWindowDimensions();
  const [scheme, setScheme] = useState(Appearance.getColorScheme());
  const [reduceMotion, setReduceMotion] = useState(false);
  useEffect(() => {
    const appearance = Appearance.addChangeListener(({ colorScheme }) => setScheme(colorScheme));
    void AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
    const motion = AccessibilityInfo.addEventListener("reduceMotionChanged", setReduceMotion);
    return () => {
      appearance.remove();
      motion.remove();
    };
  }, []);
  const adaptiveClass = width >= 840 ? "expanded" : width >= 600 ? "medium" : "compact";
  const isFoldablePosture = width >= 600 && width / Math.max(1, height) > 1.15;
  const theme = useMemo(() => materialTheme(scheme === "dark"), [scheme]);
  return { width, height, fontScale, reduceMotion, adaptiveClass, isFoldablePosture, theme };
}

function materialTheme(dark) {
  const dynamicPrimary =
    Platform.OS === "android" && Number(Platform.Version) >= 31
      ? PlatformColor("@android:color/system_accent1_600")
      : dark ? "#70D7BC" : "#006B57";
  return {
    dark,
    primary: dynamicPrimary,
    background: dark ? "#101412" : "#F7FAF8",
    surface: dark ? "#191C1A" : "#FFFFFF",
    onSurface: dark ? "#E1E3DF" : "#191C1A",
    outline: dark ? "#89938E" : "#6F7974",
  };
}

export function AdaptiveScaffold({ children, navigation, testID, brandColor }) {
  const excellence = useMobileExcellence();
  const dualPane =
    excellence.adaptiveClass === "expanded" || excellence.isFoldablePosture;
  return (
    <View
      testID={testID}
      style={[
        styles.scaffold,
        {
          backgroundColor: excellence.theme.background,
          borderTopColor: brandColor || excellence.theme.primary,
        },
      ]}
      accessibilityRole="none"
    >
      <View style={[styles.frame, dualPane && styles.expandedFrame]}>
        {dualPane && navigation ? <View style={styles.navigationRail}>{navigation}</View> : null}
        <View style={styles.body}>{children}</View>
      </View>
      {!dualPane ? navigation : null}
    </View>
  );
}

export function AnimatedEntrance({ children, style }) {
  const { reduceMotion } = useMobileExcellence();
  const opacity = useRef(new Animated.Value(reduceMotion ? 1 : 0)).current;
  const translate = useRef(new Animated.Value(reduceMotion ? 0 : 8)).current;
  useEffect(() => {
    if (reduceMotion) return undefined;
    const animation = Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 220, useNativeDriver: true }),
      Animated.timing(translate, { toValue: 0, duration: 220, useNativeDriver: true }),
    ]);
    animation.start();
    return () => animation.stop();
  }, [opacity, reduceMotion, translate]);
  return (
    <Animated.View style={[style, { opacity, transform: [{ translateY: translate }] }]}>
      {children}
    </Animated.View>
  );
}

export function SkeletonBlock({ height = 72 }) {
  const { reduceMotion, theme } = useMobileExcellence();
  const opacity = useRef(new Animated.Value(0.45)).current;
  useEffect(() => {
    if (reduceMotion) return undefined;
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 0.85, duration: 700, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.45, duration: 700, useNativeDriver: true }),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [opacity, reduceMotion]);
  return (
    <Animated.View
      accessible
      accessibilityLabel="Loading content"
      accessibilityRole="progressbar"
      style={[styles.skeleton, { height, opacity, backgroundColor: theme.outline }]}
    />
  );
}

export function SyncBanner({ online, pending }) {
  if (online && pending === 0) return null;
  return (
    <View
      style={styles.banner}
      accessible
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
    >
      <Text style={styles.bannerText}>
        {online ? `Syncing ${pending} saved change${pending === 1 ? "" : "s"}` : "Offline · changes are saved on this device"}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  scaffold: { borderTopWidth: 4, flex: 1 },
  frame: { alignSelf: "center", flex: 1, width: "100%" },
  expandedFrame: { flexDirection: "row", maxWidth: 1440 },
  navigationRail: { borderRightColor: "#CCD6D1", borderRightWidth: 1, padding: 12, width: 220 },
  body: { flex: 1, minWidth: 0 },
  skeleton: { borderRadius: 16, width: "100%" },
  banner: { backgroundColor: "#F5E6C8", paddingHorizontal: 16, paddingVertical: 10 },
  bannerText: { color: "#4A3513", fontSize: 14, fontWeight: "700", textAlign: "center" },
});
