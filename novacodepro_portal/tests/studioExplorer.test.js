import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { StudioExplorer } from "../src/novacodepro/explorer/StudioExplorer.js";

const workspaceId = "workspace-001";

const seedData = {
  workspaces: [
    { id: workspaceId, name: "NovaRide Workspace", status: "ACTIVE", home_route: "/novacodepro/workspace/novaride/dashboard" },
    { id: "workspace-002", name: "NovaPay Workspace", status: "ACTIVE", home_route: "/novacodepro/workspace/novapay/dashboard" },
  ],
  selectedWorkspaceId: workspaceId,
  selectedWorkspace: { id: workspaceId, name: "NovaRide Workspace", status: "ACTIVE", home_route: "/novacodepro/workspace/novaride/dashboard" },
  workspaceProjects: [
    { id: "project-001", name: "Ride App", status: "ACTIVE", owner_id: "dev-one" },
    { id: "project-002", name: "Dispatch Service", status: "DRAFT", owner_id: "dev-two" },
  ],
  workspaceFavorites: [{ id: "fav-001", label: "Open Roadmap", route: "explorer://workspace-001/project/project-001" }],
  recentResources: [{ id: "recent-001", type: "file", name: "app.tsx", path: "apps/rider/src/app.tsx" }],
  openEditors: [{ id: "editor-001", name: "app.tsx", path: "apps/rider/src/app.tsx", pinned: true, language: "TypeScript React" }],
  repositoryStatus: { root: "/repo", branch: "main", head_sha: "abc123", dirty: true },
  repositoryTreeLoaded: true,
  repositoryEntries: [
    { path: "apps/rider/src/app.tsx", extension: ".tsx", size_bytes: 1024 },
    { path: "tests/rider/app.test.tsx", extension: ".tsx", size_bytes: 512 },
    { path: "docs/architecture.md", extension: ".md", size_bytes: 256 },
    { path: "infra/deploy.yaml", extension: ".yaml", size_bytes: 128 },
  ],
  selectedResource: {
    id: "file:workspace-001:apps/rider/src/app.tsx",
    type: "file",
    name: "app.tsx",
    path: "apps/rider/src/app.tsx",
    workspaceId,
    organizationId: "novatech",
    repositoryId: "/repo",
    language: "TypeScript React",
    gitStatus: "Modified",
    sizeBytes: 1024,
    metadata: { classification: "source" },
  },
  searchQuery: "app",
  searchResults: [{ path: "apps/rider/src/app.tsx", snippet: "app" }],
  searchState: "ready",
  preview: {
    state: "ready",
    language: "TypeScript React",
    encoding: "utf-8",
    sizeLabel: "1,024 bytes",
    lines: ["export const app = true;", "console.log(app);"],
    truncated: false,
  },
  expandedPaths: new Set(["organisation:workspace-001:NovaTech", "workspace:workspace-001:workspace-001"]),
  loadState: "ready",
  loadError: null,
  filterText: "",
};

describe("StudioExplorer", () => {
  it("renders a governed explorer workbench backed by real workspace and repository data", () => {
    const markup = renderToStaticMarkup(
      React.createElement(StudioExplorer, {
        session: {
          user: { id: "alice" },
          organization: { id: "novatech", name: "NovaTech" },
          workspace: { id: workspaceId, name: "NovaRide Workspace" },
        },
        environment: "Development",
        activeRole: { label: "Developer" },
        activeProject: { name: "Ride App" },
        seedData,
        navigate: () => {},
        onFocusNav: () => {},
      }),
    );

    assert.match(markup, /Governed solution, project, repository and file explorer/);
    assert.match(markup, /NovaRide Workspace/);
    assert.match(markup, /Workspace tree/);
    assert.match(markup, /Repository tree/);
    assert.match(markup, /Open editors/);
    assert.match(markup, /Favourites/);
    assert.match(markup, /Recent resources/);
    assert.match(markup, /Context inspector/);
    assert.match(markup, /TypeScript React/);
    assert.match(markup, /Modified/);
    assert.match(markup, /Traceability links/);
  });

  it("renders unsupported preview state safely", () => {
    const markup = renderToStaticMarkup(
      React.createElement(StudioExplorer, {
        session: {
          user: { id: "alice" },
          organization: { id: "novatech", name: "NovaTech" },
          workspace: { id: workspaceId, name: "NovaRide Workspace" },
        },
        environment: "Development",
        activeRole: { label: "Developer" },
        activeProject: { name: "Ride App" },
        seedData: {
          ...seedData,
          selectedResource: {
            ...seedData.selectedResource,
            path: "docs/manual.pdf",
            type: "file",
            language: "Plain text",
          },
          preview: { state: "unsupported", language: "Plain text", encoding: "utf-8", sizeLabel: "Unavailable" },
          searchState: "idle",
          searchResults: [],
        },
        navigate: () => {},
        onFocusNav: () => {},
      }),
    );

    assert.match(markup, /Unsupported preview/);
    assert.match(markup, /Open-in-editor is unavailable until NCP-STUDIO-003/);
  });

  it("keeps the Studio shell wired to the explorer branch", () => {
    const appSource = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
    assert.ok(appSource.includes("StudioExplorer"));
    assert.ok(appSource.includes('focusNav === "Explorer"'));
  });
});
