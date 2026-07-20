import React from "react";
import { createRoot } from "react-dom/client";

import { ResilienceAvailabilityWindow } from "./ResilienceAvailabilityWindow.js";
import { createOperationsApi } from "./api/operationsApi.js";
import { getOperationsRuntimeConfig } from "./runtimeConfig.js";
import "./styles.css";

const container = document.getElementById("root");

if (!container) {
  throw new Error("root container missing");
}

const runtimeConfig = getOperationsRuntimeConfig();
const operationsApi = createOperationsApi(runtimeConfig);

createRoot(container).render(
  <React.StrictMode>
    <ResilienceAvailabilityWindow api={operationsApi} config={runtimeConfig} />
  </React.StrictMode>,
);
