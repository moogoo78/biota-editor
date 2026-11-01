"""TaiCOL nametool webhook — same contract as biota's POST /hooks:
{"event": "...", "data": {"email", "namespace_id", "name"}}"""
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..ingest import import_namespace
from ..models import Notification, User, WebhookEvent
from ..sources import taicol
from ..sources.http import UpstreamError

log = logging.getLogger("hooks")
router = APIRouter(prefix="/api", tags=["hooks"])


@router.post("/hooks")
async def taicol_hook(request: Request, db: Session = Depends(get_db),
                      x_webhook_token: str | None = Header(default=None),
                      token: str | None = Query(default=None)):
    if settings.webhook_secret:
        given = x_webhook_token or token or ""
        if not hmac.compare_digest(given, settings.webhook_secret):
            raise HTTPException(401, "bad webhook token")
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(400, "invalid json")
    event = (body or {}).get("event")
    data = (body or {}).get("data") or {}
    if not event or not isinstance(data, dict):
        return {"message": "invalid data"}

    ev = WebhookEvent(name=str(event)[:200], data=data)
    db.add(ev)
    db.commit()

    def done(msg: str) -> dict:
        ev.result = msg
        db.commit()
        return {"message": msg}

    email = (data.get("email") or "").lower()
    try:
        namespace_id = int(data.get("namespace_id"))
    except (TypeError, ValueError):
        return done("invalid data")
    user = db.query(User).filter_by(email=email).first() if email else None
    if user is None:
        return done("no user")
    try:
        if not taicol.owns_namespace(user.email, namespace_id):
            return done("namespace not available")
        pub, status, counts = import_namespace(db, user.id, namespace_id)
    except UpstreamError as e:
        log.warning("webhook import failed: %s", e)
        return done(f"import failed: {e}")

    name = data.get("name") or pub.title
    verb = "imported" if status == "new" else "re-synced"
    db.add(Notification(user_id=user.id, event_id=ev.id, publication_id=pub.id,
                        content=f"namespace [{namespace_id}] {name} published — {verb} "
                                f"(+{counts['created']} ~{counts['updated']} -{counts['deleted']})"))
    db.commit()
    return done("ok")
