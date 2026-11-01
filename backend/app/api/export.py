import json
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse

from ..export import build_export_data
from ..export import render
from ..models import Publication
from .deps import get_pub

router = APIRouter(prefix="/api/publications", tags=["export"])

FORMATS = {
    "docx": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ""),
    "pdf": ("pdf", "application/pdf", ""),
    "pdf2": ("pdf", "application/pdf", "-journal"),
    "pdf3": ("pdf", "application/pdf", "-journal-compact"),
    "json": ("json", "application/json", ""),
}


@router.get("/{pub_id}/preview")
def preview(pub: Publication = Depends(get_pub)):
    """The structured context every renderer consumes (generate_json)."""
    return render.generate_json([build_export_data(pub)])


@router.get("/{pub_id}/export")
def export(format: str = "docx", pub: Publication = Depends(get_pub)):
    if format not in FORMATS:
        raise HTTPException(422, f"format must be one of {list(FORMATS)}")
    ext, mime, suffix = FORMATS[format]
    data = [build_export_data(pub)]
    if format == "docx":
        buf = BytesIO()
        render.generate_docx(data).save(buf)
        buf.seek(0)
    elif format == "pdf":
        buf = render.generate_pdf(data)
    elif format == "pdf2":
        buf = render.generate_pdf2(data)
    elif format == "pdf3":
        buf = render.generate_pdf3(data)
    else:
        body = json.dumps(render.generate_json(data), ensure_ascii=False, indent=2)
        buf = BytesIO(body.encode())
    filename = quote(f"biotaeditor-{pub.title or pub.id}{suffix}.{ext}")
    return StreamingResponse(buf, media_type=mime, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
    })
