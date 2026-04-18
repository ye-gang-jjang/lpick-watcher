from __future__ import annotations

from lpick_watcher.config import ENABLED_STORES

from . import aladin, gimbab
from .base import StoreFetcher

CATALOG_STORE_FETCHERS: dict[str, StoreFetcher] = {
    "aladin": aladin.fetch,
    "gimbab": gimbab.fetch,
}


def get_enabled_catalog_store_fetchers() -> list[StoreFetcher]:
    enabled = {value.lower() for value in ENABLED_STORES}
    if not enabled or "all" in enabled:
        return list(CATALOG_STORE_FETCHERS.values())

    return [fetcher for slug, fetcher in CATALOG_STORE_FETCHERS.items() if slug in enabled]
