"""TaiEOL (臺灣生命大百科) media by TaiCOL taxon_id."""
import re
from urllib.parse import urlparse

from ..config import settings
from .http import get_json

# TaiEOL serves its API only with a browser-like UA (as biota did)
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
           "Accept": "*/*"}


def _license_code(url: str) -> str:
    """'https://creativecommons.org/licenses/by-nc/3.0/tw/' -> 'cc-by-nc'"""
    if not url:
        return ""
    m = re.search(r"/licenses/([a-z\-]+)/", url) or re.search(r"/(publicdomain)/", url)
    return f"cc-{m.group(1)}" if m and m.group(1) != "publicdomain" else ("cc0" if m else url)


def photos(taxon_id: str) -> dict:
    data = get_json("taieol", f"{settings.taieol_api}/taieol_object/taxon_id/{taxon_id}",
                    {"token": settings.taieol_token}, headers=HEADERS)
    out = []
    for obj in (data or {}).get("data", []) or []:
        for i, m in enumerate(obj.get("associatedMedia", []) or []):
            url = m.get("url") or ""
            if not url:
                continue
            authors = (m.get("authors") or "").replace("作者：", "").strip()
            path = urlparse(url).path
            out.append({
                "source": "taieol",
                "source_id": f"{obj.get('OID')}:{path.rsplit('/', 1)[-1]}",
                "url": url,
                "thumb_url": url.replace("/w960/", "/w480/"),
                "attribution": ", ".join(x for x in (authors, obj.get("datasetName") or obj.get("rightsHolder")) if x),
                "license": _license_code(m.get("licence") or ""),
                "license_url": m.get("licence") or "",
                "observer": authors,
                "link": obj.get("permanentLink") or obj.get("taieolTaxonPage") or "",
                "title": obj.get("scientificName") or "",
                "kind": obj.get("speciesPictureClassification") or "",
                "citation": m.get("citation") or "",
            })
    return {"total": len(out), "page": 1, "has_more": False, "items": out}
