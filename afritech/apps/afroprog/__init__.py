"""AfriPro codex-style developer workspace surfaces."""

from .chat.ai_service import (
    AfriProAIService,
    ChatWorkspaceResponse,
)
from .dashboard.views import (
    render_afroprog_dashboard_view,
)

__all__ = [
    "AfriProAIService",
    "ChatWorkspaceResponse",
    "render_afroprog_dashboard_view",
]
