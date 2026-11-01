import io
import json

import pytest
from docx import Document
from pypdf import PdfReader

from app.export import images as export_images


@pytest.fixture
def filled(client, auth, pub_id, monkeypatch):
    """One species with two specimens and one image; image download is stubbed."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (400, 300), (40, 120, 60)).save(buf, "JPEG")
    monkeypatch.setattr("app.export.render.fetch_image",
                        lambda url: io.BytesIO(buf.getvalue()) if export_images.allowed(url) else None)
    items = client.get(f"/api/publications/{pub_id}", headers=auth).json()["items"]
    it = next(i for i in items if i["scientific_name"] == "Berberis brevisepala")
    client.put(f"/api/items/{it['id']}/specimens", headers=auth, json=[
        {"occurrence_id": "a", "record": {"locality": "合歡山", "county": "南投縣", "recorded_by": "Lu",
                                          "record_number": "1", "institution_code": "TAI", "catalog_number": "9"}},
        {"occurrence_id": "b", "display_text": "Custom text", "record": {"county": "花蓮縣"}}])
    client.put(f"/api/items/{it['id']}/images", headers=auth, json=[
        {"source": "inat", "source_id": "1", "url": "https://static.inaturalist.org/a.jpg",
         "caption": "Flowering branch", "attribution": "(c) moo"}])
    client.post(f"/api/publications/{pub_id}/keys", headers=auth, json={"title": "Key", "entries": [
        {"number": 1, "description": "Leaves spiny", "result_item_id": it["id"]},
        {"number": 1, "indent_level": 1, "description": "Leaves entire", "result_couplet": 2}]})
    return pub_id


def test_preview_json(client, auth, filled):
    ctx = client.get(f"/api/publications/{filled}/preview", headers=auth).json()
    pub = ctx["publications"][0]
    assert pub["category"]["scientificName"] == "Berberis"
    sp = next(i for i in pub["items"] if i["scientificName"] == "Berberis brevisepala")
    assert {g["county"] for g in sp["specimens"]} == {"南投縣", "花蓮縣"}
    assert sp["images"][0]["captionText"] == "Flowering branch ((c) moo)"
    assert pub["keys"][0]["entries"][0]["result"] == "Berberis brevisepala"


def test_docx(client, auth, filled):
    r = client.get(f"/api/publications/{filled}/export?format=docx", headers=auth)
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    doc = Document(io.BytesIO(r.content))
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Berberis brevisepala" in text and "合歡山, Lu 1 (TAI:9)" in text and "Custom text" in text
    assert "Flowering branch ((c) moo)" in text
    assert len(doc.inline_shapes) == 1


@pytest.mark.parametrize("fmt", ["pdf", "pdf2", "pdf3"])
def test_pdf(client, auth, filled, fmt):
    r = client.get(f"/api/publications/{filled}/export?format={fmt}", headers=auth)
    assert r.status_code == 200, r.text[:500]
    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) >= 1
    assert "brevisepala" in "".join(p.extract_text() or "" for p in reader.pages)


def test_json_download_and_bad_format(client, auth, filled):
    r = client.get(f"/api/publications/{filled}/export?format=json", headers=auth)
    assert json.loads(r.content)["publications"][0]["title"]
    assert client.get(f"/api/publications/{filled}/export?format=rtf", headers=auth).status_code == 422


def test_image_host_allowlist():
    assert export_images.allowed("https://data.taieol.tw/x.jpg")
    assert not export_images.allowed("http://169.254.169.254/latest/meta-data")
    assert not export_images.allowed("file:///etc/passwd")
