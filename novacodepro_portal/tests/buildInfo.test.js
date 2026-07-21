import assert from "node:assert/strict";
import { describe, it } from "node:test";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createBuildInfo } from "../src/platform/buildInfo.js";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

describe("build info", () => {
  it("derives a deterministic timestamp from SOURCE_DATE_EPOCH", () => {
    const original = process.env.SOURCE_DATE_EPOCH;
    process.env.SOURCE_DATE_EPOCH = "1234567890";
    try {
      const buildInfo = createBuildInfo({
        application: "NovaCodePro Experience Platform",
        version: "0.1.0",
        apiBaseUrl: "/v1",
        rootDir,
      });

      assert.equal(buildInfo.built_at, "2009-02-13T23:31:30.000Z");
      assert.match(buildInfo.build_id, /^0\.1\.0-/);
      assert.equal(buildInfo.api_base_url, "/v1");
      assert.equal(buildInfo.application, "NovaCodePro Experience Platform");
    } finally {
      if (original === undefined) {
        delete process.env.SOURCE_DATE_EPOCH;
      } else {
        process.env.SOURCE_DATE_EPOCH = original;
      }
    }
  });

  it("honors explicit commit and timestamp overrides", () => {
    const originalCommit = process.env.NOVACODEPRO_BUILD_COMMIT;
    const originalTimestamp = process.env.NOVACODEPRO_BUILD_TIMESTAMP;
    process.env.NOVACODEPRO_BUILD_COMMIT = "abc1234";
    process.env.NOVACODEPRO_BUILD_TIMESTAMP = "2026-07-21T00:00:00.000Z";
    try {
      const buildInfo = createBuildInfo({
        application: "NovaCodePro Experience Platform",
        version: "0.1.0",
        apiBaseUrl: "/v1",
        rootDir,
      });

      assert.equal(buildInfo.commit, "abc1234");
      assert.equal(buildInfo.build_id, "0.1.0-abc1234");
      assert.equal(buildInfo.built_at, "2026-07-21T00:00:00.000Z");
    } finally {
      if (originalCommit === undefined) {
        delete process.env.NOVACODEPRO_BUILD_COMMIT;
      } else {
        process.env.NOVACODEPRO_BUILD_COMMIT = originalCommit;
      }
      if (originalTimestamp === undefined) {
        delete process.env.NOVACODEPRO_BUILD_TIMESTAMP;
      } else {
        process.env.NOVACODEPRO_BUILD_TIMESTAMP = originalTimestamp;
      }
    }
  });
});
