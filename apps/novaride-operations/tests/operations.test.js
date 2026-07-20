import assert from "node:assert/strict";
import { test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { ResilienceAvailabilityWindow } from "../src/ResilienceAvailabilityWindow.js";
import { getOperationsSection, operationsSections } from "../src/operationsModel.js";

test("operations model exposes the interactive operator workspaces", () => {
  assert.equal(operationsSections.length, 6);
  assert.equal(getOperationsSection("overview").label, "Overview");
  assert.equal(getOperationsSection("incidents").actions[0], "Assign commander");
  assert.equal(getOperationsSection("support").summary.includes("refund"), true);
});

test("operations portal renders a navigable incident and support workspace", () => {
  const markup = renderToStaticMarkup(React.createElement(ResilienceAvailabilityWindow));

  assert.match(markup, /NovaRide operations/);
  assert.match(markup, /Resilience and availability/);
  assert.match(markup, /Operations sections/);
  assert.match(markup, /Operational queue/);
  assert.match(markup, /Morning dispatch review/);
  assert.match(markup, /Region health check/);
  assert.match(markup, /Open incident/);
  assert.match(markup, /Broadcast status/);
  assert.match(markup, /Dependency-aware health/);
  assert.match(markup, /PostgreSQL: writable primary/);
});

test("operations portal exposes pressed state for the active section", () => {
  const markup = renderToStaticMarkup(React.createElement(ResilienceAvailabilityWindow));

  assert.match(markup, /aria-pressed="true"/);
  assert.match(markup, /aria-pressed="false"/);
  assert.match(markup, /Overview/);
  assert.match(markup, /Evidence/);
});
