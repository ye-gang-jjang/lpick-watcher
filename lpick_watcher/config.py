import os
from pathlib import Path


API_BASE_URL = os.environ.get("LPICK_API_BASE_URL", "http://localhost:8000").strip()
STATE_PATH = Path("seen_urls.json")
REQUEST_DELAY_SEC = 1.0
GIMBAB_CATEGORY_URL = os.environ.get(
    "LPICK_GIMBAB_CATEGORY_URL",
    "https://gimbabrecords.com/product/list.html?cate_no=52",
).strip()
GIMBAB_MAX_PAGES = int(os.environ.get("LPICK_GIMBAB_MAX_PAGES", "5"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LPICK-WATCHER/1.0; +https://www.lpick.shop)",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

DEFAULT_ARTISTS = [
    "김뜻돌",
    "새소년",
    "실리카겔",
    "잔나비",
    "혁오",
    "검정치마",
    "CHEEZE",
    "오혁",
    "장기하",
    "브로콜리너마저",
    "wave to earth",
    "죠지",
    "페퍼톤스",
    "스텔라장",
    "한로로",
    "소수빈",
    "빛과소금",
]


def parse_csv_env(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [value.strip() for value in raw.split(",") if value.strip()]


ARTISTS = parse_csv_env("LPICK_ARTISTS") or DEFAULT_ARTISTS
ENABLED_STORES = parse_csv_env("LPICK_ENABLED_STORES")
