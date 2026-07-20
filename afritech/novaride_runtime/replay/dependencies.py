from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import Request

from afritech.novaride_runtime.replay.postgres_repository import PostgresReplayRepository
from afritech.novaride_runtime.replay.repository import ReplayPlanRepository
from afritech.novaride_runtime.replay.service import ReplayService


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


def get_replay_plan_repository(request: Request) -> ReplayPlanRepository:
    repository = getattr(request.app.state, "novaride_replay_repository", None)
    if repository is None:
        raise RuntimeError("novaride_replay_repository_not_configured")
    return repository


def get_replay_service(request: Request) -> ReplayService:
    return ReplayService(get_replay_plan_repository(request))
