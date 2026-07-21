import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { createBuildInfo } from "./src/platform/buildInfo.js";

const allowedHosts = [
  "afritechnology.com",
  "www.afritechnology.com",
  "novacodepro.afritechnology.com",
  "localhost",
  "127.0.0.1",
];

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const packageJson = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));

const buildInfo = createBuildInfo({
  application: "NovaCodePro Experience Platform",
  version: packageJson.version,
  apiBaseUrl: "/v1",
  rootDir,
});

export default defineConfig({
  base: "/novacodepro/",
  plugins: [
    react(),
    {
      name: "novacodepro-version-json",
      generateBundle() {
        this.emitFile({
          type: "asset",
          fileName: "version.json",
          source: `${JSON.stringify(buildInfo, null, 2)}\n`,
        });
      },
    },
  ],
  define: {
    __NOVACODEPRO_BUILD_INFO__: JSON.stringify(buildInfo),
  },
  server: {
    host: "0.0.0.0",
    allowedHosts,
    fs: {
      allow: [path.resolve(rootDir, "..")],
    },
  },
  preview: {
    host: "0.0.0.0",
    allowedHosts,
  },
});
