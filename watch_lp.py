from lpick_watcher.config import ENABLED_STORES
from lpick_watcher.pipeline import run_watch
from lpick_watcher.sinks.pending_api import validate_api_config


def main() -> None:
    validate_api_config()
    active_stores = ", ".join(ENABLED_STORES) if ENABLED_STORES else "all"
    print(f"[START] stores={active_stores}")

    summary = run_watch()

    print("\n[DONE]")
    print(f"  candidates found  : {summary.candidates_found}")
    print(f"  pending pushed    : {summary.pending_pushed}")
    print(f"  duplicates skipped: {summary.duplicates_skipped}")
    print(f"  store errors      : {summary.store_errors}")
    print(f"  push errors       : {summary.push_errors}")


if __name__ == "__main__":
    main()
