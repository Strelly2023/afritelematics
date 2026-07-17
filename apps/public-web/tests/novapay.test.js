import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const novapay = readFileSync(new URL("../src/novapay.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novapay is published in the public catalog and launcher", () => {
  assert.match(data, /NovaPay/);
  assert.match(data, /novapay/);
  assert.match(data, /business\.afritechnology\.com/);
});

test("novapay route is wired into the public web app", () => {
  assert.match(app, /NovaPayDetail/);
  assert.match(app, /\/products\/novapay/);
  assert.match(app, /NovaPay is NovaTech's payments and financial operations platform/);
});

test("novapay detail covers payments, risk, and trust", () => {
  assert.match(novapay, /Payments lifecycle from funding to reconciliation/);
  assert.match(novapay, /Consumer App/);
  assert.match(novapay, /Merchant App/);
  assert.match(novapay, /Escrow and settlement/);
  assert.match(novapay, /Fraud detection/);
  assert.match(novapay, /NovaTrust/);
});

test("novapay route is discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novapay/);
});
