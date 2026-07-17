import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const allowedHosts = [
  "novacodepro.afritechnology.com",
  "localhost",
  "127.0.0.1",
];

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const packageJson = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));

function resolveGitCommit() {
  try {
    return execSync("git rev-parse --short HEAD", { cwd: rootDir, stdio: ["ignore", "pipe", "ignore"] })
      .toString()
      .trim();
  } catch {
    return "unknown";
  }
}

const buildInfo = {
  application: "NovaCodePro Experience Platform",
  version: packageJson.version,
  build_id: `${packageJson.version}-${resolveGitCommit()}`,
  commit: resolveGitCommit(),
  built_at: new Date().toISOString(),
  api_base_url: "/v1",
};

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
