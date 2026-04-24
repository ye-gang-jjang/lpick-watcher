from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from lpick_watcher.config import YES24_CATEGORY_URL
from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsers import looks_like_lp, normalize_ws, parse_price

STORE_SLUG = "yes24"
STORE_NAME = "YES24"

ALBUM_TRAILING_NOTE_PATTERN = re.compile(r"\s+-\s+.*$")
ALBUM_TAG_PATTERN = re.compile(r"\s*\[[^\]]*\]")
ALBUM_PAREN_PATTERN = re.compile(r"\s*\([^\)]*\)")
ALBUM_PREFIX_PATTERN = re.compile(r"^(?:정규|싱글|미니|EP|소품집)\s*\d+집\s+", re.IGNORECASE)
UNAVAILABLE_MARKERS = (
    "일시품절",
    "품절",
    "예약판매종료",
    "예약 판매 종료",
)


def _extract_artist(raw_title: str, artist_text: str) -> str:
    artist = normalize_ws(artist_text)
    artist = artist.removesuffix(" 노래").removesuffix(" 밴드").removesuffix(" 작곡").strip()
    if artist:
        return artist

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
    html = get_html(YES24_CATEGORY_URL)
    soup = BeautifulSoup(html, "lxml")
    items_by_url: dict[str, FoundItem] = {}

    for product_box in soup.select("div.itemUnit"):
        raw_title = ""
        href = ""

        try:
            box_text = normalize_ws(product_box.get_text(" ", strip=True))
            if any(marker in box_text for marker in UNAVAILABLE_MARKERS):
                continue

            title_link = product_box.select_one("div.info_name a.gd_name[href*='/product/goods/']")
            if title_link is None:
                continue

            raw_title = normalize_ws(title_link.get_text(" ", strip=True))
            href_value = title_link.get("href")
            href = href_value if isinstance(href_value, str) else ""
            if not raw_title or not href or not looks_like_lp(raw_title):
                continue

            artist_link = product_box.select_one("span.info_auth a")
            artist_text = normalize_ws(artist_link.get_text(" ", strip=True)) if artist_link else ""

            artist = _extract_artist(raw_title, artist_text)
            album = _extract_album(raw_title)
            full_url = urljoin("https://www.yes24.com", href)

            image = product_box.select_one("div.item_img img")
            image_url = ""
            if image is not None:
                src = image.get("data-original") or image.get("src") or ""
                if isinstance(src, str) and src:
                    image_url = urljoin("https://www.yes24.com", src)

            price_node = product_box.select_one("div.info_price strong.txt_num")
            price_text = normalize_ws(price_node.get_text(" ", strip=True)) if price_node is not None else ""
            price = parse_price(price_text)

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
            error_url = urljoin("https://www.yes24.com", href) if href else "(url 없음)"
            error_title = raw_title or "(title 없음)"
            print(
                f"[WARN] parse failed: store='{STORE_SLUG}' title='{error_title}' url='{error_url}' error={error}"
            )
            continue

    return list(items_by_url.values())
