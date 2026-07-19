import React from "react";
import { createRoot } from "react-dom/client";

import { FraudCenterApp } from "./FraudCenterApp";
import "./styles.css";

const container = document.getElementById("root");

if (!container) {
  throw new Error("root container missing");
}

createRoot(container).render(
  <React.StrictMode>
    <FraudCenterApp />
  </React.StrictMode>,
);
