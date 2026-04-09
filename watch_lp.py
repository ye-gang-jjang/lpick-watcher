import time
from lpick_watcher.config import ARTISTS, REQUEST_DELAY_SEC
from lpick_watcher.models import FoundItem
from lpick_watcher.sinks.pending_api import push_to_pending, validate_api_config
from lpick_watcher.state import load_seen, save_seen
from lpick_watcher.stores import aladin, hottracks, yes24


# =========================
# Runner
# =========================
def collect_all(artist: str) -> list[FoundItem]:
    results: list[FoundItem] = []
    for store_fetcher in (aladin.fetch, yes24.fetch, hottracks.fetch):
        try:
            results.extend(store_fetcher(artist))
        except Exception as e:
            print(f"[WARN] {store_fetcher.__module__} failed for '{artist}': {e}")
        time.sleep(REQUEST_DELAY_SEC)
    return results


def main() -> None:
    validate_api_config()
    seen = load_seen()
    pushed = 0

    for artist in ARTISTS:
        found = collect_all(artist)
        new_items = [it for it in found if it.url not in seen]

        if not new_items:
            print(f"[OK] {artist}: no new items")
            continue

        print(f"[NEW] {artist}: {len(new_items)} items")
        for it in new_items:
            try:
                push_to_pending(it)
                seen.add(it.url)
                pushed += 1
                print(f"  + {it.store_name} | {it.album} | {it.url}")
            except Exception as e:
                # push 실패하면 seen에 추가하지 않음(다음 실행 때 재시도)
                print(f"[ERROR] push failed: {e}")
            time.sleep(0.5)

        time.sleep(REQUEST_DELAY_SEC)

    save_seen(seen)
    print(f"\n[DONE] total new pushed: {pushed}")


if __name__ == "__main__":
    main()
