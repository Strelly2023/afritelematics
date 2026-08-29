from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import Request

from afritech.novaride_runtime.replay.postgres_repository import PostgresReplayRepository
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository
from afritech.novaride_runtime.replay.service import (
    ReplayEventSource,
    ReplayService,
)
from afritech.novaride_runtime.replay.postgres_event_source import (
    TenantScopedPostgresReplayEventSource,
)


def build_default_replay_repository() -> ReplayPlanRepository:
    configured_path = os.environ.get("NOVARIDE_REPLAY_DB_PATH")
    if configured_path:
        db_path = Path(configured_path)
    else:
        environment = os.environ.get("AFRITECH_ENV", "development").lower()
        if environment in {"production", "prod"}:
            db_path = Path("var/novaride-runtime-replay.sqlite3")
        else:
            db_path = Path(tempfile.gettempdir()) / f"novaride-runtime-replay-{uuid4().hex}.sqlite3"
    return PostgresReplayRepository(db_path)


def build_production_replay_repository():
    """Compose production replay control state onto PostgreSQL.

    Selection creates no connection. Each repository method opens its
    own tenant-scoped runtime session through the long-lived session
    factory.
    """
    from afritech.novaride_runtime.replay.postgres_repository_facade import (
        TenantScopedPostgresReplayRepository,
    )

    from afritech.novaride_runtime.config import (
        NovaRideRuntimeSettings,
    )
    from afritech.novaride_runtime.persistence.runtime_selection import (
        PostgresRuntimeSelection,
        select_runtime_persistence,
    )

    settings = NovaRideRuntimeSettings.from_env()
    selection = select_runtime_persistence(settings)

    if not isinstance(
        selection,
        PostgresRuntimeSelection,
    ):
        raise RuntimeError(
            "production_replay_postgres_selection_required"
        )

    return TenantScopedPostgresReplayRepository(
        selection.session_factory
    )


def build_production_replay_event_source():
    """Compose production replay onto the certified PostgreSQL authority.

    Persistence selection creates no database connection. Each replay
    lookup opens its own tenant-scoped PostgresRuntimeSession.
    """
    from afritech.novaride_runtime.config import (
        NovaRideRuntimeSettings,
    )
    from afritech.novaride_runtime.persistence.runtime_selection import (
        PostgresRuntimeSelection,
        select_runtime_persistence,
    )

    settings = NovaRideRuntimeSettings.from_env()
    selection = select_runtime_persistence(settings)

    if not isinstance(
        selection,
        PostgresRuntimeSelection,
    ):
        raise RuntimeError(
            "production_replay_postgres_selection_required"
        )

    return TenantScopedPostgresReplayEventSource(
        selection.session_factory
    )


def get_replay_plan_repository(request: Request) -> ReplayPlanRepository:
    repository = getattr(request.app.state, "novaride_replay_repository", None)
    if repository is None:
        raise RuntimeError("novaride_replay_repository_not_configured")
    return repository


def get_replay_event_source(
    request: Request,
) -> ReplayEventSource:
    event_source = getattr(
        request.app.state,
        "novaride_replay_event_source",
        None,
    )

    if event_source is not None:
        return event_source

    environment = os.environ.get(
        "NOVARIDE_ENVIRONMENT",
        os.environ.get(
            "AFRITECH_ENV",
            "development",
        ),
    ).strip().lower()

    if environment in {"production", "prod"}:
        raise RuntimeError(
            "novaride_replay_event_source_not_configured"
        )

    # Non-production fallback only.
    #
    # Reuse the canonical in-process NovaRide runtime that the
    # development/test API already operates. Import lazily to avoid
    # creating a module-import cycle between API composition and replay
    # dependency declaration.
    from afritech.api.novaride_runtime_api import (
        get_novaride_runtime,
    )

    runtime = get_novaride_runtime()

    return runtime.repositories.events


def get_replay_service(request: Request) -> ReplayService:
    return ReplayService(
        get_replay_plan_repository(request),
        event_source=get_replay_event_source(request),
    )
