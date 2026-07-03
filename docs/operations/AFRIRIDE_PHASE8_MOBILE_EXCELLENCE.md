# Phase 8 — Mobile Excellence

## Runtime contract

Both Expo applications use one shared mobile-excellence runtime. It provides Material 3
surface and color semantics, Android 12+ dynamic primary color, system dark-mode
fallbacks, compact/medium/expanded window classes, and wide-foldable detection.

At 840 logical pixels the bottom navigation becomes a navigation rail. Wide foldable
postures use the same dual-pane layout, while compact and medium devices retain
bottom navigation. Content remains bounded to 1440 pixels on large displays.

## Accessibility and motion

- Interactive controls have a minimum 48-pixel target.
- Tabs expose tab roles and selected state; buttons expose disabled state.
- Loading and synchronization announcements use progressbar, alert, and live-region
  semantics.
- Screen transitions and skeleton shimmer stop when reduced motion is enabled.
- Text continues to use native font scaling.

## Offline-first and optimistic behavior

Ride requests and driver availability update immediately. Offline mutations are stored
in the existing durable operation queues and replayed after connectivity returns.
Optimistic identifiers are never polled as server identifiers. The sync banner shows
offline and pending-operation state without blocking navigation.

Server state remains authoritative: successful responses replace optimistic state,
online failures roll back, and the existing REST/realtime reconciliation path remains
unchanged.

## Release validation

Before release:

```bash
cd rider_app && npm run typecheck
cd ../driver_app && npm run typecheck
python -m pytest afriride_system/tests/test_phase8_mobile_excellence.py
```

Also export both Metro bundles and test portrait, landscape, tablet, font scaling,
screen reader, reduced motion, dark mode, and offline-to-online recovery on devices.
