import os
from pathlib import Path


API_BASE_URL = os.environ.get("LPICK_API_BASE_URL", "http://localhost:8000").strip()
STATE_PATH = Path("seen_urls.json")
REQUEST_DELAY_SEC = 1.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LPICK-WATCHER/1.0; +https://www.lpick.shop)",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

ARTISTS = [
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
