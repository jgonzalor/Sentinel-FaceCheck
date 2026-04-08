from __future__ import annotations
import base64
import json
from dataclasses import dataclass
from typing import Any
import requests
from .config import google_lens_enabled, lenso_api_key, yandex_enabled

GOOGLELENS_OK = True
GOOGLELENS_ERROR = ""
try:
    from googlelens import GoogleLens
except Exception as exc:  # pragma: no cover
    GOOGLELENS_OK = False
    GOOGLELENS_ERROR = str(exc)
    GoogleLens = None


@dataclass
class SearchResult:
    provider: str
    title: str
    url: str


def google_lens_search(image_path: str) -> list[SearchResult]:
    if not google_lens_enabled():
        return []
    if not GOOGLELENS_OK:
        raise RuntimeError(f"google-lens-python no disponible: {GOOGLELENS_ERROR}")
    lens = GoogleLens()
    raw = lens.search_by_file(image_path)
    results = []
    for item in raw.get("results", [])[:12]:
        url = item.get("url", "")
        title = item.get("title", "Sin título")
        if url:
            results.append(SearchResult(provider="Google Lens", title=title, url=url))
    return results


def yandex_search_url(image_path: str) -> str:
    if not yandex_enabled():
        return ""
    with open(image_path, "rb") as f:
        files = {"upfile": ("blob", f, "image/jpeg")}
        params = {
            "rpt": "imageview",
            "format": "json",
            "request": '{"blocks":[{"block":"b-page_type_search-by-image__link"}]}'
        }
        r = requests.post("https://yandex.com/images/search", params=params, files=files, timeout=30)
    r.raise_for_status()
    data = json.loads(r.content)
    return f"https://yandex.com/images/search?{data['blocks'][0]['params']['url']}"


def lenso_search(image_path: str) -> list[SearchResult]:
    key = lenso_api_key().strip()
    if not key:
        return []
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"image": b64}
    r = requests.post("https://api.eyematch.ai/search", json=payload, headers=headers, timeout=45)
    r.raise_for_status()
    data = r.json()
    results = []
    for item in data.get("results", [])[:10]:
        url = item.get("url", "")
        title = item.get("title", "Match")
        if url:
            results.append(SearchResult(provider="Lenso.ai", title=title, url=url))
    return results


def manual_provider_links() -> dict[str, str]:
    return {
        "TinEye": "https://tineye.com/",
        "Baidu Images": "https://image.baidu.com/",
        "Bing Visual Search": "https://www.bing.com/images/search?view=detailv2&iss=sbi",
        "Lenso.ai (web)": "https://lenso.ai",
        "Google Lens (web)": "https://lens.google.com/",
        "Yandex Images": "https://yandex.com/images/",
    }
