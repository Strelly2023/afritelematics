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
});
