"""TaiCOL nametool: published namespaces (the /biota payload) + ownership,
and the public TaiCOL API for name_id -> taxon_id."""
from ..config import settings
from .http import UpstreamError, get_json


def fetch_namespace(namespace_id: int) -> dict:
    """{title, author, updated_at, literatures:[{citation, reference_id}],
    group:[{name, name_id, rank_id, name_authors, usage_references_text,
    common_names[], synonyms[{name_id, usage_references_text}], description,
    distribution, note}]}"""
    data = get_json("taicol", f"{settings.taicol_api}/biota",
                    {"namespace_id": namespace_id, "token": settings.taicol_token}, cache=False)
    if not isinstance(data, dict) or "group" not in data:
        raise UpstreamError("taicol", f"namespace {namespace_id}: unexpected payload")
    return data


def available_namespaces(email: str) -> list[int]:
    data = get_json("taicol", f"{settings.taicol_api}/user/namespace", {"email": email}, cache=False)
    return [int(x) for x in (data or {}).get("namespaces", [])]


def owns_namespace(email: str, namespace_id: int) -> bool:
    if settings.taicol_skip_ownership:
        return True
    return int(namespace_id) in available_namespaces(email)


def taxon_ids_for_name(name_id: int) -> list[str]:
    """Accepted taxon ids a TaiCOL name_id is used in (first = best)."""
    data = get_json("taicol", f"{settings.taicol_public_api}/name", {"name_id": name_id})
    out: list[str] = []
    for row in (data or {}).get("data", []) or []:
        for t in row.get("taxon", []) or []:
            if (tid := t.get("taxon_id")) and tid not in out:
                # accepted usages first
                if t.get("taicol_name_status") == "Accepted":
                    out.insert(0, tid)
                else:
                    out.append(tid)
    return out
