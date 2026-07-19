import assert from "node:assert/strict";
import { test } from "node:test";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { CorporatePortalApp } from "../src/CorporatePortalApp.tsx";

test("corporate portal renders accessible navigation and disables approvals without backend", () => {
  let renderer;
  act(() => {
    renderer = TestRenderer.create(React.createElement(CorporatePortalApp));
  });

  const root = renderer.root;
  const tabs = root.findAllByType("button").filter((button) => button.props["aria-pressed"] !== undefined);
  assert.equal(tabs.length, 3);
  assert.equal(tabs[0].props["aria-pressed"], true);

  act(() => {
    tabs[2].props.onClick();
  });

  assert.match(String(root.findByProps({ role: "status" }).children.join("")), /approvals controls/i);

  const submitButton = root.findAllByType("button").find((button) => button.children.join("") === "Submit approval");
  assert.ok(submitButton);
  assert.equal(submitButton.props.disabled, true);
});

test("corporate portal supports governed approval submission when backend is available", () => {
  const approvals = [];
  let renderer;
  act(() => {
    renderer = TestRenderer.create(
      React.createElement(CorporatePortalApp, {
        backendAvailable: true,
        onApprove: (scope, reason) => approvals.push({ scope, reason }),
      }),
    );
  });

  const root = renderer.root;
  const tabs = root.findAllByType("button").filter((button) => button.props["aria-pressed"] !== undefined);
  act(() => {
    tabs[2].props.onClick();
  });

  const textarea = root.findByType("textarea");
  act(() => {
    textarea.props.onChange({ target: { value: "Approve monthly guest ride allocation" } });
  });

  act(() => {
    root.findByType("form").props.onSubmit({ preventDefault() {} });
  });

  assert.deepEqual(approvals, [{ scope: "department-billing", reason: "Approve monthly guest ride allocation" }]);
  assert.match(String(root.findByProps({ role: "status" }).children.join("")), /Approval submitted/);
});

test("corporate portal denies access without NovaID authorization", () => {
  let renderer;
  act(() => {
    renderer = TestRenderer.create(React.createElement(CorporatePortalApp, { authorized: false }));
  });

  const alert = renderer.root.findByProps({ role: "alert" });
  assert.match(String(alert.children.join("")), /Access denied/);
});
