import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts = [
  "afritechnology.com",
  "www.afritechnology.com",
  "app.afritechnology.com",
  "localhost",
  "127.0.0.1",
];

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 4175,
    strictPort: true,
    allowedHosts,
  },
  preview: {
    host: "0.0.0.0",
    port: 4175,
    strictPort: true,
    allowedHosts,
  },
  build: {
    outDir: "dist",
  },
});
