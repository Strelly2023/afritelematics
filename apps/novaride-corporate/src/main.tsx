import React from "react";
import { createRoot } from "react-dom/client";
import { CorporatePortalApp } from "./CorporatePortalApp";
import "./styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("root container missing");
}

createRoot(root).render(
  <React.StrictMode>
    <CorporatePortalApp />
  </React.StrictMode>,
);
