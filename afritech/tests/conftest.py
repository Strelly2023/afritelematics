from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DJANGO_APP = ROOT / "afriride_system/django_app"

if str(DJANGO_APP) not in sys.path:
    sys.path.insert(0, str(DJANGO_APP))
