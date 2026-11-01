from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..ingest import apply_namespace, import_namespace
from ..models import Item, Publication, PublicationLiterature, User
from ..schemas import (ImportIn, ImportOut, LiteratureIn, LiteratureOut, OrderIn, PublicationOut,
                       PublicationPatch, PublicationSummary)
from ..sources import taicol
from ..sources.http import UpstreamError
from .deps import get_pub, pub_out, pub_summary, upstream

router = APIRouter(prefix="/api", tags=["publications"])

STATUSES = {"draft", "review", "done"}


@router.get("/namespaces/available")
def available(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Namespaces this user may import (from TaiCOL), flagged if already imported."""
    try:
        ids = taicol.available_namespaces(user.email)
    except UpstreamError as e:
        raise upstream(e)
    imported = {p.namespace_id: p.id for p in db.query(Publication).filter_by(user_id=user.id)}
    return [{"namespace_id": i, "publication_id": imported.get(i)} for i in ids]


@router.post("/publications/import", response_model=ImportOut)
def import_pub(body: ImportIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        if not taicol.owns_namespace(user.email, body.namespace_id):
            raise HTTPException(403, f"namespace {body.namespace_id} is not available to {user.email}")
        pub, status, counts = import_namespace(db, user.id, body.namespace_id)
    except UpstreamError as e:
        raise upstream(e)
    return ImportOut(publication_id=pub.id, status=status, counts=counts)


@router.get("/publications", response_model=list[PublicationSummary])
def list_pubs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    pubs = db.query(Publication).filter_by(user_id=user.id).order_by(Publication.updated_at.desc()).all()
    return [pub_summary(p) for p in pubs]


@router.get("/publications/{pub_id}", response_model=PublicationOut)
def get_publication(pub: Publication = Depends(get_pub)):
    return pub_out(pub)


@router.patch("/publications/{pub_id}", response_model=PublicationOut)
def patch_publication(body: PublicationPatch, pub: Publication = Depends(get_pub),
                      db: Session = Depends(get_db)):
    vals = body.model_dump(exclude_unset=True)
    if "status" in vals and vals["status"] not in STATUSES:
        raise HTTPException(422, f"status must be one of {sorted(STATUSES)}")
    for k, v in vals.items():
        setattr(pub, k, v)
    db.commit()
    return pub_out(pub)


@router.delete("/publications/{pub_id}")
def delete_publication(pub: Publication = Depends(get_pub), db: Session = Depends(get_db)):
    db.delete(pub)
    db.commit()
    return {"message": "deleted"}


@router.post("/publications/{pub_id}/sync")
def sync_publication(pub: Publication = Depends(get_pub), db: Session = Depends(get_db)):
    try:
        data = taicol.fetch_namespace(pub.namespace_id)
    except UpstreamError as e:
        raise upstream(e)
    counts = apply_namespace(db, pub, data)
    db.commit()
    return counts


@router.put("/publications/{pub_id}/literatures", response_model=list[LiteratureOut])
def put_literatures(body: list[LiteratureIn], pub: Publication = Depends(get_pub),
                    db: Session = Depends(get_db)):
    pub.literatures.clear()
    db.flush()
    for i, lit in enumerate(body, start=1):
        pub.literatures.append(PublicationLiterature(reference_id=lit.reference_id,
                                                     citation=lit.citation, sort=i))
    db.commit()
    return pub.literatures


@router.put("/publications/{pub_id}/items/order", response_model=PublicationOut)
def order_items(body: OrderIn, pub: Publication = Depends(get_pub), db: Session = Depends(get_db)):
    by_id = {i.id: i for i in pub.items}
    if set(body.ids) != set(by_id):
        raise HTTPException(422, "ids must list every item of the publication exactly once")
    for n, iid in enumerate(body.ids, start=1):
        by_id[iid].sort = n
    db.commit()
    db.refresh(pub)
    return pub_out(pub)
