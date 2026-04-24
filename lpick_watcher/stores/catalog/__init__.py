from lpick_watcher.config import ENABLED_STORES

from ..base import StoreFetcher
from . import aladin, gimbab, yes24

CATALOG_STORES = [aladin, gimbab, yes24]
CATALOG_STORE_FETCHERS: dict[str, StoreFetcher] = {store.STORE_SLUG: store.fetch for store in CATALOG_STORES}


def get_enabled_catalog_store_fetchers() -> list[StoreFetcher]:
    enabled = {value.lower() for value in ENABLED_STORES}
    if not enabled or "all" in enabled:
        return [store.fetch for store in CATALOG_STORES]

    return [store.fetch for store in CATALOG_STORES if store.STORE_SLUG in enabled]

__all__ = [
    "CATALOG_STORES",
    "CATALOG_STORE_FETCHERS",
    "get_enabled_catalog_store_fetchers",
    "aladin",
    "gimbab",
    "yes24",
]
