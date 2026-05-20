"""Side-effect-free command logging for the AfriRide API."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("afriride.api")


def log_command(command_name: str, payload: dict[str, Any]) -> None:
    logger.info("COMMAND %s %s", command_name, payload)


def log_result(command_name: str, result: dict[str, Any]) -> None:
    logger.info("RESULT %s %s", command_name, result)
