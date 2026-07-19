import assert from "node:assert/strict";
import { test } from "node:test";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { AdminConsoleApp } from "../src/AdminConsoleApp.tsx";

test("admin console renders accessible navigation and guarded switches", () => {
  let renderer;
  act(() => {
    renderer = TestRenderer.create(React.createElement(AdminConsoleApp));
  });

  const root = renderer.root;
  const tabs = root.findAllByType("button").filter((button) => button.props["aria-pressed"] !== undefined);
  assert.equal(tabs.length, 3);
  assert.equal(tabs[0].props["aria-pressed"], true);

  act(() => {
    tabs[1].props.onClick();
  });

  assert.match(String(root.findByProps({ role: "status" }).children.join("")), /incidents controls/i);

  const pauseButton = root.findAllByType("button").find((button) => button.children.join("") === "Pause region");
  assert.ok(pauseButton);
  assert.equal(pauseButton.props.disabled, true);
});

test("admin console submits a governed switch when backend access is available", () => {
  const actions = [];
  let renderer;
  act(() => {
    renderer = TestRenderer.create(
      React.createElement(AdminConsoleApp, {
        backendAvailable: true,
        onSwitch: (action, reason) => actions.push({ action, reason }),
      }),
    );
  });

  const root = renderer.root;
  const textarea = root.findByType("textarea");
  act(() => {
    textarea.props.onChange({ target: { value: "Pause region for incident mitigation" } });
  });

  const checkbox = root.findByType("input");
  act(() => {
    checkbox.props.onChange({ target: { checked: true } });
  });

  const pauseButton = root.findAllByType("button").find((button) => button.children.join("") === "Pause region");
  act(() => {
    pauseButton.props.onClick();
  });

  assert.deepEqual(actions, [{ action: "Pause region", reason: "Pause region for incident mitigation" }]);
  assert.match(String(root.findByProps({ role: "status" }).children.join("")), /recorded with reason/);
});

test("admin console denies access without NovaID authorization", () => {
  let renderer;
  act(() => {
    renderer = TestRenderer.create(React.createElement(AdminConsoleApp, { authorized: false }));
  });

  const alert = renderer.root.findByProps({ role: "alert" });
  assert.match(String(alert.children.join("")), /Access denied/);
});
