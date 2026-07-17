import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Application from "expo-application";
import * as BackgroundFetch from "expo-background-fetch";
import * as Battery from "expo-battery";
import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Location from "expo-location";
import * as Network from "expo-network";
import * as Notifications from "expo-notifications";
import * as TaskManager from "expo-task-manager";
import { Linking, Platform } from "react-native";

import { apiRequest } from "../api/client";

export const DRIVER_LOCATION_TASK = "afriride-driver-location-v1";
export const DRIVER_SYNC_TASK = "afriride-driver-sync-v1";
const QUEUE_KEY = "@afriride/driver/offline-queue/v1";
const ACTIVE_DRIVER_KEY = "@afriride/driver/active-id/v1";
const PUSH_KEY = "@afriride/driver/push-token/v1";

type LocationPayload = {
  driver_id: string;
  lat: number;
  lng: number;
  heading: number | null;
  accuracy_m: number | null;
  speed_mps: number | null;
  timestamp: string;
};

type QueueItem = {
  id: string;
  path: string;
  body: Record<string, unknown>;
  createdAt: string;
  attempts: number;
  nextRetryAt: string;
  operationType: "availability" | "location" | "push" | "trip" | "unknown";
};

export type DriverMobilityHealth = {
  batteryLevel: number | null;
  lowPowerMode: boolean;
  networkConnected: boolean;
  deviceTrusted: boolean;
  backgroundLocation: boolean;
  pushGranted: boolean;
  pendingSync: number;
};

async function readQueue(): Promise<QueueItem[]> {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  if (!raw) return [];
  try {
    const value = JSON.parse(raw);
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

async function storeQueue(queue: QueueItem[]) {
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(-1000)));
}

function classifyOperation(path: string): QueueItem["operationType"] {
  if (path.includes("/availability")) return "availability";
  if (path.includes("/location")) return "location";
  if (path.includes("/push")) return "push";
  if (path.includes("/ride") || path.includes("/trip")) return "trip";
  return "unknown";
}

export async function queueDriverOperation(
  path: string,
  body: Record<string, unknown>,
) {
  const queue = await readQueue();
  const operationType = classifyOperation(path);
  const nextRetryAt = new Date(Date.now() + 30_000).toISOString();
  const nextQueue =
    operationType === "availability"
      ? queue.filter((item) => item.operationType !== "availability" || item.path !== path)
      : queue;
  await storeQueue([
    ...nextQueue,
    {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      path,
      body,
      createdAt: new Date().toISOString(),
      attempts: 0,
      nextRetryAt,
      operationType,
    },
  ]);
}

export async function getPendingDriverQueueCount() {
  return (await readQueue()).length;
}

export async function synchronizeDriverQueue() {
  const [network, queue] = await Promise.all([
    Network.getNetworkStateAsync(),
    readQueue(),
  ]);
  if (!network.isConnected || queue.length === 0) return queue.length;
  const now = Date.now();
  const remaining: QueueItem[] = [];
  for (const item of queue) {
    if (Date.parse(item.nextRetryAt || item.createdAt || "") > now) {
      remaining.push(item);
      continue;
    }
    try {
      await apiRequest(item.path, {
        method: "POST",
        headers: { "Idempotency-Key": item.id },
        body: { ...item.body, offline_created_at: item.createdAt },
      });
    } catch {
      const attempts = item.attempts + 1;
      remaining.push({
        ...item,
        attempts,
        nextRetryAt: new Date(
          Date.now() + Math.min(15 * 60_000, 30_000 * 2 ** Math.min(attempts, 4)),
        ).toISOString(),
      });
    }
  }
  await storeQueue(remaining);
  return remaining.length;
}

async function deliverLocation(location: Location.LocationObject) {
  const driverId = await AsyncStorage.getItem(ACTIVE_DRIVER_KEY);
  if (!driverId) return;
  const body: LocationPayload = {
    driver_id: driverId,
    lat: location.coords.latitude,
    lng: location.coords.longitude,
    heading: location.coords.heading,
    accuracy_m: location.coords.accuracy,
    speed_mps: location.coords.speed,
    timestamp: new Date(location.timestamp).toISOString(),
  };
  try {
    await apiRequest("/v1/drivers/location", { method: "POST", body });
  } catch {
    await queueDriverOperation("/v1/drivers/location", body);
  }
}

TaskManager.defineTask(DRIVER_LOCATION_TASK, async ({ data, error }) => {
  if (error) return;
  const locations = (data as { locations?: Location.LocationObject[] } | undefined)?.locations;
  for (const location of locations || []) await deliverLocation(location);
});

