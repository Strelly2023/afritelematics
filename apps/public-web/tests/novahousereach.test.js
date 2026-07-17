import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const housing = readFileSync(new URL("../src/novahousereach.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novahousereach product is published in the public catalog and launcher", () => {
  assert.match(data, /NovaHouseReach/);
  assert.match(data, /novahousereach/);
  assert.match(data, /Private Preview/);
  assert.match(data, /Property Operating System/);
  assert.match(data, /novahousereach.afritechnology.com/);
});

test("novahousereach route is wired into the public web app", () => {
  assert.match(app, /NovaHouseReachDetail/);
  assert.match(app, /\/products\/novahousereach/);
  assert.match(app, /NovaHouseReach is NovaTech's property operating system/);
});

test("novahousereach detail covers lifecycle, search, and trust surfaces", () => {
  assert.match(housing, /Complete property lifecycle coverage/);
  assert.match(housing, /Natural language property matching/);
  assert.match(housing, /NovaID/);
  assert.match(housing, /NovaPay/);
  assert.match(housing, /NovaTrust/);
  assert.match(housing, /Open platform surfaces/);
  assert.match(housing, /Digital twin/);
});

test("novahousereach route is discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novahousereach/);
});
