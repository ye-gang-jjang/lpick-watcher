from urllib.parse import quote_plus

from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsing import build_found_items


def fetch(artist: str) -> list[FoundItem]:
    query = quote_plus(artist)
    url = f"https://www.yes24.com/Product/Search?query={query}"
    html = get_html(url)
    return build_found_items(
        html=html,
        artist=artist,
        store_slug="yes24",
        store_name="YES24",
        base_url="https://www.yes24.com",
        selector="a[href^='/Product/Goods/']",
        min_title_length=2,
    )
