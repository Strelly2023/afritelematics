import { useSyncExternalStore } from "react";

import { platformRuntime } from "./runtime.js";

export function usePlatformRuntime() {
  return useSyncExternalStore(
    platformRuntime.subscribe,
    platformRuntime.getState,
    platformRuntime.getState,
  );
}

