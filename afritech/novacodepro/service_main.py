from __future__ import annotations

import argparse

from afritech.novacodepro import processes
from afritech.novacodepro.service_registry import get_service_definition, service_definition_map


def create_service_app(service_name: str):
    definition = get_service_definition(service_name)
    return getattr(processes, definition.app_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a NovaCodePro independent service process")
    parser.add_argument("service_name", choices=sorted(service_definition_map().keys()))
    args = parser.parse_args()
    app = create_service_app(args.service_name)
    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(f"uvicorn is required to launch NovaCodePro services: {exc}") from exc
    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()
