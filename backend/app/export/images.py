"""Download a selected image for embedding in an export (allow-listed hosts only)."""
from io import BytesIO
from urllib.parse import urlparse

import httpx

from ..config import IMAGE_HOSTS, settings

MAX_BYTES = 15 * 1024 * 1024


def allowed(url: str) -> bool:
    u = urlparse(url or "")
    return u.scheme in ("http", "https") and (u.hostname or "") in IMAGE_HOSTS


def fetch_image(url: str) -> BytesIO | None:
    if not allowed(url):
        return None
    try:
        with httpx.Client(timeout=settings.http_timeout, follow_redirects=False,
                          headers={"User-Agent": "Mozilla/5.0 BiotaEditor"}) as c:
            r = c.get(url)
            if r.status_code != 200 or len(r.content) > MAX_BYTES:
                return None
            return BytesIO(r.content)
    except httpx.HTTPError:
        return None
