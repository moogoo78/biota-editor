"""iNaturalist research-grade observation photos."""
from ..config import settings
from .http import get_json


def _size(url: str, size: str) -> str:
    return url.replace("/square.", f"/{size}.") if url else url


def photos(name: str, page: int = 1, per_page: int = 30) -> dict:
    data = get_json("inat", f"{settings.inat_api}/observations", {
        "taxon_name": name, "photos": "true", "quality_grade": "research",
        "per_page": per_page, "page": page, "order_by": "votes",
    })
    out = []
    for obs in data.get("results", []):
        user = (obs.get("user") or {}).get("login") or ""
        for p in obs.get("photos", []) or []:
            url = p.get("url") or ""
            out.append({
                "source": "inat",
                "source_id": str(p.get("id")),
                "url": _size(url, "large"),
                "thumb_url": _size(url, "medium"),
                "attribution": p.get("attribution") or "",
                "license": p.get("license_code") or "",
                "observer": user,
                "link": f"https://www.inaturalist.org/observations/{obs.get('id')}",
                "title": (obs.get("taxon") or {}).get("name") or name,
                "date": obs.get("observed_on") or "",
                "place": obs.get("place_guess") or "",
            })
    total = data.get("total_results", 0)
    return {"total": total, "page": page, "has_more": page * per_page < total, "items": out}
