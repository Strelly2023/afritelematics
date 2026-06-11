"""WebSocket-like chat consumer for AfriPro."""

from __future__ import annotations

from .views import render_chat_view


class ChatConsumer:
    """Framework-light consumer that mirrors a real-time chat handler."""

    async def receive(self, text_data: str) -> dict[str, object]:
        return render_chat_view(prompt=text_data, mode="code")


__all__ = ["ChatConsumer"]
