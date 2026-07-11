import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts = [
  "novacodepro.afritechnology.com",
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
