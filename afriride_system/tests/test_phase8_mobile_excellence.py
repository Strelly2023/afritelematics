from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shared_material_adaptive_runtime_covers_device_classes() -> None:
    source = read("afriride_system/mobile/shared/mobileExcellence.js")
    assert "PlatformColor" in source
    assert "system_accent1_600" in source
    assert 'width >= 840 ? "expanded" : width >= 600 ? "medium" : "compact"' in source
    assert "isFoldablePosture" in source
    assert "navigationRail" in source
    assert "Appearance.addChangeListener" in source


def test_motion_loading_and_sync_respect_accessibility_and_offline_state() -> None:
    source = read("afriride_system/mobile/shared/mobileExcellence.js")
    assert "AccessibilityInfo.isReduceMotionEnabled" in source
    assert "reduceMotionChanged" in source
    assert "useNativeDriver: true" in source
    assert 'accessibilityRole="progressbar"' in source
    assert 'accessibilityLiveRegion="polite"' in source
    for app in ("rider_app/App.tsx", "driver_app/App.tsx"):
        app_source = read(app)
        assert "<AdaptiveScaffold" in app_source
        assert "<AnimatedEntrance>" in app_source
        assert "<SkeletonBlock" in app_source
        assert "<SyncBanner" in app_source
        assert "navigation={" in app_source


def test_mobile_navigation_and_controls_are_accessible_and_adaptive() -> None:
    for app in ("rider_app", "driver_app"):
        tabs = read(f"{app}/ui/widgets/BottomTabs.tsx")
        button = read(f"{app}/ui/widgets/PrimaryButton.tsx")
        assert 'accessibilityRole="tablist"' in tabs
        assert 'accessibilityRole="tab"' in tabs
        assert "selected: active" in tabs
        assert "useWindowDimensions().width >= 840" in tabs
        assert "minHeight: 48" in tabs
        assert 'accessibilityRole="button"' in button
        assert "useMobileExcellence" in button
        assert "theme.primary" in button


def test_rider_and_driver_keep_optimistic_offline_operations() -> None:
    rider = read("rider_app/state/providers/useRideFlow.ts")
    driver = read("driver_app/state/providers/useDriverFlow.ts")
    assert "optimistic-${Date.now()}" in rider
    assert "enqueueRiderOperation" in rider
    assert "network.isConnected" in rider
    assert "queueDriverOperation" in driver
    assert "availability: current.availability || previous" in driver
    assert "requests: current.requests.filter((request) => request.rideId !== rideId)" in driver


def test_bundlers_watch_the_single_shared_mobile_runtime() -> None:
    for app in ("rider_app", "driver_app"):
        metro = read(f"{app}/metro.config.js")
        assert "watchFolders" in metro
        assert "afriride_system" in metro
