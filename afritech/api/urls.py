from django.urls import path

from afritech.api.afriride_driver_views import (
    api_root,
    driver_availability,
    driver_earnings,
    driver_queue,
    driver_replay_history,
    driver_status,
    ride_accept,
    ride_arrive,
    ride_complete,
    ride_reject,
    ride_start,
)
from afritech.api.verification_views import (
    verify_proof_view,
    verify_log_proof_view,
)
from afritech.api.explain_execution_views import explain_execution_view
from afritech.api.trust_kernel_views import verify_event_view
from afritech.api.orchestration_views import (
    orchestration_abort_view,
    orchestration_detail_view,
    orchestration_list_view,
    orchestration_pause_view,
    orchestration_resume_view,
)

urlpatterns = [
    path("", api_root),
    path("driver/availability", driver_availability),
    path("driver/status", driver_status),
    path("driver/<str:driver_id>/queue", driver_queue),
    path("driver/<str:driver_id>/earnings", driver_earnings),
    path("driver/replay-history", driver_replay_history),
    path("ride/<str:ride_id>/accept", ride_accept),
    path("ride/<str:ride_id>/reject", ride_reject),
    path("ride/arrive", ride_arrive),
    path("ride/<str:ride_id>/start", ride_start),
    path("ride/<str:ride_id>/complete", ride_complete),
    path("verify-proof/", verify_proof_view),
    path("verify/<uuid:event_id>", verify_event_view),
    path("verify-log-proof/", verify_log_proof_view),
    path("execution/<str:execution_id>/explain/", explain_execution_view),
    path("orchestrations", orchestration_list_view),
    path("orchestrations/<str:orchestration_id>", orchestration_detail_view),
    path("orchestrations/<str:orchestration_id>/pause", orchestration_pause_view),
    path("orchestrations/<str:orchestration_id>/resume", orchestration_resume_view),
    path("orchestrations/<str:orchestration_id>/abort", orchestration_abort_view),
]
