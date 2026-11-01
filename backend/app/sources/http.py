"""Shared outbound HTTP: one httpx client per call site + a tiny TTL cache so
paging through candidates doesn't hammer TaiCOL / ISLAND / iNat / TaiEOL."""
import time
from typing import Any

import httpx

from ..config import settings

UA = "BiotaEditor/0.1 (+https://github.com/moogoo78)"

_cache: dict[str, tuple[float, Any]] = {}


class UpstreamError(Exception):
    def __init__(self, source: str, message: str):
        super().__init__(f"[{source}] {message}")
        self.source = source


def get_json(source: str, url: str, params: Any = None, *, cache: bool = True,
             headers: dict | None = None) -> Any:
    key = f"{url}?{httpx.QueryParams(params or {})}"
    now = time.monotonic()
    if cache and (hit := _cache.get(key)) and hit[0] > now:
        return hit[1]
    try:
        with httpx.Client(timeout=settings.http_timeout, follow_redirects=True,
                          headers={"User-Agent": UA, **(headers or {})}) as c:
            r = c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        raise UpstreamError(source, f"HTTP {e.response.status_code}") from e
    except (httpx.HTTPError, ValueError) as e:
        raise UpstreamError(source, str(e) or e.__class__.__name__) from e
    if cache:
        if len(_cache) > 2000:
            _cache.clear()
        _cache[key] = (now + settings.cache_ttl, data)
    return data


def clear_cache() -> None:
    _cache.clear()
