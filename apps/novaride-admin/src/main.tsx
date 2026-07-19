import React from "react";
import { createRoot } from "react-dom/client";
import { AdminConsoleApp } from "./AdminConsoleApp";
import "./styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("root container missing");
}

createRoot(root).render(
  <React.StrictMode>
    <AdminConsoleApp />
  </React.StrictMode>,
);
