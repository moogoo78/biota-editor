"""TaiCOL namespace -> Publication/Items. Ports biota's
create_collection_by_taicol_namespace / sync_collection_by_taicol_namespace
(biota/app/helpers.py), but a sync upserts by name_id and never touches the
specimens/images the author picked, nor fields the author edited locally."""
from .models import utcnow

from sqlalchemy.orm import Session

from .models import Item, ItemSynonym, Publication, PublicationLiterature
from .sources import taicol
from .text import strip_tags

TEXT_FIELDS = ("description", "distribution", "note", "common_names")


def _item_values(g: dict) -> dict:
    return {
        "name_id": g.get("name_id"),
        "rank_id": g.get("rank_id"),
        "scientific_name": strip_tags(g.get("name")),
        "name_html": g.get("name") or "",
        "name_authors": g.get("name_authors") or "",
        "usage_text": g.get("usage_references_text") or "",
        "common_names": "|".join(g.get("common_names") or []),
        "description": g.get("description") or "",
        "distribution": g.get("distribution") or "",
        "note": g.get("note") or "",
        "source_data": g,
    }


def _set_synonyms(item: Item, g: dict) -> None:
    item.synonyms.clear()
    for i, s in enumerate(g.get("synonyms") or []):
        item.synonyms.append(ItemSynonym(name_id=s.get("name_id"),
                                         usage_text=s.get("usage_references_text") or "", sort=i))


def _set_literatures(pub: Publication, data: dict) -> None:
    pub.literatures.clear()
    for i, lit in enumerate(data.get("literatures") or []):
        pub.literatures.append(PublicationLiterature(
            reference_id=lit.get("reference_id"), citation=lit.get("citation") or "", sort=i + 1))


def apply_namespace(db: Session, pub: Publication, data: dict) -> dict:
    """Upsert ``pub`` from a /biota payload. Returns counts."""
    pub.title = data.get("title") or pub.title or f"namespace {pub.namespace_id}"
    pub.author = data.get("author") or pub.author or ""
    pub.source_data = data
    pub.synced_at = utcnow()
    _set_literatures(pub, data)

    existing = {it.name_id: it for it in pub.items if it.name_id is not None}
    remote_ids = set()
    created = updated = 0
    for sort, g in enumerate(data.get("group") or [], start=1):
        vals = _item_values(g)
        nid = vals["name_id"]
        remote_ids.add(nid)
        if nid is not None and nid in existing:
            item = existing[nid]
            keep = set(item.edited_fields or [])
            for k, v in vals.items():
                if k not in keep:
                    setattr(item, k, v)
            updated += 1
        else:
            item = Item(**vals)
            pub.items.append(item)
            created += 1
        item.sort = sort
        _set_synonyms(item, g)

    deleted = 0
    for item in list(pub.items):
        if item.name_id is not None and item.name_id not in remote_ids:
            pub.items.remove(item)
            deleted += 1
    db.flush()
    return {"created": created, "updated": updated, "deleted": deleted}


def import_namespace(db: Session, user_id: int, namespace_id: int,
                     data: dict | None = None) -> tuple[Publication, str, dict]:
    """Create (or re-sync) the user's publication for a namespace.
    -> (publication, 'new'|'exist', counts)"""
    if data is None:
        data = taicol.fetch_namespace(namespace_id)
    pub = db.query(Publication).filter_by(user_id=user_id, namespace_id=namespace_id).one_or_none()
    status = "exist"
    if pub is None:
        pub = Publication(user_id=user_id, namespace_id=namespace_id)
        db.add(pub)
        status = "new"
    counts = apply_namespace(db, pub, data)
    db.commit()
    return pub, status, counts
