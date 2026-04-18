from urllib.parse import quote_plus

from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsers import build_found_items


def fetch(artist: str) -> list[FoundItem]:
    query = quote_plus(artist)
    url = f"https://hottracks.kyobobook.co.kr/search?searchKeyword={query}"
    html = get_html(url)
    return build_found_items(
        html=html,
        artist=artist,
        store_slug="hottracks",
        store_name="핫트랙스",
        base_url="https://hottracks.kyobobook.co.kr",
        selector="a[href*='/products/'], a[href*='/product/']",
        min_title_length=2,
    )
