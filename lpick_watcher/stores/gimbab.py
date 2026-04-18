from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from lpick_watcher.config import GIMBAB_CATEGORY_URL, GIMBAB_MAX_PAGES
from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsers import normalize_ws, parse_price


TRAILING_NOTE_PATTERN = re.compile(r"\s*\*.*$")
PAREN_PATTERN = re.compile(r"\s*\([^\)]*\)")
ARTIST_KO_THEN_EN_PATTERN = re.compile(r"^([가-힣0-9 .&'\-]+)\s+[A-Za-z].*$")
ARTIST_EN_THEN_KO_PATTERN = re.compile(r"^([A-Za-z0-9 .&'\-]+)\s+[가-힣].*$")
ALBUM_PREFIX_PATTERN = re.compile(r"^(?:정규|싱글|미니|EP)\s*\d+집\s+", re.IGNORECASE)


def _build_page_url(page: int) -> str:
    parsed = urlparse(GIMBAB_CATEGORY_URL)
    query = parse_qs(parsed.query)
    query["page"] = [str(page)]
    encoded_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=encoded_query))


def _extract_artist_album(raw_title: str) -> tuple[str, str]:
    normalized = normalize_ws(raw_title)
    parts = normalized.split(" / ", 1)

    if len(parts) == 2:
        artist = normalize_ws(parts[0])
        album = normalize_ws(parts[1])
    else:
        artist = "김밥레코즈"
        album = normalized

    artist = PAREN_PATTERN.sub("", artist)
    has_korean = bool(re.search(r"[가-힣]", artist))
    has_english = bool(re.search(r"[A-Za-z]", artist))
    if has_korean and has_english:
        ko_then_en_match = ARTIST_KO_THEN_EN_PATTERN.match(artist)
        en_then_ko_match = ARTIST_EN_THEN_KO_PATTERN.match(artist)
        if ko_then_en_match:
            artist = ko_then_en_match.group(1)
        elif en_then_ko_match:
            artist = en_then_ko_match.group(1)
    artist = normalize_ws(artist)

    album = TRAILING_NOTE_PATTERN.sub("", album)
    album = ALBUM_PREFIX_PATTERN.sub("", album)
    album = PAREN_PATTERN.sub("", album)
    album = normalize_ws(album)
    return artist, album


def fetch() -> list[FoundItem]:
    items_by_url: dict[str, FoundItem] = {}

    for page in range(1, max(1, GIMBAB_MAX_PAGES) + 1):
        html = get_html(_build_page_url(page))
        soup = BeautifulSoup(html, "lxml")
        product_items = soup.select("ul.prdList > li[id^='anchorBoxId_']")

        if not product_items:
            break

        for product_item in product_items:
            raw_title = ""
            href = ""

            try:
                link = product_item.select_one("div.description .name a")
                if link is None:
                    continue

                raw_title = normalize_ws(link.get_text(" ", strip=True))
                href_value = link.get("href")
                href = href_value if isinstance(href_value, str) else ""
                if not raw_title or not href:
                    continue

                artist, album = _extract_artist_album(raw_title)
                full_url = urljoin("https://gimbabrecords.com", href)
                image = product_item.select_one(".thumbnail img")
                image_url = ""
                if image is not None:
                    src = image.get("src") or ""
                    if isinstance(src, str) and src:
                        image_url = urljoin("https://gimbabrecords.com", src)

                price_node = product_item.select_one(".spec li")
                price_text = ""
                if price_node is not None:
                    price_text = normalize_ws(price_node.get_text(" ", strip=True))
                price = parse_price(price_text)

                items_by_url[full_url] = FoundItem(
                    artist=artist,
                    album=album,
                    store_slug="gimbab",
                    store_name="김밥레코즈",
                    source_product_title=raw_title,
                    url=full_url,
                    price=price,
                    cover_image_url=image_url or None,
                )
            except Exception as error:
                error_href = href if isinstance(href, str) else ""
                error_url = urljoin("https://gimbabrecords.com", error_href) if error_href else "(url 없음)"
                error_title = raw_title or "(title 없음)"
                print(
                    f"[WARN] parse failed: store='gimbab' title='{error_title}' url='{error_url}' error={error}"
                )
                continue

    return list(items_by_url.values())
