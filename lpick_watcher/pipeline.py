from dataclasses import dataclass
import time

from lpick_watcher.config import REQUEST_DELAY_SEC
from lpick_watcher.models import FoundItem
from lpick_watcher.sinks.pending_api import push_to_pending
from lpick_watcher.state import load_seen, save_seen
from lpick_watcher.stores import get_enabled_catalog_store_fetchers, get_enabled_store_fetchers


@dataclass
class RunSummary:
    artists_processed: int = 0
    candidates_found: int = 0
    pending_pushed: int = 0
    duplicates_skipped: int = 0
    store_errors: int = 0
    push_errors: int = 0


def collect_for_artist(artist: str) -> tuple[list[FoundItem], int]:
    results: list[FoundItem] = []
    store_errors = 0

    for store_fetcher in get_enabled_store_fetchers():
        try:
            results.extend(store_fetcher(artist))
        except Exception as error:
            store_errors += 1
            print(f"[WARN] {store_fetcher.__module__} failed for '{artist}': {error}")

        time.sleep(REQUEST_DELAY_SEC)

    deduped_by_url: dict[str, FoundItem] = {}
    for item in results:
        deduped_by_url[item.url] = item

    return list(deduped_by_url.values()), store_errors


def run_watch(artists: list[str]) -> RunSummary:
    seen = load_seen()
    summary = RunSummary()

    for store_fetcher in get_enabled_catalog_store_fetchers():
        try:
            found = store_fetcher()
        except Exception as error:
            summary.store_errors += 1
            print(f"[WARN] {store_fetcher.__module__} failed: {error}")
            time.sleep(REQUEST_DELAY_SEC)
            continue

        summary.candidates_found += len(found)
        new_items = [item for item in found if item.url not in seen]
        summary.duplicates_skipped += max(0, len(found) - len(new_items))

        if not new_items:
            print(f"[OK] {store_fetcher.__module__}: no new items")
        else:
            print(f"[NEW] {store_fetcher.__module__}: {len(new_items)} items")

        for item in new_items:
            try:
                push_to_pending(item)
                seen.add(item.url)
                summary.pending_pushed += 1
                print(f"  + {item.store_name} | {item.album} | {item.url}")
            except Exception as error:
                summary.push_errors += 1
                print(f"[ERROR] push failed: {error}")

            time.sleep(0.5)

        time.sleep(REQUEST_DELAY_SEC)

    for artist in artists:
        found, store_errors = collect_for_artist(artist)
        summary.artists_processed += 1
        summary.candidates_found += len(found)
        summary.store_errors += store_errors

        new_items = [item for item in found if item.url not in seen]
        summary.duplicates_skipped += max(0, len(found) - len(new_items))

        if not new_items:
            print(f"[OK] {artist}: no new items")
            continue

        print(f"[NEW] {artist}: {len(new_items)} items")

        for item in new_items:
            try:
                push_to_pending(item)
                seen.add(item.url)
                summary.pending_pushed += 1
                print(f"  + {item.store_name} | {item.album} | {item.url}")
            except Exception as error:
                summary.push_errors += 1
                print(f"[ERROR] push failed: {error}")

            time.sleep(0.5)

        time.sleep(REQUEST_DELAY_SEC)

    save_seen(seen)
    return summary
