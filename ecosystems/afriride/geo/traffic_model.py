from __future__ import annotations

import hashlib
import random


class TrafficModel:
    def delay(self, segment_id: str, base_time: int, *, seed: int) -> int:
        digest = hashlib.sha256(f"{segment_id}:{int(seed)}".encode()).hexdigest()
        rng = random.Random(int(digest[:16], 16))
        return int(base_time) + rng.randint(0, 120)
