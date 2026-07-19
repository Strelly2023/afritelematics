import assert from "node:assert/strict";
import { test } from "node:test";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { FraudCenterApp } from "../src/FraudCenterApp.tsx";

test("fraud center renders accessible queue and disabled governance actions without backend", () => {
  let renderer;
  act(() => {
    renderer = TestRenderer.create(React.createElement(FraudCenterApp));
  });

  const root = renderer.root;
  const queueButtons = root.findAllByType("button").filter((button) => button.props["aria-pressed"] !== undefined);
  assert.equal(queueButtons.length, 4);
  assert.equal(queueButtons[0].props["aria-pressed"], true);

  const status = root.findByProps({ role: "status" });
  assert.match(String(status.children.join("")), /Backend unavailable/);

  const freezeButton = root.findAllByType("button").find((button) => button.children.join("") === "Freeze payout");
  assert.ok(freezeButton);
  assert.equal(freezeButton.props.disabled, true);
});

test("fraud center updates selection and dispatches backend-enabled actions", () => {
  const actions = [];
  let renderer;
  act(() => {
    renderer = TestRenderer.create(
      React.createElement(FraudCenterApp, {
        backendAvailable: true,
        onAction: (caseId, action) => {
          actions.push({ caseId, action });
        },
      }),
    );
  });

  const root = renderer.root;
  const queueButtons = root.findAllByType("button").filter((button) => button.props["aria-pressed"] !== undefined);
  act(() => {
    queueButtons[1].props.onClick();
  });

  const caseDetails = root.findByProps({ role: "status" });
  assert.match(String(caseDetails.children.join("")), /Selected FC-002/);

  const freezeButton = root.findAllByType("button").find((button) => button.children.join("") === "Freeze payout");
  act(() => {
    freezeButton.props.onClick();
  });

  assert.deepEqual(actions, [{ caseId: "FC-002", action: "Freeze payout" }]);
  assert.match(String(caseDetails.children.join("")), /Freeze payout queued for FC-002/);
});

test("fraud center denies access when NovaID authorization is absent", () => {
  let renderer;
  act(() => {
    renderer = TestRenderer.create(React.createElement(FraudCenterApp, { authorized: false }));
  });

  const alert = renderer.root.findByProps({ role: "alert" });
  assert.match(String(alert.children.join("")), /Access denied/);
});
