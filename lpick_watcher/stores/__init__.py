from collections.abc import Callable

from lpick_watcher.config import ENABLED_STORES
from lpick_watcher.models import FoundItem

from . import aladin, gimbab, hottracks, yes24

StoreFetcher = Callable[[str], list[FoundItem]]
CatalogStoreFetcher = Callable[[], list[FoundItem]]

STORE_FETCHERS: dict[str, StoreFetcher] = {
    "aladin": aladin.fetch,
    "yes24": yes24.fetch,
    "hottracks": hottracks.fetch,
}

CATALOG_STORE_FETCHERS: dict[str, CatalogStoreFetcher] = {
    "gimbab": gimbab.fetch,
}


def get_enabled_store_fetchers() -> list[StoreFetcher]:
    if not ENABLED_STORES or "all" in {value.lower() for value in ENABLED_STORES}:
        return list(STORE_FETCHERS.values())

    return [
        fetcher
        for slug, fetcher in STORE_FETCHERS.items()
        if slug in set(ENABLED_STORES)
    ]


def get_enabled_catalog_store_fetchers() -> list[CatalogStoreFetcher]:
    if not ENABLED_STORES or "all" in {value.lower() for value in ENABLED_STORES}:
        return list(CATALOG_STORE_FETCHERS.values())

    return [
        fetcher
        for slug, fetcher in CATALOG_STORE_FETCHERS.items()
        if slug in set(ENABLED_STORES)
    ]
