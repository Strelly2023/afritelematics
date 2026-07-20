import assert from "node:assert/strict";
import { test } from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { ResilienceAvailabilityWindow } from "../src/ResilienceAvailabilityWindow.js";
import { getOperationsSection, operationsSections } from "../src/operationsModel.js";

function state(status, data = null, updatedAt = "2026-07-20T00:00:00Z") {
  return { status, data, updatedAt };
}

function buildWorkspace() {
  const now = "2026-07-20T00:00:00Z";
  return {
    overview: state("success", {
      generated_at: now,
      summary: {
        active_trips: 1,
        drivers_online: 1,
        drivers_available: 1,
        riders_active: 1,
        open_incidents: 1,
        critical_incidents: 0,
        open_safety_cases: 1,
        open_support_cases: 1,
        pending_refunds: 1,
        payment_failures: 1,
        pending_approvals: 1,
      },
      dependencies: [
        { name: "PostgreSQL", status: "unknown", observed_at: now, latency_ms: null, message: "not probed", source: "runtime", degraded_reason: "probe_not_configured" },
        { name: "Redis", status: "unknown", observed_at: now, latency_ms: null, message: "not probed", source: "runtime", degraded_reason: "probe_not_configured" },
      ],
      recent_activity: [{ subject_id: "incident_1", event_type: "incident_created", message: "Incident created" }],
      alerts: [],
    }, now),
    dependencies: state("success", {
      generated_at: now,
      dependencies: [
        { name: "PostgreSQL", status: "unknown", observed_at: now, latency_ms: null, message: "not probed", source: "runtime", degraded_reason: "probe_not_configured" },
        { name: "Redis", status: "unknown", observed_at: now, latency_ms: null, message: "not probed", source: "runtime", degraded_reason: "probe_not_configured" },
      ],
    }, now),
    map: state("success", {
      generated_at: now,
      items: [
        {
          trip_id: "trip_1",
          driver_id: "driver_1",
          rider_id: "rider_1",
          vehicle_id: "vehicle_1",
          status: "IN_PROGRESS",
          pickup: { label: "City Pickup" },
          destination: { label: "City Destination" },
          current_location: { lat: -37.8135, lng: 144.965, heading: 90, speed: 32, label: "Live city route" },
          heading: 90,
          speed: 32,
          last_location_at: now,
          region: "AU",
          service_area: "region:AU",
          incident_status: "reported",
          safety_status: "new",
        },
      ],
    }, now),
    trips: state("success", { generated_at: now, items: [{ trip_id: "trip_1", status: "IN_PROGRESS", region: "AU", service_area: "region:AU", driver_id: "driver_1", rider_id: "rider_1", pickup: { label: "City Pickup" }, destination: { label: "City Destination" } }] }, now),
    drivers: state("success", { generated_at: now, items: [{ driver_id: "driver_1", status: "AVAILABLE", driver_name: "Amina Driver", vehicle_id: "vehicle_1", region: "AU", dispatchable: true, location_precision: "unknown" }] }, now),
    dispatch: state("success", { generated_at: now, items: [{ offer_id: "offer_1", trip_id: "trip_1", driver_id: "driver_1", state: "CREATED", estimated_earnings: { amount: "12.50", currency: "AUD" }, dispatchable: true, queue_position: 1, last_updated_at: now }] }, now),
    incidents: state("success", { generated_at: now, items: [{ incident_id: "incident_1", title: "Dispatch delay", severity: "SEV2", current_state: "declared", assigned_to: "incident-commander", commander: "incident-commander", affected_trips: ["trip_1"] }] }, now),
    safety: state("success", { generated_at: now, items: [{ case_id: "safety_1", severity: "SEV1", current_state: "new", linked_trip_id: "trip_1", linked_driver_id: "driver_1", assigned_to: null }] }, now),
    support: state("success", { generated_at: now, items: [{ case_id: "support_1", case_type: "booking_problem", current_state: "new", trip_id: "trip_1", rider_id: "rider_1", driver_id: "driver_1" }] }, now),
    refunds: state("success", { generated_at: now, items: [{ refund_id: "refund_1", current_state: "approval_pending", amount: "75", currency: "AUD", payment_id: "payment_1", requester_id: "finance_1", approval_required: true }] }, now),
    investigations: state("success", { generated_at: now, items: [{ investigation_id: "investigation_1", current_state: "open", payment_id: "payment_1", reason: "payment declined", assigned_to: "finance_1" }] }, now),
    disputes: state("success", { generated_at: now, items: [{ dispute_id: "dispute_1", current_state: "open", trip_id: "trip_1", policy_version: "2026.2", appeal_state: "none" }] }, now),
    actions: state("success", { generated_at: now, items: [{ action_id: "action_1", action_type: "manual_dispatch", current_state: "requested", target_id: "trip_1", requested_by: "ops_1", approved_by: null, risk_level: "medium" }] }, now),
    evidence: state("success", { generated_at: now, items: [{ evidence_id: "evidence_1", evidence_type: "incident.lifecycle", subject_id: "incident_1", integrity_status: "verified", verification_status: "verified" }] }, now),
  };
}

