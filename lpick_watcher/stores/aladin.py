from urllib.parse import quote_plus

from lpick_watcher.http import get_html
from lpick_watcher.models import FoundItem
from lpick_watcher.parsing import build_found_items


def fetch(artist: str) -> list[FoundItem]:
    query = quote_plus(artist)
    url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=All&SearchWord={query}"
    html = get_html(url)
    return build_found_items(
        html=html,
        artist=artist,
        store_slug="aladin",
        store_name="알라딘",
        base_url="https://www.aladin.co.kr",
        selector="a[href*='wproduct.aspx?ItemId=']",
    )
