import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const robots = readFileSync(new URL("../public/robots.txt", import.meta.url), "utf8");

test("public root metadata is corporate and canonical", () => {
  assert.match(html, /AfriTechnology \| Trusted Digital Platforms/);
  assert.match(html, /https:\/\/afritechnology\.com\//);
  assert.doesNotMatch(html, /AfriRide Operator Dashboard/);
});

test("internal operator surfaces are not indexable public routes", () => {
  assert.match(robots, /Disallow: \/operator/);
  assert.doesNotMatch(app, /Operator Dashboard/);
});

test("contact workflow preserves recoverable failure state", () => {
  assert.match(app, /recoverable/);
  assert.match(app, /Your input has been preserved/);
});

test("public website distinguishes availability states", () => {
  assert.match(data, /Controlled Pilot/);
  assert.match(data, /Coming Soon/);
  assert.match(data, /Available/);
});
