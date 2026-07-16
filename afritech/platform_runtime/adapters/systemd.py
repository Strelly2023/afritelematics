"""Systemd deployment adapter."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class SystemdDeploymentAdapter:
    unit_name: str
    name: str = "systemd"
    kind: str = "deployment"

    async def validate(self) -> dict[str, Any]:
        completed = await asyncio.to_thread(subprocess.run, ["systemctl", "status", self.unit_name, "--no-pager"], capture_output=True, text=True)
        return {"mode": "REAL" if completed.returncode == 0 else "UNAVAILABLE", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}

