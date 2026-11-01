from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..ingest import TEXT_FIELDS, _item_values
from ..models import Item, ItemImage, ItemSpecimen
from ..schemas import ImagePick, ItemOut, ItemPatch, RevertIn, SpecimenPick
from ..sources import inat, taicol, taieol, tbia
from ..sources.http import UpstreamError
from .deps import get_item, item_out, search_names, upstream

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/{item_id}", response_model=ItemOut)
def read_item(item: Item = Depends(get_item)):
    return item_out(item)


@router.patch("/{item_id}", response_model=ItemOut)
def patch_item(body: ItemPatch, item: Item = Depends(get_item), db: Session = Depends(get_db)):
    edited = set(item.edited_fields or [])
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(item, k, v or "")
        edited.add(k)
    item.edited_fields = sorted(edited)
    db.commit()
    return item_out(item)


@router.post("/{item_id}/revert", response_model=ItemOut)
def revert_item(body: RevertIn, item: Item = Depends(get_item), db: Session = Depends(get_db)):
    """Restore fields to the TaiCOL values and let future syncs update them again."""
    src = _item_values(item.source_data or {})
    edited = set(item.edited_fields or [])
    for k in body.fields:
        if k in TEXT_FIELDS:
            setattr(item, k, src[k])
            edited.discard(k)
    item.edited_fields = sorted(edited)
    db.commit()
    return item_out(item)


# ---- specimens (tbia-specimen-annotation / ISLAND) ----

def _filters(county, type_status, dataset_name, has_media) -> dict:
    return {"county": county, "type_status": type_status, "dataset_name": dataset_name,
            "has_media": has_media}


@router.get("/{item_id}/specimen-candidates")
def specimen_candidates(
    item: Item = Depends(get_item),
    q: str | None = None,
    names: list[str] = Query(default=[]),
    county: list[str] = Query(default=[]),
    type_status: list[str] = Query(default=[]),
    dataset_name: list[str] = Query(default=[]),
    has_media: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """ISLAND has no taxon id, so match by name: the accepted name plus every
    synonym (``names`` narrows that set), or a free-text ``q`` instead."""
    use = names or search_names(item)
    try:
        res = tbia.search(use, q, _filters(county, type_status, dataset_name, has_media),
                          limit=limit, offset=offset)
    except UpstreamError as e:
        raise upstream(e)
    picked = {s.occurrence_id for s in item.specimens}
    for row in res.get("items", []):
        row["picked"] = row.get("id") in picked
        row["link"] = tbia.record_link(row.get("id"))
        row["display_text"] = tbia.display_text(row)
    res["names"] = [] if q else use
    return res


@router.get("/{item_id}/specimen-facets")
def specimen_facets(item: Item = Depends(get_item), q: str | None = None,
                    names: list[str] = Query(default=[])):
    try:
        return tbia.facets(names or search_names(item), q)
    except UpstreamError as e:
        raise upstream(e)


@router.put("/{item_id}/specimens", response_model=ItemOut)
def put_specimens(body: list[SpecimenPick], item: Item = Depends(get_item),
                  db: Session = Depends(get_db)):
    """Replace the picked set (order = list order). Existing picks keep their
    edited display text unless a new one is sent."""
    old = {s.occurrence_id: s for s in item.specimens}
    seen: set[str] = set()
    new: list[ItemSpecimen] = []
    for n, p in enumerate(body, start=1):
        if p.occurrence_id in seen:
            continue
        seen.add(p.occurrence_id)
        r = p.record
        sp = old.get(p.occurrence_id)
        if sp is None:
            sp = ItemSpecimen(source="tbia", occurrence_id=p.occurrence_id)
            for k in ("scientific_name", "catalog_number", "recorded_by", "record_number",
                      "locality", "county", "institution_code", "dataset_name", "type_status"):
                v = r.get(k)
                setattr(sp, k, str(v) if v is not None else None)
            sp.event_date = str(r.get("standard_date") or r.get("event_date") or "") or None
            sp.source_data = r
            sp.display_text = p.display_text or tbia.display_text(r)
        elif p.display_text is not None:
            sp.display_text = p.display_text
        sp.sort = n
        new.append(sp)
    item.specimens[:] = new
    db.commit()
    db.refresh(item)
    return item_out(item)


# ---- images (iNaturalist / TaiEOL) ----

@router.get("/{item_id}/image-candidates")
def image_candidates(item: Item = Depends(get_item), source: str = "inat", page: int = 1,
                     name: str | None = None):
    try:
        if source == "inat":
            res = inat.photos(name or item.scientific_name, page=page)
        elif source == "taieol":
            if not item.name_id:
                raise HTTPException(422, "item has no TaiCOL name_id")
            tids = taicol.taxon_ids_for_name(item.name_id)
            if not tids:
                return {"total": 0, "page": 1, "has_more": False, "items": [], "taxon_id": None}
            res = taieol.photos(tids[0])
            res["taxon_id"] = tids[0]
        else:
            raise HTTPException(422, "source must be inat or taieol")
    except UpstreamError as e:
        raise upstream(e)
    picked = {(im.source, im.source_id) for im in item.images}
    for row in res["items"]:
        row["picked"] = (row["source"], row["source_id"]) in picked
    return res


@router.put("/{item_id}/images", response_model=ItemOut)
def put_images(body: list[ImagePick], item: Item = Depends(get_item), db: Session = Depends(get_db)):
    old = {(im.source, im.source_id): im for im in item.images}
    seen: set = set()
    new: list[ItemImage] = []
    for n, p in enumerate(body, start=1):
        key = (p.source, p.source_id)
        if key in seen:
            continue
        seen.add(key)
        im = old.get(key) or ItemImage(source=p.source, source_id=p.source_id,
                                       source_data=p.record or None)
        im.url, im.thumb_url, im.link = p.url, p.thumb_url, p.link
        im.attribution, im.license, im.caption = p.attribution, p.license, p.caption
        im.sort = n
        new.append(im)
    item.images[:] = new
    db.commit()
    db.refresh(item)
    return item_out(item)
