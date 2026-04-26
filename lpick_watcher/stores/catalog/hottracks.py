from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from lpick_watcher.config import HEADERS, HOTTRACKS_CATEGORY_URL
from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsers import normalize_ws

import requests

STORE_SLUG = "hottracks"
STORE_NAME = "핫트랙스"
HOTTRACKS_LIST_API_URL = "https://hottracks.kyobobook.co.kr/api/gw/hotf/recordSub/lp"
DETAIL_URL_PREFIX = "https://hottracks.kyobobook.co.kr/p/"
ARTIST_KO_PAREN_PATTERN = re.compile(r"^[A-Za-z0-9 .&'\-/]+\(([가-힣0-9 .&'\-/]+)\)$")
ALBUM_TAG_PATTERN = re.compile(r"\s*\[[^\]]*\]")
ALBUM_PAREN_PATTERN = re.compile(r"\s*\([^\)]*\)")
ALBUM_PREFIX_PATTERN = re.compile(r"^(?:정규|싱글|미니|EP|소품집)\s*\d+집\s+", re.IGNORECASE)


def _parse_query_params() -> dict[str, str]:
    parsed = urlparse(HOTTRACKS_CATEGORY_URL)
    query = parse_qs(parsed.query)
    path_parts = [part for part in parsed.path.split("/") if part]
    category_code = path_parts[-1] if len(path_parts) >= 3 and path_parts[-2] == "lp" else ""
    filters = {
        value.strip().lower()
        for raw_value in query.get("filter", [])
        for value in raw_value.split(",")
        if value.strip()
    }

    params = {
        "per": "48",
        "page": query.get("page", ["1"])[0] or "1",
        "sort": query.get("sort", ["R"])[0] or "R",
        "cpYn": "Y" if "coupon" in filters else "N",
        "dcYn": "Y" if "discount" in filters else "N",
        "saleYn": "Y" if "soldout" in filters else "N",
        "saleCmdtClstCode": category_code,
        "termDvsnCode": "002",
    }

    if "mucdo" in filters:
        params["imprYsno"] = "N"
    elif "mucim" in filters:
        params["imprYsno"] = "Y"

    return params


def _extract_album(raw_title: str) -> str:
    target = ALBUM_TAG_PATTERN.sub("", raw_title)
    target = ALBUM_PAREN_PATTERN.sub("", target)
    target = ALBUM_PREFIX_PATTERN.sub("", target)
    return normalize_ws(target).replace("O.S.T", "OST")


def _extract_artist(raw_artist: str) -> str:
    normalized = normalize_ws(raw_artist).replace("O.S.T", "OST")
    korean_paren_match = ARTIST_KO_PAREN_PATTERN.match(normalized)
    if korean_paren_match:
        return normalize_ws(korean_paren_match.group(1))
    return normalized


def _build_detail_url(sale_cmdt_id: str) -> str:
    return urljoin(DETAIL_URL_PREFIX, sale_cmdt_id)


def _extract_cover_image_url(detail_url: str) -> str | None:
    try:
        html = get_html(detail_url)
    except Exception:
        return None

    match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html, re.IGNORECASE)
    if not match:
        return None
    image_url = normalize_ws(match.group(1))
    return image_url or None


def fetch() -> list[FoundItem]:
    response = requests.get(
        HOTTRACKS_LIST_API_URL,
        params=_parse_query_params(),
        headers={**HEADERS, "Accept": "application/json, text/plain, */*", "Referer": HOTTRACKS_CATEGORY_URL},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    tab_contents = payload.get("data", {}).get("tabContents", [])

    items_by_url: dict[str, FoundItem] = {}
    for product in tab_contents:
        raw_title = normalize_ws(str(product.get("cmdtName") or ""))
        artist = _extract_artist(str(product.get("artistName") or "")) or STORE_NAME
        sale_cmdt_id = normalize_ws(str(product.get("saleCmdtId") or ""))
        if not raw_title or not sale_cmdt_id:
            continue

        detail_url = _build_detail_url(sale_cmdt_id)
        items_by_url[detail_url] = FoundItem(
            artist=artist,
            album=_extract_album(raw_title),
            store_slug=STORE_SLUG,
            store_name=STORE_NAME,
            source_product_title=raw_title,
            url=detail_url,
            price=product.get("price") if isinstance(product.get("price"), int) else None,
            cover_image_url=_extract_cover_image_url(detail_url),
        )

    return list(items_by_url.values())
