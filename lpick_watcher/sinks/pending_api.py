import requests

from lpick_watcher.config import API_BASE_URL, HEADERS
from lpick_watcher.models import FoundItem


def validate_api_config() -> None:
    if not API_BASE_URL:
        raise RuntimeError("LPICK_API_BASE_URL 환경변수가 비어있습니다.\n")


def push_to_pending(item: FoundItem) -> None:
    payload = {
        "artistName": item.artist,
        "albumTitle": item.album,
        "storeSlug": item.store_slug,
        "sourceProductTitle": item.source_product_title,
        "url": item.url,
        "price": item.price,
        "coverImageUrl": item.cover_image_url,
        "note": "watcher 자동 수집",
    }

    response = requests.post(
        f"{API_BASE_URL.rstrip('/')}/pending-candidates",
        json=payload,
        timeout=20,
        headers={**HEADERS, "Content-Type": "application/json"},
        allow_redirects=True,
    )
    if response.status_code == 409:
        return
    response.raise_for_status()
