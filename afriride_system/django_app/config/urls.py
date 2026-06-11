# afriride_system/django_app/config/urls.py

from django.urls import include, path

from afritech.api import afriride_driver_views as driver_views
from afritech.api.trust_kernel_views import verify_event_view
from afritech.api.trust_graph_views import (
    governance_pending_requests_view,
    governance_rollback_view,
    governance_rule_save_view,
    governance_rule_submit_view,
    governance_rules_view,
    governance_vote_view,
    governance_votes_view,
    proof_certificate_view,
    risk_scores_view,
    rule_dependency_add_view,
    rule_graph_view,
    rule_impact_view,
    trust_conversation_view,
    trust_converse_view,
    trust_graph_view,
    trust_history_view,
    trust_node_view,
    trust_process_view,
    trust_simulate_view,
)


def resolve_view(*names: str):
    for name in names:
        view = getattr(driver_views, name, None)
        if view is not None:
            return view

    joined = ", ".join(names)
    raise ImportError(
        f"None of these views exist in afritech.api.afriride_driver_views: {joined}"
    )


api_root = resolve_view("api_root")
health = resolve_view("health")
driver_availability = resolve_view("driver_availability")
driver_status = resolve_view("driver_status")
driver_queue = resolve_view("driver_queue")
driver_replay_history = resolve_view("driver_replay_history")

driver_earnings = resolve_view(
    "driver_earnings",
    "get_driver_earnings",
    "driver_earnings_view",
)

active_rides = resolve_view(
    "active_rides",
    "rides_active",
    "active_rides_view",
)

replay_health = resolve_view("replay_health")
evidence_pipeline = resolve_view("evidence_pipeline")
evidence_pipeline_summary = resolve_view("evidence_pipeline_summary")
pilot_evidence = resolve_view("pilot_evidence")
pilot_metrics = resolve_view("pilot_metrics")
pilot_readiness = resolve_view("pilot_readiness")
guard_violations = resolve_view("guard_violations")
guard_violations_summary = resolve_view("guard_violations_summary")

ride_accept = resolve_view("ride_accept")
ride_reject = resolve_view("ride_reject")
ride_arrive = resolve_view("ride_arrive")
ride_start = resolve_view("ride_start")
ride_complete = resolve_view("ride_complete")


urlpatterns = [
    path("", api_root),
    path("health", health),

    # ✅ include API modules
    path("api/", include("afritech.api.urls")),
    path("api/blockchain/", include("blockchain.urls")),

    # ✅ verification
    path("verify/<uuid:event_id>", verify_event_view),

    # ✅ driver endpoints
    path("driver/availability", driver_availability),
    path("driver/status", driver_status),
    path("driver/<str:driver_id>/queue", driver_queue),
    path("driver/<str:driver_id>/earnings", driver_earnings),
    path("driver/replay-history", driver_replay_history),

    # ✅ rides
    path("rides/active", active_rides),
    path("ride/<str:ride_id>/accept", ride_accept),
    path("ride/<str:ride_id>/reject", ride_reject),
    path("ride/arrive", ride_arrive),
    path("ride/<str:ride_id>/start", ride_start),
    path("ride/<str:ride_id>/complete", ride_complete),

    # ✅ system + evidence
    path("system/replay/health", replay_health),
    path("system/evidence", evidence_pipeline),
    path("system/evidence/summary", evidence_pipeline_summary),

    # ✅ pilot
    path("pilot/evidence", pilot_evidence),
    path("pilot/metrics", pilot_metrics),
    path("pilot/readiness", pilot_readiness),

    # ✅ guards
    path("system/guards", guard_violations),
    path("system/guards/summary", guard_violations_summary),

    # ✅ trust graph
    path("trust/graph", trust_graph_view),
    path("trust/history", trust_history_view),
    path("trust/node/<str:node_id>", trust_node_view),
    path("trust/process", trust_process_view),
    path("trust/conversation", trust_conversation_view),
    path("trust/converse", trust_converse_view),
    path("trust/simulate", trust_simulate_view),

    # ✅ governance
    path("trust/rules", governance_rules_view),
    path("trust/rules/save", governance_rule_save_view),
    path("trust/rules/<str:version_id>/submit", governance_rule_submit_view),
    path("trust/change-requests/pending", governance_pending_requests_view),
    path("trust/change-requests/<str:request_id>/vote", governance_vote_view),
    path("trust/change-requests/<str:request_id>/votes", governance_votes_view),
    path("trust/rules/<str:rule_name>/rollback", governance_rollback_view),

    # ✅ rule graph + impact
    path("trust/rule-graph", rule_graph_view),
    path("trust/rule-graph/dependency", rule_dependency_add_view),
    path("trust/impact/<str:rule_name>", rule_impact_view),

    # ✅ risk + proof
    path("trust/risk", risk_scores_view),
    path("trust/proof/<str:proposal_id>", proof_certificate_view),
]