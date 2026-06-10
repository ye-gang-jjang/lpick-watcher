from lpick_watcher.config import ENABLED_STORES

from ..base import StoreFetcher
from . import aladin, doperecord, gimbab, hottracks, yes24

CATALOG_STORES = [aladin, doperecord, gimbab, hottracks, yes24]


def get_enabled_catalog_store_fetchers() -> list[StoreFetcher]:
    enabled = {value.lower() for value in ENABLED_STORES}
    if not enabled or "all" in enabled:
        return [store.fetch for store in CATALOG_STORES]

    return [store.fetch for store in CATALOG_STORES if store.STORE_SLUG in enabled]

__all__ = [
    "CATALOG_STORES",
    "get_enabled_catalog_store_fetchers",
    "aladin",
    "doperecord",
    "gimbab",
    "hottracks",
    "yes24",
]
