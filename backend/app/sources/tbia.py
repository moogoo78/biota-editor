"""tbia-specimen-annotation (ISLAND) occurrence API."""
from ..config import settings
from .http import get_json

PASS_FILTERS = ("county", "type_status", "basis_of_record", "dataset_name", "bio_group")


def _params(names: list[str], q: str | None, filters: dict, extra: list | None = None) -> list:
    params: list[tuple[str, str | int]] = []
    if q:
        params.append(("q", q))
    else:
        params += [("scientific_name", n) for n in names]
    for k in PASS_FILTERS:
        for v in filters.get(k) or []:
            params.append((k, v))
    if filters.get("has_media"):
        params.append(("has_media", "true"))
    return params + (extra or [])


def search(names: list[str], q: str | None = None, filters: dict | None = None, *,
           limit: int = 50, offset: int = 0, sort: str = "scientific_name") -> dict:
    """-> {total, items:[occurrence row], limit, offset}"""
    params = _params(names, q, filters or {},
                     [("limit", limit), ("offset", offset), ("sort", sort), ("order", "asc")])
    return get_json("tbia", f"{settings.tbia_api}/api/occurrences", params)


def facets(names: list[str], q: str | None = None, filters: dict | None = None) -> dict:
    return get_json("tbia", f"{settings.tbia_api}/api/occurrences/facets",
                    _params(names, q, filters or {}))


def record_link(occurrence_id: str) -> str:
    return f"{settings.tbia_web}/record/{occurrence_id}"


def display_text(row: dict) -> str:
    """Port of biota's format_specimen_display, for ISLAND's snake_case rows:
    'locality, recorded_by record_number (INST:catalog_number)'."""
    locality = row.get("locality") or "--"
    who = " ".join(x for x in (row.get("recorded_by"), row.get("record_number")) if x) or "--"
    inst = row.get("institution_code") or row.get("dataset_name") or "--"
    cat = row.get("catalog_number") or "--"
    return f"{locality}, {who} ({inst}:{cat})"
