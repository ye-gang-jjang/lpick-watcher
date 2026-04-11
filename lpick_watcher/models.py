from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FoundItem:
    artist: str
    album: str
    store_slug: str
    store_name: str
    source_product_title: str
    url: str
    price: Optional[int] = None
    cover_image_url: Optional[str] = None
