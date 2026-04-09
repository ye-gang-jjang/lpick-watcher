from dataclasses import dataclass


@dataclass(frozen=True)
class FoundItem:
    artist: str
    album: str
    store_slug: str
    store_name: str
    source_product_title: str
    url: str
