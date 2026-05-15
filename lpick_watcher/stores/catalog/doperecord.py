from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from lpick_watcher.config import DOPERECORD_CATEGORY_URL
from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsers import normalize_ws, parse_price

STORE_SLUG = "doperecord"
STORE_NAME = "도프레코드"

LEADING_TAG_PATTERN = re.compile(r"^(?:\[[^\]]+\]\s*)+")
ARTIST_KO_FIRST_PAREN_PATTERN = re.compile(r"^([가-힣0-9 .&'\-/]+)\s*\([A-Za-z0-9 .&'\-/]+\)$")
ARTIST_KO_LAST_PAREN_PATTERN = re.compile(r"^[A-Za-z0-9 .&'\-/]+\s*\(([가-힣0-9 .&'\-/]+)\)$")
ARTIST_KO_THEN_EN_PATTERN = re.compile(r"^([가-힣0-9 .&'\-/]+)\s+[A-Za-z].*$")
ARTIST_EN_THEN_KO_PATTERN = re.compile(r"^([A-Za-z0-9 .&'\-/]+)\s+[가-힣].*$")
TITLE_SPLIT_PATTERN = re.compile(r"\s*[\-–—]\s*")
ANGLE_BRACKET_PATTERN = re.compile(r"^(.*?)\s*<([^>]+)>$")
ALBUM_TAG_PATTERN = re.compile(r"\s*\[[^\]]*\]")
ALBUM_PAREN_PATTERN = re.compile(r"\s*\([^\)]*\)")
ALBUM_PREFIX_PATTERN = re.compile(r"^(?:정규|싱글|미니|EP|소품집)\s*\d+집\s+", re.IGNORECASE)
ALBUM_TYPE_PREFIX_PATTERN = re.compile(r"^(?:EP앨범|정규앨범|싱글앨범|미니앨범)\s+", re.IGNORECASE)
ALBUM_EDITION_PATTERN = re.compile(r"\s+\d+(?:ST|ND|RD|TH)\s+ANNIVERSARY\s+EDITION$", re.IGNORECASE)
LP_INCLUDE_PATTERNS = (
    ' lp',
    'lp]',
    'lp)',
    'vinyl',
    '7"',
    '12"',
)
NON_LP_EXCLUDE_PATTERNS = (
    '[cd]',
    ' cassette',
    '[cassette]',
)


def _strip_leading_tags(raw_title: str) -> str:
    return normalize_ws(LEADING_TAG_PATTERN.sub("", raw_title))


def _looks_like_lp(raw_title: str) -> bool:
    lowered = raw_title.lower()
    if any(pattern in lowered for pattern in LP_INCLUDE_PATTERNS):
        return True
    if any(pattern in lowered for pattern in NON_LP_EXCLUDE_PATTERNS):
        return False
    return False


def _extract_artist(cleaned_title: str) -> str:
    parts = TITLE_SPLIT_PATTERN.split(cleaned_title, maxsplit=1)
    artist = normalize_ws(parts[0]) if len(parts) == 2 else ""

    if not artist:
        base_title = normalize_ws(ALBUM_TAG_PATTERN.sub("", ALBUM_PAREN_PATTERN.sub("", cleaned_title)))
        angle_match = ANGLE_BRACKET_PATTERN.match(base_title)
        artist = normalize_ws(angle_match.group(1)) if angle_match else ""

    if not artist:
        fallback = ALBUM_TAG_PATTERN.sub("", cleaned_title)
        fallback = normalize_ws(ALBUM_PAREN_PATTERN.sub("", fallback))
        return fallback or STORE_NAME

    korean_first_match = ARTIST_KO_FIRST_PAREN_PATTERN.match(artist)
    if korean_first_match:
        return normalize_ws(korean_first_match.group(1))

    korean_last_match = ARTIST_KO_LAST_PAREN_PATTERN.match(artist)
    if korean_last_match:
        return normalize_ws(korean_last_match.group(1))

    artist = ALBUM_PAREN_PATTERN.sub("", artist)
    ko_then_en_match = ARTIST_KO_THEN_EN_PATTERN.match(artist)
    if ko_then_en_match:
        artist = ko_then_en_match.group(1)
    else:
        en_then_ko_match = ARTIST_EN_THEN_KO_PATTERN.match(artist)
        if en_then_ko_match:
            artist = en_then_ko_match.group(1)
    return normalize_ws(artist) or STORE_NAME


def _extract_album(cleaned_title: str) -> str:
    parts = TITLE_SPLIT_PATTERN.split(cleaned_title, maxsplit=1)
    target = parts[1] if len(parts) == 2 else cleaned_title

    target = normalize_ws(ALBUM_TAG_PATTERN.sub("", target))
    target = normalize_ws(ALBUM_PAREN_PATTERN.sub("", target))

    angle_match = ANGLE_BRACKET_PATTERN.match(target)
    if angle_match:
        target = angle_match.group(2)

    target = ALBUM_TYPE_PREFIX_PATTERN.sub("", target)
    target = ALBUM_PREFIX_PATTERN.sub("", target)
    target = ALBUM_EDITION_PATTERN.sub("", target)
    return normalize_ws(target)


def fetch() -> list[FoundItem]:
    html = get_html(DOPERECORD_CATEGORY_URL)
    soup = BeautifulSoup(html, "lxml")
    items_by_url: dict[str, FoundItem] = {}

    for product_item in soup.select("li[id^='anchorBoxId_']"):
        raw_title = ""
        href = ""

        try:
            link = product_item.select_one("div.description .name a")
            if link is None:
                continue

            title_spans = link.select("span")
            if title_spans:
                raw_title = normalize_ws(title_spans[-1].get_text(" ", strip=True))
            else:
                raw_title = normalize_ws(link.get_text(" ", strip=True))
            href_value = link.get("href")
            href = href_value if isinstance(href_value, str) else ""
            if not raw_title or not href:
                continue

            cleaned_title = _strip_leading_tags(raw_title)
            if not _looks_like_lp(cleaned_title):
                continue

            artist = _extract_artist(cleaned_title)
            album = _extract_album(cleaned_title)
            full_url = urljoin("https://doperecord.com", href)

            image = product_item.select_one(".thumbnail img")
            image_url = ""
            if image is not None:
                src = image.get("src") or ""
                if isinstance(src, str) and src:
                    image_url = urljoin("https://doperecord.com", src)

            price_text = normalize_ws(product_item.get_text(" ", strip=True))
            price = parse_price(price_text)

            items_by_url[full_url] = FoundItem(
                artist=artist,
                album=album,
                store_slug=STORE_SLUG,
                store_name=STORE_NAME,
                source_product_title=cleaned_title,
                url=full_url,
                price=price,
                cover_image_url=image_url or None,
            )
        except Exception as error:
            error_url = urljoin("https://doperecord.com", href) if href else "(url 없음)"
            error_title = raw_title or "(title 없음)"
            print(
                f"[WARN] parse failed: store='{STORE_SLUG}' title='{error_title}' url='{error_url}' error={error}"
            )
            continue

    return list(items_by_url.values())
