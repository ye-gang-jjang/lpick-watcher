import requests

from lpick_watcher.config import HEADERS


def get_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text
