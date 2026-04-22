from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from lpick_watcher.config import ALADIN_CATEGORY_URL
from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsers import looks_like_lp, normalize_ws, parse_price

STORE_SLUG = "aladin"
STORE_NAME = "알라딘"

ALBUM_TRAILING_NOTE_PATTERN = re.compile(r"\s+-\s+.*$")
ALBUM_TAG_PATTERN = re.compile(r"\s*\[[^\]]*\]")
ALBUM_PAREN_PATTERN = re.compile(r"\s*\([^\)]*\)")
ALBUM_PREFIX_PATTERN = re.compile(r"^(?:정규|싱글|미니|EP)\s*\d+집\s+", re.IGNORECASE)
UNAVAILABLE_MARKERS = (
    "예약판매가 종료되었습니다",
    "예약 판매 종료",
    "품절",
    "절판",
    "유통이 중단되어 구할 수 없습니다",
)


def _extract_artist(raw_title: str, artist_text: str) -> str:
    metadata_artist = normalize_ws(artist_text)
    metadata_artist = metadata_artist.removesuffix(" 노래").strip()
    if metadata_artist:
        return metadata_artist

    title_artist, _, _ = raw_title.partition(" - ")
    return normalize_ws(title_artist) or STORE_NAME


def _extract_album(raw_title: str) -> str:
    _, separator, album = raw_title.partition(" - ")
    target = album if separator else raw_title
    target = ALBUM_TRAILING_NOTE_PATTERN.sub("", target)
    target = ALBUM_TAG_PATTERN.sub("", target)
    target = ALBUM_PAREN_PATTERN.sub("", target)
    target = ALBUM_PREFIX_PATTERN.sub("", target)
    return normalize_ws(target)


def fetch() -> list[FoundItem]:
    html = get_html(ALADIN_CATEGORY_URL)
    soup = BeautifulSoup(html, "lxml")
    items_by_url: dict[str, FoundItem] = {}

    for product_box in soup.select("div.ss_book_box[itemid]"):
        raw_title = ""
        href = ""

        try:
            box_text = normalize_ws(product_box.get_text(" ", strip=True))
            if any(marker in box_text for marker in UNAVAILABLE_MARKERS):
                continue

            title_link = product_box.select_one("a.bo3[href*='wproduct.aspx?ItemId=']")
            if title_link is None:
                continue

            raw_title = normalize_ws(title_link.get_text(" ", strip=True))
            href_value = title_link.get("href")
            href = href_value if isinstance(href_value, str) else ""
            if not raw_title or not href:
                continue
            if not looks_like_lp(raw_title):
                continue

            artist_link = product_box.select_one("a[href*='AuthorSearch=']")
            artist_text = normalize_ws(artist_link.get_text(" ", strip=True)) if artist_link else ""

            artist = _extract_artist(raw_title, artist_text)
            album = _extract_album(raw_title)
            full_url = urljoin("https://www.aladin.co.kr", href)

            image = product_box.select_one("img.i_cover")
            image_url = ""
            if image is not None:
                src = image.get("src") or ""
                if isinstance(src, str) and src:
                    image_url = urljoin("https://www.aladin.co.kr", src)

            price = parse_price(box_text)

            items_by_url[full_url] = FoundItem(
                artist=artist,
                album=album,
                store_slug=STORE_SLUG,
                store_name=STORE_NAME,
                source_product_title=raw_title,
                url=full_url,
                price=price,
                cover_image_url=image_url or None,
            )
        except Exception as error:
            error_url = urljoin("https://www.aladin.co.kr", href) if href else "(url 없음)"
            error_title = raw_title or "(title 없음)"
            print(
                f"[WARN] parse failed: store='{STORE_SLUG}' title='{error_title}' url='{error_url}' error={error}"
            )
            continue

    return list(items_by_url.values())
