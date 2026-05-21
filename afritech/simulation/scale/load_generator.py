from __future__ import annotations

import random
from typing import Any


class LoadGenerator:
    def generate(self, num_requests: int, *, seed: int) -> tuple[dict[str, Any], ...]:
        if num_requests < 0:
            raise ValueError("num_requests must be non-negative")

        rng = random.Random(int(seed))
        return tuple(
            {
                "ride_id": f"ride-{index:08d}",
                "user_id": f"user-{rng.randint(1, 10000):05d}",
                "sequence": index,
            }
            for index in range(num_requests)
        )
