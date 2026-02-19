# watch_lp.py
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

# =========================
# Config
# =========================
WEBHOOK_URL = os.environ.get("LPICK_WEBHOOK_URL", "").strip()
if not WEBHOOK_URL:
    raise RuntimeError(
        "LPICK_WEBHOOK_URL 환경변수가 비어있습니다.\n"
    )

STATE_PATH = Path("seen_urls.json")

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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LPICK-WATCHER/1.0; +https://www.lpick.shop)",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

# 서버 부담/차단 방지용 딜레이
REQUEST_DELAY_SEC = 1.0


# =========================
# Models
# =========================
@dataclass(frozen=True)
class FoundItem:
    artist: str
    album: str
    store: str
    url: str


# =========================
# State (duplicate guard)
# =========================
def load_seen() -> set[str]:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(map(str, data))
        except Exception:
            pass
    return set()


def save_seen(seen: set[str]) -> None:
    STATE_PATH.write_text(
        json.dumps(sorted(seen), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# =========================
# Sheet push
# =========================
def push_to_sheet(item: FoundItem) -> None:
    payload = {
        "status": "TODO",
        "artist": item.artist,
        "album": item.album,
        "store": item.store,
        "url": item.url,
        "price": "",        # 지금 단계: 비움(사람이 확인 후 입력)
        "saleStatus": "",   # 지금 단계: 비움(예약/판매중/품절은 사람이 보강)
        "memo": "자동 감지",
    }

    r = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=20,
        headers=HEADERS,
        allow_redirects=True,
    )
    r.raise_for_status()


# =========================
# Helpers
# =========================
def get_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def normalize_ws(s: str) -> str:
    return " ".join((s or "").split())


def looks_like_lp(title: str) -> bool:
    t = (title or "").upper()
    # 너무 강하게 걸면 누락이 커져서 MVP용은 최소 조건만
    return ("LP" in t) or ("VINYL" in t) or ("바이닐" in title)


# =========================
# Site parsers (heuristic)
# =========================
def fetch_aladin(artist: str) -> List[FoundItem]:
    q = quote_plus(artist)
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=All&SearchWord={q}"

    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")

    items: List[FoundItem] = []

    # 상품 링크는 보통 wproduct.aspx?ItemId= 형태
    for a in soup.select("a[href*='wproduct.aspx?ItemId=']"):
        title = normalize_ws(a.get_text(" ", strip=True))
        href = a.get("href") or ""
        full = urljoin("https://www.aladin.co.kr", href)

        if not title or not full:
            continue
        if not looks_like_lp(title):
            continue

        items.append(FoundItem(artist=artist, album=title, store="알라딘", url=full))

    # URL 기준 중복 제거
    uniq = {}
    for it in items:
        uniq[it.url] = it
    return list(uniq.values())


def fetch_yes24(artist: str) -> List[FoundItem]:
    q = quote_plus(artist)
    url = f"https://www.yes24.com/Product/Search?query={q}"

    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")

    items: List[FoundItem] = []

    for a in soup.select("a[href^='/Product/Goods/']"):
        title = normalize_ws(a.get_text(" ", strip=True))
        href = a.get("href") or ""
        full = urljoin("https://www.yes24.com", href)

        if not title or not full:
            continue
        if len(title) < 2:
            continue
        if not looks_like_lp(title):
            continue

        items.append(FoundItem(artist=artist, album=title, store="YES24", url=full))

    uniq = {}
    for it in items:
        uniq[it.url] = it
    return list(uniq.values())


def fetch_hottracks(artist: str) -> List[FoundItem]:
    q = quote_plus(artist)
    url = f"https://hottracks.kyobobook.co.kr/search?searchKeyword={q}"

    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")

    items: List[FoundItem] = []

    # 핫트랙스는 /products/ 또는 /product/ 링크가 섞여 나오는 경우가 많음
    for a in soup.select("a[href*='/products/'], a[href*='/product/']"):
        title = normalize_ws(a.get_text(" ", strip=True))
        href = a.get("href") or ""
        full = urljoin("https://hottracks.kyobobook.co.kr", href)

        if not title or not full:
            continue
        if len(title) < 2:
            continue
        if not looks_like_lp(title):
            continue

        items.append(FoundItem(artist=artist, album=title, store="핫트랙스", url=full))

    uniq = {}
    for it in items:
        uniq[it.url] = it
    return list(uniq.values())


# =========================
# Runner
# =========================
def collect_all(artist: str) -> List[FoundItem]:
    results: List[FoundItem] = []
    for fn in (fetch_aladin, fetch_yes24, fetch_hottracks):
        try:
            results.extend(fn(artist))
        except Exception as e:
            print(f"[WARN] {fn.__name__} failed for '{artist}': {e}")
        time.sleep(REQUEST_DELAY_SEC)
    return results


def main() -> None:
    seen = load_seen()
    pushed = 0

    for artist in ARTISTS:
        found = collect_all(artist)
        new_items = [it for it in found if it.url not in seen]

        if not new_items:
            print(f"[OK] {artist}: no new items")
            continue

        print(f"[NEW] {artist}: {len(new_items)} items")
        for it in new_items:
            try:
                push_to_sheet(it)
                seen.add(it.url)
                pushed += 1
                print(f"  + {it.store} | {it.album} | {it.url}")
            except Exception as e:
                # push 실패하면 seen에 추가하지 않음(다음 실행 때 재시도)
                print(f"[ERROR] push failed: {e}")
            time.sleep(0.5)

        time.sleep(REQUEST_DELAY_SEC)

    save_seen(seen)
    print(f"\n[DONE] total new pushed: {pushed}")


if __name__ == "__main__":
    main()
