import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/design/DesignStudioWorkspace.jsx", import.meta.url), "utf8");

test("studio exposes stable top-level hooks and the complete workspace shell", () => {
  for (const region of ["Design workspace tabs", "Infinite design canvas", "Pages & layers", "Properties", "Nova AI Designer", "Activity", "Comments", "Timeline", "Build", "Review"]) assert.match(source, new RegExp(region));
  assert.match(source, /useEffect\(\(\) =>/);
  assert.doesNotMatch(source, /if\s*\([^)]*\)\s*use(?:State|Effect|Memo)/);
});

test("canvas documents load and persist through the governed NCP006B wireframe API", () => {
  assert.match(source, /api\.listWireframes/);
  assert.match(source, /api\.createWireframe/);
  assert.match(source, /api\.updateWireframe/);
  assert.match(source, /studio_document: true/);
  assert.match(source, /regions: nodes/);
});

test("workspace includes editable frames, devices, layers, properties and accessible controls", () => {
  for (const capability of ["Desktop", "Tablet", "Phone", "Foldable", "Watch", "TV", "Vehicle", "Auto layout", "Constraints", "Semantic role", "Accessible name"]) assert.match(source, new RegExp(capability));
});
