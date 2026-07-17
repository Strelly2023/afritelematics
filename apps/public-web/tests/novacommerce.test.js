import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const novacommerce = readFileSync(new URL("../src/novacommerce.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novacommerce is published in the public catalog and launcher", () => {
  assert.match(data, /NovaCommerce/);
  assert.match(data, /novacommerce/);
  assert.match(data, /merchant\.afritechnology\.com/);
  assert.match(data, /Private Preview/);
});

test("novacommerce route is wired into the public web app", () => {
  assert.match(app, /NovaCommerceDetail/);
  assert.match(app, /\/products\/novacommerce/);
  assert.match(app, /NovaCommerce is NovaTech's commerce operating system/);
});

test("novacommerce detail covers lifecycle, merchants, and trust", () => {
  assert.match(novacommerce, /Commerce lifecycle from discovery to retention/);
  assert.match(novacommerce, /Merchant App/);
  assert.match(novacommerce, /Digital storefronts/);
  assert.match(novacommerce, /Checkout and payments/);
  assert.match(novacommerce, /NovaPay/);
  assert.match(novacommerce, /Support and evidence/);
});

test("novacommerce route is discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novacommerce/);
});
