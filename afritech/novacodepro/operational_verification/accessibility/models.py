from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessibilityRunConfig:
    routes: tuple[str, ...]
    browsers: tuple[str, ...] = ("chromium", "firefox", "webkit")
    viewports: tuple[str, ...] = ("mobile", "tablet", "desktop")
    themes: tuple[str, ...] = ("light", "dark")
    wcag_level: str = "AA"


@dataclass(frozen=True, slots=True)
class AccessibilityResult:
    configured: bool
    executed: bool
    verified: bool
    wcag_level: str
    critical_violations: int
    serious_violations: int
    keyboard_navigation: str
    focus_visibility: str
    screen_reader_automated_baseline: str
    screen_reader_human_validation: str
