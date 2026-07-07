import React from "react";
import { NovaPayRoleApp } from "./src/roleApp";
import { config } from "./src/appConfig";

export default function App() {
  return <NovaPayRoleApp config={config} />;
}
