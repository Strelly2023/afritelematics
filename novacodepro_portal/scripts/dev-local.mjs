import { randomBytes } from "node:crypto";
import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const portalRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = path.resolve(portalRoot, "..");
const apiPort = Number(process.env.NOVACODEPRO_LOCAL_API_PORT || 8000);
const apiOrigin = `http://127.0.0.1:${apiPort}`;
const python = path.join(repositoryRoot, "venv", "bin", "python");
const vite = path.join(portalRoot, "node_modules", ".bin", "vite");
const stateRoot = path.join(os.tmpdir(), "novacodepro-local-runtime");
mkdirSync(stateRoot, { recursive: true });

if (!existsSync(python)) {
  console.error(`NovaCodePro local API cannot start because ${python} does not exist.`);
  console.error("Create the repository virtual environment before running npm run dev.");
  process.exit(1);
}

async function healthy() {
  try {
    const response = await fetch(`${apiOrigin}/health`, { signal: AbortSignal.timeout(1000) });
    if (!response.ok) return false;
    const payload = await response.json();
    return payload?.service === "afritech-api" && payload?.status === "healthy";
  } catch {
    return false;
  }
}

async function waitForApi(child) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (await healthy()) return;
    if (child && child.exitCode !== null) {
      throw new Error(`NovaCodePro API exited with code ${child.exitCode}.`);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`NovaCodePro API did not become healthy at ${apiOrigin}/health.`);
}

let apiProcess = null;
let frontendProcess = null;
let stopping = false;

function stop(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  if (frontendProcess && frontendProcess.exitCode === null) frontendProcess.kill("SIGTERM");
  if (apiProcess && apiProcess.exitCode === null) apiProcess.kill("SIGTERM");
  setTimeout(() => process.exit(exitCode), 250).unref();
}

process.on("SIGINT", () => stop(0));
process.on("SIGTERM", () => stop(0));

try {
  if (!(await healthy())) {
    console.log(`Starting NovaCodePro API at ${apiOrigin}…`);
    apiProcess = spawn(python, ["-m", "uvicorn", "afritech.api.app:app", "--host", "127.0.0.1", "--port", String(apiPort)], {
      cwd: repositoryRoot,
      stdio: "inherit",
      env: {
        ...process.env,
        AFRITECH_ENV: process.env.AFRITECH_ENV || "test",
        AFRITECH_RUNTIME_ENVIRONMENT: process.env.AFRITECH_RUNTIME_ENVIRONMENT || "TEST",
        AFRITECH_JWT_SECRET: process.env.AFRITECH_JWT_SECRET || randomBytes(32).toString("hex"),
        AFRIRIDE_DB_PATH: process.env.AFRIRIDE_DB_PATH || path.join(stateRoot, "runtime.sqlite3"),
        AFRITECH_MIGRATION_STATE_PATH: process.env.AFRITECH_MIGRATION_STATE_PATH || path.join(stateRoot, "migrations.json"),
        NOVATECH_RUNTIME_CONTROL_SQLITE_PATH: process.env.NOVATECH_RUNTIME_CONTROL_SQLITE_PATH || path.join(stateRoot, "control.sqlite3"),
        NOVATECH_EVIDENCE_ROOT: process.env.NOVATECH_EVIDENCE_ROOT || path.join(stateRoot, "evidence"),
      },
    });
  } else {
    console.log(`Using the healthy NovaCodePro API already running at ${apiOrigin}.`);
  }

  await waitForApi(apiProcess);
  console.log("NovaCodePro API is healthy. Starting Vite…");
  frontendProcess = spawn(vite, ["--host", "127.0.0.1", ...process.argv.slice(2)], {
    cwd: portalRoot,
    stdio: "inherit",
    env: { ...process.env, VITE_NOVACODEPRO_PROXY_TARGET: apiOrigin },
  });
  frontendProcess.on("exit", (code) => stop(code || 0));
  apiProcess?.on("exit", (code) => {
    if (!stopping) {
      console.error(`NovaCodePro API stopped unexpectedly with code ${code}.`);
      stop(code || 1);
    }
  });
} catch (error) {
  console.error(error instanceof Error ? error.message : "NovaCodePro local runtime failed to start.");
  stop(1);
}
