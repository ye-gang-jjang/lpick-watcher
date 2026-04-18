from __future__ import annotations

from collections.abc import Callable

from lpick_watcher.models import FoundItem

StoreFetcher = Callable[[], list[FoundItem]]
