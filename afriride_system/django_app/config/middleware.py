from __future__ import annotations

from django.http import HttpResponse


AFRIRIDE_ALLOWED_HEADERS = (
    "Content-Type",
    "X-Client-Event-Id",
    "X-Client-Event-Hash",
    "X-Client-Event-Timestamp",
    "X-Client-Event-Sequence",
    "X-AfriRide-Device-Id",
    "X-AfriRide-App-Version",
    "X-AfriRide-Event-Id",
    "X-AfriRide-Client-Timestamp",
    "X-AfriRide-Test-Mode",
)


class DevelopmentCorsMiddleware:
    """Minimal local-development CORS support for browser-based driver app testing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = ", ".join(AFRIRIDE_ALLOWED_HEADERS)
        return response
