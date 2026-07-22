import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");

test("request summary dependencies are initialized before the AI workspace model", () => {
  const requestSummaryDeclaration = appSource.indexOf("const requestSummary = useMemo");
  const selectedModeDeclaration = appSource.indexOf("const selectedMode = COMPOSER_MODES.find");
  const aiWorkspaceModelDeclaration = appSource.indexOf("const aiWorkspaceModel = useMemo");

  assert.notEqual(requestSummaryDeclaration, -1, "expected the requestSummary declaration");
  assert.notEqual(selectedModeDeclaration, -1, "expected the selectedMode declaration");
  assert.notEqual(aiWorkspaceModelDeclaration, -1, "expected the AI workspace model declaration");
  assert.ok(
    requestSummaryDeclaration < aiWorkspaceModelDeclaration,
    "requestSummary must be initialized before the AI workspace model consumes it",
  );
  assert.ok(
    selectedModeDeclaration < aiWorkspaceModelDeclaration,
    "selectedMode must be initialized before the AI workspace model consumes it",
  );
  assert.equal(
    appSource.match(/const requestSummary = useMemo/g)?.length,
    1,
    "expected exactly one requestSummary declaration",
  );
});
