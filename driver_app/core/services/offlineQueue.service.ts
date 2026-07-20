import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";

export type OfflineCommandPriority =
  | "EMERGENCY"
  | "HIGH"
  | "NORMAL"
  | "LOW";

export type OfflineCommandStatus =
  | "QUEUED"
  | "UPLOADING"
  | "AWAITING_ACK"
  | "SYNCED"
  | "CONFLICT"
  | "FAILED"
  | "DEAD_LETTER";

export type OfflineCommand = {
  id: string;
  idempotencyKey: string;
  operationType: string;
  aggregateId?: string;
  aggregateVersion?: number;
  encryptedPayload: string;
  authorityRequired: boolean;
  priority: OfflineCommandPriority;
  status: OfflineCommandStatus;
  attempts: number;
  createdAt: string;
  nextAttemptAt?: string;
  lastErrorCode?: string;
};

const QUEUE_KEY = "novaride:driver:offline-queue:v1";
const DEVICE_KEY_REF = "novaride:driver:offline-queue-key:v1";

async function ensureDeviceKey(): Promise<string> {
  const existing = await SecureStore.getItemAsync(DEVICE_KEY_REF);
  if (existing) {
    return existing;
  }
  const key = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  await SecureStore.setItemAsync(DEVICE_KEY_REF, key);
  return key;
}

async function encryptPayload(payload: unknown): Promise<string> {
  const key = await ensureDeviceKey();
  const encoded = JSON.stringify(payload);
  const encodeBase64 = (globalThis as { btoa?: (value: string) => string }).btoa;
  if (!encodeBase64) {
    throw new Error("base64_encoder_unavailable");
  }
  return `${key.slice(0, 8)}:${encodeBase64(unescape(encodeURIComponent(encoded)))}`;
}

function priorityRank(priority: OfflineCommandPriority): number {
  return { EMERGENCY: 0, HIGH: 1, NORMAL: 2, LOW: 3 }[priority];
}

export async function listOfflineCommands(): Promise<OfflineCommand[]> {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  const commands = raw ? (JSON.parse(raw) as OfflineCommand[]) : [];
  return commands.sort(
    (a, b) =>
      priorityRank(a.priority) - priorityRank(b.priority) ||
      new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
  );
}

async function save(commands: OfflineCommand[]): Promise<void> {
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(commands));
}

export async function enqueueOfflineCommand(input: {
  id: string;
  idempotencyKey: string;
  operationType: string;
  payload: unknown;
  authorityRequired?: boolean;
  priority?: OfflineCommandPriority;
  aggregateId?: string;
  aggregateVersion?: number;
}): Promise<OfflineCommand> {
  const commands = await listOfflineCommands();
  const existing = commands.find((command) => command.idempotencyKey === input.idempotencyKey);
  if (existing) {
    return existing;
  }
  const command: OfflineCommand = {
    id: input.id,
    idempotencyKey: input.idempotencyKey,
    operationType: input.operationType,
    aggregateId: input.aggregateId,
    aggregateVersion: input.aggregateVersion,
    encryptedPayload: await encryptPayload(input.payload),
    authorityRequired: input.authorityRequired || false,
    priority: input.priority || "NORMAL",
    status: "QUEUED",
    attempts: 0,
    createdAt: new Date().toISOString(),
  };
  await save([...commands, command]);
  return command;
}

export async function markOfflineCommandStatus(
  id: string,
  status: OfflineCommandStatus,
  lastErrorCode?: string,
): Promise<void> {
  const commands = await listOfflineCommands();
  await save(
    commands.map((command) =>
      command.id === id
        ? {
            ...command,
            status,
            attempts: status === "FAILED" ? command.attempts + 1 : command.attempts,
            lastErrorCode,
            nextAttemptAt:
              status === "FAILED"
                ? new Date(Date.now() + Math.min(300000, 1000 * 2 ** command.attempts)).toISOString()
                : command.nextAttemptAt,
          }
        : command,
    ),
  );
}
