import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/main.jsx", import.meta.url), "utf8");
const cloud = readFileSync(new URL("../src/novacloud.jsx", import.meta.url), "utf8");
const connect = readFileSync(new URL("../src/novaconnect.jsx", import.meta.url), "utf8");
const sitemap = readFileSync(new URL("../public/sitemap.xml", import.meta.url), "utf8");

test("novacloud and novaconnect are published in the public catalog and launcher", () => {
  assert.match(data, /NovaCloud/);
  assert.match(data, /NovaConnect/);
  assert.match(data, /novacloud/);
  assert.match(data, /novaconnect/);
  assert.match(data, /Private Preview/);
});

test("novacloud and novaconnect routes are wired into the public web app", () => {
  assert.match(app, /NovaCloudDetail/);
  assert.match(app, /NovaConnectDetail/);
  assert.match(app, /\/products\/novacloud/);
  assert.match(app, /\/products\/novaconnect/);
  assert.match(app, /NovaCloud is NovaTech's cloud infrastructure and platform services layer/);
  assert.match(app, /NovaConnect is NovaTech's API gateway, integrations, and partner ecosystem/);
});

test("novacloud detail covers environments, resilience, and cloud operations", () => {
  assert.match(cloud, /Infrastructure lifecycle from provisioning to optimisation/);
  assert.match(cloud, /Deployment gates/);
  assert.match(cloud, /Observability/);
  assert.match(cloud, /Disaster Recovery/);
  assert.match(cloud, /NovaTrust/);
  assert.match(cloud, /Healthy only/);
});

test("novaconnect detail covers integrations, APIs, and partner ecosystems", () => {
  assert.match(connect, /Integration lifecycle from registration to operation/);
  assert.match(connect, /API gateway/);
  assert.match(connect, /Webhooks/);
  assert.match(connect, /Partner routing/);
  assert.match(connect, /NovaFlow/);
  assert.match(connect, /Certified only/);
});

test("novacloud and novaconnect routes are discoverable from the public sitemap", () => {
  assert.match(sitemap, /products\/novacloud/);
  assert.match(sitemap, /products\/novaconnect/);
});
