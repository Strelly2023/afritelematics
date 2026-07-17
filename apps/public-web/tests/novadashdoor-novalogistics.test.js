import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const dashdoor = readFileSync(new URL("../src/novadashdoor.jsx", import.meta.url), "utf8");
const logistics = readFileSync(new URL("../src/novalogistics.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novadashdoor and novalogistics are published in the public catalog and launcher", () => {
  assert.match(data, /NovaDashDoor/);
  assert.match(data, /NovaLogistics X/);
  assert.match(data, /novadashdoor/);
  assert.match(data, /novalogistics/);
  assert.match(data, /Private Preview/);
});

test("novadashdoor and novalogistics routes are wired into the public web app", () => {
  assert.match(app, /NovaDashDoorDetail/);
  assert.match(app, /NovaLogisticsDetail/);
  assert.match(app, /\/products\/novadashdoor/);
  assert.match(app, /\/products\/novalogistics/);
  assert.match(app, /NovaDashDoor is NovaTech's AI-powered local commerce and last-mile delivery platform/);
  assert.match(app, /NovaLogistics X is NovaTech's logistics operating system/);
});

test("novadashdoor detail covers ordering, dispatch, payments, and trust", () => {
  assert.match(dashdoor, /Intelligent dispatch/);
  assert.match(dashdoor, /Natural language ordering/);
  assert.match(dashdoor, /Merchant App/);
  assert.match(dashdoor, /NovaPay/);
  assert.match(dashdoor, /NovaTrust/);
  assert.match(dashdoor, /Dispatch factors/);
});

test("novalogistics detail covers warehousing, routing, and chain of custody", () => {
  assert.match(logistics, /Complete logistics lifecycle coverage/);
  assert.match(logistics, /Warehouse App/);
  assert.match(logistics, /Route score factors/);
  assert.match(logistics, /NovaTrust/);
  assert.match(logistics, /NovaPay/);
  assert.match(logistics, /Fulfillment steps/);
});

test("novadashdoor and novalogistics routes are discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novadashdoor/);
  assert.match(sitemap, /products\/novalogistics/);
});
