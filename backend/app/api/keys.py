from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import IdentificationKey, KeyEntry, Publication, User
from ..schemas import KeyIn, KeyOut
from .deps import get_pub

router = APIRouter(prefix="/api", tags=["keys"])


def _own_key(key_id: int, user: User, db: Session) -> IdentificationKey:
    key = db.get(IdentificationKey, key_id)
    if key is None or key.publication.user_id != user.id:
        raise HTTPException(404, "Key not found")
    return key


def _fill(key: IdentificationKey, body: KeyIn, pub: Publication) -> None:
    valid = {i.id for i in pub.items}
    key.title = body.title
    key.entries.clear()
    for n, e in enumerate(body.entries, start=1):
        if e.result_item_id is not None and e.result_item_id not in valid:
            raise HTTPException(422, f"item {e.result_item_id} is not in this publication")
        key.entries.append(KeyEntry(**e.model_dump(), sort=n))


@router.get("/publications/{pub_id}/keys", response_model=list[KeyOut])
def list_keys(pub: Publication = Depends(get_pub)):
    return pub.keys


@router.post("/publications/{pub_id}/keys", response_model=KeyOut)
def create_key(body: KeyIn, pub: Publication = Depends(get_pub), db: Session = Depends(get_db)):
    key = IdentificationKey(publication_id=pub.id)
    _fill(key, body, pub)
    db.add(key)
    db.commit()
    return key


@router.put("/keys/{key_id}", response_model=KeyOut)
def update_key(key_id: int, body: KeyIn, user: User = Depends(current_user),
               db: Session = Depends(get_db)):
    key = _own_key(key_id, user, db)
    _fill(key, body, key.publication)
    db.commit()
    return key


@router.delete("/keys/{key_id}")
def delete_key(key_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own_key(key_id, user, db))
    db.commit()
    return {"message": "deleted"}
