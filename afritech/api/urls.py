from django.urls import path

from afritech.api.verification_views import (
    verify_proof_view,
    verify_log_proof_view,
)
from afritech.api.explain_execution_views import explain_execution_view

urlpatterns = [
    path("verify-proof/", verify_proof_view),
    path("verify-log-proof/", verify_log_proof_view),
    path("execution/<str:execution_id>/explain/", explain_execution_view),
]
