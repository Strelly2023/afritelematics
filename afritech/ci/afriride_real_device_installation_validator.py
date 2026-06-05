from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/pilot/AFRIRIDE_REAL_DEVICE_INSTALLATION_PATH.md",
    "docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md",
    "afriride_system/flutter/driver_app/pubspec.yaml",
    "afriride_system/flutter/rider_app/pubspec.yaml",
)

REQUIRED_TEXT = (
    "live_pilot_authorized = false",
    "flutter build apk --release",
    "adb install -r",
    "GET https://afriride-api.onrender.com/health = 200 OK",
    "driver_phone_001",
    "rider_phone_001",
    "operator_laptop_001",
    "Public production release is not authorized",
)


def validate() -> bool:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"missing real-device installation files: {missing}")

    text = (ROOT / "docs/pilot/AFRIRIDE_REAL_DEVICE_INSTALLATION_PATH.md").read_text(
        encoding="utf-8"
    )
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing real-device install text: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRIRIDE_REAL_DEVICE_INSTALLATION_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
