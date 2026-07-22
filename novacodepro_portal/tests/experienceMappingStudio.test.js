import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/design/ExperienceMappingStudio.jsx", import.meta.url), "utf8");

test("experience mapping studio persists all four governed artifact types", () => {
  for (const method of ["createResearchStudy", "createPersona", "createJourney", "createUserFlow", "addJourneyStage", "addFlowNode"]) assert.match(source, new RegExp(`api\\.${method}`));
  assert.doesNotMatch(source, /mock|fixture/i);
});

test("persona, journey and research data retain evidence and traceability fields", () => {
  for (const field of ["accessibility_needs", "device_preferences", "trust_concerns", "evidence_references", "linked_requirements", "pain_point", "opportunity", "Review status", "Approval status"]) assert.match(source, new RegExp(field));
});

test("flow builder offers success, failure and governed system node semantics", () => {
  for (const nodeType of ["AUTHENTICATION", "AUTHORIZATION", "API_CALL", "ERROR", "RETRY", "BACKGROUND_PROCESS", "END"]) assert.match(source, new RegExp(nodeType));
  assert.match(source, /source_id/);
  assert.match(source, /target_id/);
});
