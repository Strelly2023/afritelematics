import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const novaid = readFileSync(new URL("../src/novaid.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novaid is published in the public catalog and launcher", () => {
  assert.match(data, /NovaID/);
  assert.match(data, /novaid/);
  assert.match(data, /identity\.afritechnology\.com/);
});

test("novaid route is wired into the public web app", () => {
  assert.match(app, /NovaIDDetail/);
  assert.match(app, /\/products\/novaid/);
  assert.match(app, /NovaID is NovaTech's identity and access platform/);
});

test("novaid detail covers identity, verification, and trust", () => {
  assert.match(novaid, /Identity lifecycle from registration to audit/);
  assert.match(novaid, /Passkeys/);
  assert.match(novaid, /KYC and verification/);
  assert.match(novaid, /Device trust/);
  assert.match(novaid, /NovaTrust/);
  assert.match(novaid, /Consent management/);
});

test("novaid route is discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novaid/);
});
