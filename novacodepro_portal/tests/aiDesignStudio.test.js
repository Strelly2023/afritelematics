import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/design/AIDesignStudio.jsx", import.meta.url), "utf8");

test("AI design generation joins NovaAI execution governance to durable design drafts", () => {
  for (const call of ["ai.createExecution", "ai.analyseExecution", "design.createAIDesignDraft", "design.listAIGenerations", "design.createReview"]) assert.match(source, new RegExp(call.replace(".", "\\.")));
  for (const context of ["brand", "devices", "accessibility_target", "policy_result", "human_verified"]) assert.match(source, new RegExp(context));
});

test("AI designer supports the requested generation and improvement actions", () => {
  for (const capability of ["Generate dashboard", "Generate mobile app", "Improve usability", "Improve accessibility", "Requirements → flows", "Wireframes → mockups", "Generate implementation code", "Compare alternatives"]) assert.match(source, new RegExp(capability));
});

test("AI review is criterion-versioned, evidence-backed and explicitly non-certifying", () => {
  for (const criterion of ["Usability", "Accessibility", "Performance risk", "Consistency", "Responsiveness", "Requirements coverage"]) assert.match(source, new RegExp(criterion));
  assert.match(source, /not a certification|not compliance certification/);
  assert.match(source, /human_review_status: "PENDING"/);
});
