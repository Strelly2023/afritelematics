from __future__ import annotations

from afritech.docs.document_system import validate_document_system


def main() -> int:
    failures = validate_document_system()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("NOVATECH_DOCUMENT_SYSTEM: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
