"""Declared Django-style routes for AfriPro."""

from __future__ import annotations


urlpatterns = (
    {
        "path": "/afroprog/dashboard/",
        "view": "afroprog_dashboard",
        "name": "afroprog-dashboard",
    },
    {
        "path": "/afroprog/chat/",
        "view": "afroprog_chat",
        "name": "afroprog-chat",
    },
    {
        "path": "/afroprog/projects/",
        "view": "afroprog_projects",
        "name": "afroprog-projects",
    },
)


__all__ = ["urlpatterns"]
