from __future__ import annotations

from .models import AccessibilityResult, AccessibilityRunConfig


def verify_accessibility(config: AccessibilityRunConfig, *, tools_ran: bool, critical: int = 0, serious: int = 0, keyboard: bool = True, focus: bool = True) -> AccessibilityResult:
    verified = bool(tools_ran and critical == 0 and serious == 0 and keyboard and focus)
    return AccessibilityResult(
        configured=bool(config.routes),
        executed=tools_ran,
        verified=verified,
        wcag_level=config.wcag_level,
        critical_violations=critical,
        serious_violations=serious,
        keyboard_navigation="PASS" if keyboard else "FAIL",
        focus_visibility="PASS" if focus else "FAIL",
        screen_reader_automated_baseline="PASS" if tools_ran else "PENDING",
        screen_reader_human_validation="PENDING",
    )
