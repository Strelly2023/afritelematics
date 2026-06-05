from __future__ import annotations

import sys
from pathlib import Path

from django.test import Client


ROOT = Path(__file__).resolve().parents[2]
DJANGO_APP = ROOT / "afriride_system/django_app"

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))


def test_verify_proof_browser_get_renders_method_not_allowed_without_template_error():
    response = Client(HTTP_ACCEPT="text/html").get("/api/verify-proof/")

    assert response.status_code == 405
    assert response["content-type"].startswith("text/html")
