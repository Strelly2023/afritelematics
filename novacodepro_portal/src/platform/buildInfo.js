import { execSync } from "node:child_process";

function resolveGitCommit(rootDir) {
  const override = process.env.NOVACODEPRO_BUILD_COMMIT;
  if (override && override.trim()) {
    return override.trim();
  }
  try {
    return execSync("git rev-parse --short HEAD", { cwd: rootDir, stdio: ["ignore", "pipe", "ignore"] })
      .toString()
      .trim();
  } catch {
    return "unknown";
  }
}

function resolveBuildTimestamp(rootDir) {
  const override = process.env.NOVACODEPRO_BUILD_TIMESTAMP;
  if (override && override.trim()) {
    return override.trim();
  }
  const sourceDateEpoch = Number(process.env.SOURCE_DATE_EPOCH);
  if (Number.isFinite(sourceDateEpoch) && sourceDateEpoch > 0) {
    return new Date(sourceDateEpoch * 1000).toISOString();
  }
  try {
    const seconds = execSync("git show -s --format=%ct HEAD", { cwd: rootDir, stdio: ["ignore", "pipe", "ignore"] })
      .toString()
      .trim();
    const epochSeconds = Number(seconds);
    if (Number.isFinite(epochSeconds) && epochSeconds > 0) {
      return new Date(epochSeconds * 1000).toISOString();
    }
  } catch {
    // Fall through to a stable sentinel instead of wall-clock time.
  }
  return "1970-01-01T00:00:00.000Z";
}

export function createBuildInfo({ application, version, apiBaseUrl = "/v1", rootDir }) {
  const commit = resolveGitCommit(rootDir);
  return {
    application,
    version,
    build_id: `${version}-${commit}`,
    commit,
    built_at: resolveBuildTimestamp(rootDir),
    api_base_url: apiBaseUrl,
  };
}