TaskManager.defineTask(DRIVER_SYNC_TASK, async () => {
  const remaining = await synchronizeDriverQueue();
  return remaining === 0
    ? BackgroundFetch.BackgroundFetchResult.NewData
    : BackgroundFetch.BackgroundFetchResult.NoData;
});

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerDriverPush(driverId: string) {
  if (!Device.isDevice) return null;
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("trip-offers", {
      name: "Trip offers",
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 200, 250],
      sound: "default",
    });
  }
  const permission = await Notifications.requestPermissionsAsync();
  if (!permission.granted) return null;
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
  if (token !== (await AsyncStorage.getItem(PUSH_KEY))) {
    await apiRequest("/v1/mobile/devices/push", {
      method: "POST",
      body: { actor_id: driverId, role: "driver", token, platform: Platform.OS },
    });
    await AsyncStorage.setItem(PUSH_KEY, token);
  }
  return token;
}

export async function startDriverBackgroundMobility(driverId: string) {
  const foreground = await Location.requestForegroundPermissionsAsync();
  if (!foreground.granted) throw new Error("foreground_location_denied");
  const background = await Location.requestBackgroundPermissionsAsync();
  if (!background.granted) throw new Error("background_location_denied");
  await AsyncStorage.setItem(ACTIVE_DRIVER_KEY, driverId);
  const lowPowerMode = await Battery.isLowPowerModeEnabledAsync().catch(() => false);
  if (!(await Location.hasStartedLocationUpdatesAsync(DRIVER_LOCATION_TASK))) {
    await Location.startLocationUpdatesAsync(DRIVER_LOCATION_TASK, {
      accuracy: lowPowerMode ? Location.Accuracy.Balanced : Location.Accuracy.High,
      distanceInterval: lowPowerMode ? 40 : 15,
      timeInterval: lowPowerMode ? 30000 : 10000,
      deferredUpdatesDistance: lowPowerMode ? 100 : 50,
      deferredUpdatesInterval: lowPowerMode ? 60000 : 30000,
      pausesUpdatesAutomatically: false,
      activityType: Location.ActivityType.AutomotiveNavigation,
      foregroundService: {
        notificationTitle: "AfriRide shift active",
        notificationBody: "Location is shared for dispatch, navigation and rider safety.",
        notificationColor: "#135f4a",
      },
      showsBackgroundLocationIndicator: true,
    });
  }
  if (!(await TaskManager.isTaskRegisteredAsync(DRIVER_SYNC_TASK))) {
    await BackgroundFetch.registerTaskAsync(DRIVER_SYNC_TASK, {
      minimumInterval: 15 * 60,
      stopOnTerminate: false,
      startOnBoot: true,
    });
  }
}

export async function stopDriverBackgroundMobility() {
  if (await Location.hasStartedLocationUpdatesAsync(DRIVER_LOCATION_TASK)) {
    await Location.stopLocationUpdatesAsync(DRIVER_LOCATION_TASK);
  }
  await AsyncStorage.removeItem(ACTIVE_DRIVER_KEY);
  await synchronizeDriverQueue();
}

export async function clearDriverMobilityState() {
  await stopDriverBackgroundMobility().catch(() => undefined);
  await AsyncStorage.multiRemove([QUEUE_KEY, ACTIVE_DRIVER_KEY, PUSH_KEY]);
}

export async function openDriverNavigation(destination: string) {
  const query = encodeURIComponent(destination);
  const url = Platform.select({
    ios: `maps://?daddr=${query}&dirflg=d`,
    android: `google.navigation:q=${query}&mode=d`,
    default: `https://www.google.com/maps/dir/?api=1&destination=${query}`,
  })!;
  if (await Linking.canOpenURL(url)) return Linking.openURL(url);
  return Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${query}`);
}

export async function getDriverMobilityHealth(): Promise<DriverMobilityHealth> {
  const [battery, lowPower, network, background, push, queue] = await Promise.all([
    Battery.getBatteryLevelAsync().catch(() => -1),
    Battery.isLowPowerModeEnabledAsync().catch(() => false),
    Network.getNetworkStateAsync(),
    Location.getBackgroundPermissionsAsync(),
    Notifications.getPermissionsAsync(),
    readQueue(),
  ]);
  return {
    batteryLevel: battery < 0 ? null : battery,
    lowPowerMode: lowPower,
    networkConnected: Boolean(network.isConnected),
    deviceTrusted: Device.isDevice && !Application.applicationId?.toLowerCase().includes("expo"),
    backgroundLocation: background.granted,
    pushGranted: push.granted,
    pendingSync: queue.length,
  };
}
