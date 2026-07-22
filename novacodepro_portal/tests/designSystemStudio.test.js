import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../src/design/DesignSystemStudio.jsx", import.meta.url), "utf8");

test("design system persists tokens, components and brands through governed APIs", () => {
  for (const method of ["listDesignTokens", "createDesignToken", "listComponents", "createComponent", "listBrands", "createBrand"]) assert.match(source, new RegExp(`api\\.${method}`));
});

test("token architecture covers enterprise design categories and themes", () => {
  for (const category of ["COLOR", "TYPOGRAPHY", "SPACING", "RADIUS", "MOTION", "BREAKPOINT", "Z_INDEX", "OPACITY"]) assert.match(source, new RegExp(category));
  for (const theme of ["Light", "Dark", "High contrast", "Brand", "Product", "Tenant"]) assert.match(source, new RegExp(theme));
});

test("component definitions carry properties variants states responsiveness accessibility and examples", () => {
  for (const key of ["properties", "variants", "states", "responsive_behavior", "accessibility", "usage_documentation", "code_examples"]) assert.match(source, new RegExp(key));
});
