"""AfriPay API routes."""

from __future__ import annotations

from django.urls import path

from afriride_system.django_app.apps.afripay import views


urlpatterns = [
    path("auth/oauth/token", views.oauth_token_view),
    path("auth/api-keys", views.api_key_issue_view),
    path("payments", views.payment_create_view),
    path("payments/<str:reference>", views.payment_detail_view),
    path("fx/quote", views.fx_quote_view),
    path("wallets/<str:wallet_id>", views.wallet_detail_view),
    path("treasury/pools", views.treasury_pools_view),
    path("events/<str:aggregate_id>", views.event_replay_view),
    path("escrows", views.escrow_create_view),
    path("escrows/<str:escrow_id>/release", views.escrow_release_view),
    path("payouts", views.payout_create_view),
    path("webhooks/<str:provider>", views.webhook_view),
    path("providers/flutterwave/test/transfer", views.flutterwave_sandbox_transfer_view),
    path("providers/mpesa/test/stk-push", views.mpesa_sandbox_stk_push_view),
    path("metrics", views.metrics_json_view),
    path("metrics/prometheus", views.metrics_prometheus_view),
    path("alerts", views.alerts_view),
]
