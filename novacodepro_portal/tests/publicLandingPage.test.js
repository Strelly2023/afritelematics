import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/public/PublicLandingPage.jsx", import.meta.url), "utf8");

test("public landing page presents the complete governed design entry experience", () => {
  for (const content of [
    "UI/UX Design &amp;",
    "Start Designing",
    "Generate from Prompt",
    "Import Requirements",
    "Open Existing Project",
    "AI Designer",
    "Wireframing",
    "Design systems",
    "Accessibility",
    "Developer handoff",
    "NovaID authentication",
    "DEMONSTRATION",
  ]) {
    assert.ok(source.includes(content), `expected public page to include ${content}`);
  }
});

test("public landing page exposes accessible navigation and user preferences", () => {
  assert.ok(source.includes('aria-label="Platform navigation"'));
  assert.ok(source.includes('aria-label="Theme"'));
  assert.ok(source.includes('aria-label="Language"'));
  assert.ok(source.includes('className="skip-link"'));
  assert.ok(source.includes('aria-expanded={menuOpen}'));
});
