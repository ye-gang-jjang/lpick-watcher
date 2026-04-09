from urllib.parse import urljoin

from bs4 import BeautifulSoup

from lpick_watcher.models import FoundItem


def normalize_ws(value: str) -> str:
    return " ".join((value or "").split())


def looks_like_lp(title: str) -> bool:
    upper_title = (title or "").upper()
    return ("LP" in upper_title) or ("VINYL" in upper_title) or ("바이닐" in title)


def build_found_items(
    *,
    html: str,
    artist: str,
    store_slug: str,
    store_name: str,
    base_url: str,
    selector: str,
    min_title_length: int = 0,
) -> list[FoundItem]:
    soup = BeautifulSoup(html, "lxml")
    items: list[FoundItem] = []

    for anchor in soup.select(selector):
        title = normalize_ws(anchor.get_text(" ", strip=True))
        href = anchor.get("href") or ""
        href_text = href if isinstance(href, str) else ""
        full_url = urljoin(base_url, href_text)

        if not title or not full_url:
            continue
        if len(title) < min_title_length:
            continue
        if not looks_like_lp(title):
            continue

        items.append(
            FoundItem(
                artist=artist,
                album=title,
                store_slug=store_slug,
                store_name=store_name,
                source_product_title=title,
                url=full_url,
            )
        )

    unique_items: dict[str, FoundItem] = {}
    for item in items:
        unique_items[item.url] = item

    return list(unique_items.values())
