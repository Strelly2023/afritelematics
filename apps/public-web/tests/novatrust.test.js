import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const novatrust = readFileSync(new URL("../src/novatrust.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novatrust is published in the public catalog and launcher", () => {
  assert.match(data, /NovaTrust/);
  assert.match(data, /novatrust/);
  assert.match(data, /trust\.afritechnology\.com/);
});

test("novatrust route is wired into the public web app", () => {
  assert.match(app, /NovaTrustDetail/);
  assert.match(app, /\/products\/novatrust/);
  assert.match(app, /NovaTrust is NovaTech's evidence, assurance, policy, and verification platform/);
});

test("novatrust detail covers lifecycle, evidence, and trust controls", () => {
  assert.match(novatrust, /Trust lifecycle from evidence discovery to dispute resolution/);
  assert.match(novatrust, /Evidence verification/);
  assert.match(novatrust, /Policy controls/);
  assert.match(novatrust, /Fraud detection/);
  assert.match(novatrust, /Audit history/);
  assert.match(novatrust, /Dispute support/);
});

test("novatrust route is discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novatrust/);
});
