import React from "react";
import { createRoot } from "react-dom/client";

import { ResilienceAvailabilityWindow } from "./ResilienceAvailabilityWindow.js";
import "./styles.css";

const container = document.getElementById("root");

if (!container) {
  throw new Error("root container missing");
}

createRoot(container).render(
  <React.StrictMode>
    <ResilienceAvailabilityWindow />
  </React.StrictMode>,
);