function buildMockApi() {
  const noop = async () => ({});
  return {
    getOverview: noop,
    getDependencies: noop,
    getLiveMap: noop,
    getLiveTrips: noop,
    getLiveDrivers: noop,
    getDispatchQueue: noop,
    getDispatchHealth: noop,
    getIncidents: noop,
    getSafetyCases: noop,
    getSupportCases: noop,
    getRefunds: noop,
    getPaymentInvestigations: noop,
    getDisputes: noop,
    getActions: noop,
    getEvidence: noop,
    createIncident: noop,
    createSupportCase: noop,
    createRefund: noop,
    createAction: noop,
    createPaymentInvestigation: noop,
    assignIncident: noop,
    transitionIncident: noop,
    assignSafetyCase: noop,
    escalateSafetyCase: noop,
    assignSupportCase: noop,
    resolveSupportCase: noop,
    evaluateRefund: noop,
    approveRefund: noop,
    executeRefund: noop,
    evaluateAction: noop,
    approveAction: noop,
    executeAction: noop,
    verifyAction: noop,
  };
}

test("operations model exposes the governed workspaces", () => {
  assert.equal(operationsSections.length, 13);
  assert.equal(getOperationsSection("overview").label, "Overview");
  assert.equal(getOperationsSection("incidents").summary.includes("Incident lifecycle"), true);
  assert.equal(getOperationsSection("support").summary.includes("Search, case handling"), true);
});

test("operations portal renders live backend-backed workspace data", () => {
  const markup = renderToStaticMarkup(
    React.createElement(ResilienceAvailabilityWindow, {
      api: buildMockApi(),
      config: {
        baseUrl: "/api/v1/novaride/operations",
        liveMapEnabled: true,
        refundExecutionEnabled: false,
        productionActionsEnabled: false,
        requestTimeoutMs: 12_000,
      },
      initialWorkspace: buildWorkspace(),
    }),
  );

  assert.match(markup, /NovaRide operations/);
  assert.match(markup, /Operations workspace/);
  assert.match(markup, /Active trips/);
  assert.match(markup, /Dependency health/);
  assert.match(markup, /incident_created/);
  assert.match(markup, /refund execution disabled/i);
  assert.match(markup, /Production actions disabled/);
  assert.match(markup, /Evidence-preserving workflows/);
  assert.doesNotMatch(markup, /PostgreSQL: writable primary/);
});

test("operations portal renders loading and restricted states honestly", () => {
  const loadingMarkup = renderToStaticMarkup(
    React.createElement(ResilienceAvailabilityWindow, {
      initialWorkspace: {
        overview: { status: "loading" },
        dependencies: { status: "loading" },
      },
    }),
  );

  assert.match(loadingMarkup, /Loading Overview/);

  const restrictedMarkup = renderToStaticMarkup(
    React.createElement(ResilienceAvailabilityWindow, {
      initialWorkspace: {
        overview: { status: "restricted", data: null },
        dependencies: { status: "restricted", data: null },
      },
    }),
  );

  assert.match(restrictedMarkup, /Overview unavailable/);
  assert.match(restrictedMarkup, /Live operational counts and dependency posture from the backend\./);
});
