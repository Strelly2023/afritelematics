import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Application from "expo-application";
import * as Battery from "expo-battery";
import * as Device from "expo-device";
import * as Location from "expo-location";
import * as Network from "expo-network";
import * as Notifications from "expo-notifications";
import Constants from "expo-constants";
import { Platform } from "react-native";

import { apiRequest } from "../api/client";

const QUEUE_KEY = "@afriride/rider/offline-queue/v1";
const PUSH_KEY = "@afriride/rider/push-token/v1";

export type MobilityHealth = {
  batteryLevel: number | null;
  lowPowerMode: boolean;
  networkConnected: boolean;
  deviceTrusted: boolean;
  locationGranted: boolean;
  pushGranted: boolean;
  pendingSync: number;
};

type QueuedOperation = {
  id: string;
  path: string;
  body: Record<string, unknown>;
  createdAt: string;
  attempts: number;
};

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

async function readQueue(): Promise<QueuedOperation[]> {
  const value = await AsyncStorage.getItem(QUEUE_KEY);
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function writeQueue(queue: QueuedOperation[]) {
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

export async function enqueueRiderOperation(
  path: string,
  body: Record<string, unknown>,
) {
  const queue = await readQueue();
  const operation: QueuedOperation = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    path,
    body,
    createdAt: new Date().toISOString(),
    attempts: 0,
  };
  await writeQueue([...queue, operation]);
  return operation.id;
}

export async function synchronizeRiderQueue() {
  const network = await Network.getNetworkStateAsync();
  const queue = await readQueue();
  if (!network.isConnected || queue.length === 0) return queue.length;

  const remaining: QueuedOperation[] = [];
  for (const operation of queue) {
    try {
      await apiRequest(operation.path, {
        method: "POST",
        headers: { "Idempotency-Key": operation.id },
        body: { ...operation.body, offline_created_at: operation.createdAt },
      });
    } catch {
      remaining.push({ ...operation, attempts: operation.attempts + 1 });
    }
  }
  await writeQueue(remaining);
  return remaining.length;
}

export async function registerRiderPush(riderId: string) {
  if (!Device.isDevice) return null;
  const permission = await Notifications.requestPermissionsAsync();
  if (!permission.granted) return null;
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
  if (token !== (await AsyncStorage.getItem(PUSH_KEY))) {
    await apiRequest("/v1/mobile/devices/push", {
      method: "POST",
      body: { actor_id: riderId, role: "rider", token, platform: Platform.OS },
    });
    await AsyncStorage.setItem(PUSH_KEY, token);
  }
  return token;
}

export async function getRiderLocation() {
  const permission = await Location.requestForegroundPermissionsAsync();
  if (!permission.granted) return null;
  return Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.Balanced,
  });
}

export async function getRiderMobilityHealth(): Promise<MobilityHealth> {
  const [battery, lowPowerMode, network, location, push, pending] =
    await Promise.all([
      Battery.getBatteryLevelAsync().catch(() => -1),
      Battery.isLowPowerModeEnabledAsync().catch(() => false),
      Network.getNetworkStateAsync(),
      Location.getForegroundPermissionsAsync(),
      Notifications.getPermissionsAsync(),
      readQueue(),
    ]);
  return {
    batteryLevel: battery < 0 ? null : battery,
    lowPowerMode,
    networkConnected: Boolean(network.isConnected),
    deviceTrusted:
      Device.isDevice &&
      !Application.applicationId?.toLowerCase().includes("expo"),
    locationGranted: location.granted,
    pushGranted: push.granted,
    pendingSync: pending.length,
  };
}
