from __future__ import annotations

import re
from typing import Optional

PRICE_PATTERN = re.compile(r"([0-9][0-9,]*)\s*원")


def normalize_ws(value: str) -> str:
    return " ".join((value or "").split())


def looks_like_lp(title: str) -> bool:
    upper_title = (title or "").upper()
    return ("LP" in upper_title) or ("VINYL" in upper_title) or ("바이닐" in title)


def parse_price(value: str) -> Optional[int]:
    price_match = PRICE_PATTERN.search(normalize_ws(value))
    if not price_match:
        return None
    return int(price_match.group(1).replace(",", ""))
