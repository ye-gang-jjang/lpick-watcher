import os
from pathlib import Path


API_BASE_URL = os.environ.get("LPICK_API_BASE_URL", "https://vinyl-alert-api.onrender.com").strip()
STATE_PATH = Path("seen_urls.json")
REQUEST_DELAY_SEC = 1.0
ALADIN_CATEGORY_URL = os.environ.get(
    "LPICK_ALADIN_CATEGORY_URL",
    "https://www.aladin.co.kr/shop/wbrowse.aspx?BrowseTarget=List&ViewRowsCount=25&ViewType=Detail&PublishMonth=0&SortOrder=6&page=1&Stockstatus=1&PublishDay=84&CID=86800&CustReviewRankStart=&CustReviewRankEnd=&CustReviewCountStart=&CustReviewCountEnd=&PriceFilterMin=&PriceFilterMax=&MusicFilter=&SearchOption=",
).strip()
YES24_CATEGORY_URL = os.environ.get(
    "LPICK_YES24_CATEGORY_URL",
    "https://www.yes24.com/product/category/display/003001033001",
).strip()
GIMBAB_CATEGORY_URL = os.environ.get(
    "LPICK_GIMBAB_CATEGORY_URL",
    "https://gimbabrecords.com/product/list.html?cate_no=52",
).strip()
GIMBAB_MAX_PAGES = int(os.environ.get("LPICK_GIMBAB_MAX_PAGES", "1"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LPICK-WATCHER/1.0; +https://www.lpick.shop)",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

def parse_csv_env(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [value.strip() for value in raw.split(",") if value.strip()]


ENABLED_STORES = parse_csv_env("LPICK_ENABLED_STORES")
