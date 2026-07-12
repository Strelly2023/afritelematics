import { useSyncExternalStore } from "react";

import { platformRuntime } from "./runtime.js";

export function usePlatformRuntime() {
  const state = useSyncExternalStore(
    platformRuntime.subscribe,
    platformRuntime.getState,
    platformRuntime.getState,
  );
  return {
    ...state,
    ...platformRuntime,
  };
}
