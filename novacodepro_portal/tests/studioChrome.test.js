import assert from "node:assert/strict";
import { describe, it } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { StudioChrome } from "../src/novacodepro/StudioChrome.js";

describe("StudioChrome", () => {
  it("renders the enterprise studio shell regions", () => {
    const markup = renderToStaticMarkup(
      React.createElement(
        StudioChrome,
        {
          title: "NovaCodePro Studio",
          subtitle: "NovaTech · Workspace · Development",
          menus: [
            {
              id: "file",
              label: "File",
              items: [
                { id: "open", label: "Open workspace", description: "Go to the workspace hub" },
              ],
            },
            {
              id: "git",
              label: "Git",
              items: [
                { id: "sync", label: "Sync", description: "Synchronize the branch" },
              ],
            },
          ],
          activityItems: [
            { id: "Dashboard", label: "Home", icon: "⌂", description: "Workspace overview" },
            { id: "Explorer", label: "Explorer", icon: "⟂", description: "Browse workspace resources" },
          ],
          contextItems: [
            { label: "Organisation", value: "NovaTech" },
            { label: "Workspace", value: "Enterprise" },
          ],
          statusItems: [
            { label: "Auth", value: "Signed in", tone: "success" },
            { label: "Connection", value: "Connected", tone: "success" },
          ],
        },
        React.createElement("main", null, "Workspace content"),
      ),
    );

    assert.match(markup, /NovaCodePro Studio/);
    assert.match(markup, /File/);
    assert.match(markup, /Git/);
    assert.match(markup, /Workspace overview/);
    assert.match(markup, /Organisation/);
    assert.match(markup, /Signed in/);
    assert.match(markup, /Workspace content/);
  });
});
