from __future__ import annotations

import hashlib
from datetime import date


def pick_variant(day: date, seed: str = "seed") -> str:
    key = f"{day.isoformat()}::{seed}".encode()
    h = hashlib.sha256(key).hexdigest()
    return "A" if int(h[:2], 16) % 2 == 0 else "B"
