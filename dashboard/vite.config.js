import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts = [
  "afritechnology.com",
  "www.afritechnology.com",
  "app.afritechnology.com",
  "api.afritechnology.com",
  "verify.afritechnology.com",

  "identity.afritechnology.com",
  "trust.afritechnology.com",
  "merchant.afritechnology.com",
  "business.afritechnology.com",
  "operator.afritechnology.com",
  "agent.afritechnology.com",
  "fleet.afritechnology.com",
  "support.afritechnology.com",
  "status.afritechnology.com",
  "developer.afritechnology.com",
  "docs.afritechnology.com",
  "download.afritechnology.com",

  "localhost",
  "127.0.0.1",
];

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    allowedHosts,
  },
  preview: {
    host: "0.0.0.0",
    allowedHosts,
  },
});
