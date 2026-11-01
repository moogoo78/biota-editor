import json
import os

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import Item, Publication, User
from ..schemas import ItemOut, ItemSummary, PublicationOut, PublicationSummary, SpecimenOut
from ..sources import tbia
from ..sources.http import UpstreamError
from ..text import name_from_usage

with open(os.path.join(os.path.dirname(__file__), "..", "ranks.json"), encoding="utf-8") as f:
    RANKS: dict[int, list[str]] = {int(k): v for k, v in json.load(f).items()}


def upstream(e: UpstreamError) -> HTTPException:
    return HTTPException(502, str(e))


def get_pub(pub_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Publication:
    pub = db.get(Publication, pub_id)
    if pub is None or pub.user_id != user.id:
        raise HTTPException(404, "Publication not found")
    return pub


def get_item(item_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Item:
    item = db.get(Item, item_id)
    if item is None or item.publication.user_id != user.id:
        raise HTTPException(404, "Item not found")
    return item


def search_names(item: Item) -> list[str]:
    """Accepted name first, then each synonym's plain name (deduplicated)."""
    out = [item.scientific_name]
    for s in item.synonyms:
        n = name_from_usage(s.usage_text)
        if n and n not in out:
            out.append(n)
    return [n for n in out if n]


def item_summary(item: Item) -> ItemSummary:
    s = ItemSummary.model_validate(item)
    s.rank = RANKS.get(item.rank_id or 0)
    s.n_specimens, s.n_images, s.n_synonyms = len(item.specimens), len(item.images), len(item.synonyms)
    return s


def item_out(item: Item) -> ItemOut:
    out = ItemOut.model_validate(item)
    out.rank = RANKS.get(item.rank_id or 0)
    out.n_specimens, out.n_images, out.n_synonyms = len(item.specimens), len(item.images), len(item.synonyms)
    out.search_names = search_names(item)
    out.specimens = [
        SpecimenOut.model_validate(s).model_copy(update={"link": tbia.record_link(s.occurrence_id)})
        for s in item.specimens
    ]
    return out


def pub_summary(pub: Publication) -> PublicationSummary:
    s = PublicationSummary.model_validate(pub)
    s.n_items = len(pub.items)
    return s


def pub_out(pub: Publication) -> PublicationOut:
    out = PublicationOut.model_validate(pub)
    out.n_items = len(pub.items)
    out.items = [item_summary(i) for i in pub.items]
    return out
