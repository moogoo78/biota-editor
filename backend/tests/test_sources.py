import httpx
import respx

from app.config import settings


def _brev(client, auth, pub_id):
    items = client.get(f"/api/publications/{pub_id}", headers=auth).json()["items"]
    return next(i for i in items if i["scientific_name"] == "Berberis brevisepala")


@respx.mock
def test_tbia_candidates_by_names(client, auth, pub_id):
    route = respx.get(f"{settings.tbia_api}/api/occurrences").mock(return_value=httpx.Response(200, json={
        "total": 1, "limit": 50, "offset": 0, "items": [{
            "id": "abc", "scientific_name": "Berberis alpicola", "locality": "玉山",
            "recorded_by": "Hayata", "record_number": "12", "institution_code": "TAI",
            "catalog_number": "001", "county": "南投縣"}]}))
    it = _brev(client, auth, pub_id)
    res = client.get(f"/api/items/{it['id']}/specimen-candidates?county=南投縣", headers=auth).json()
    q = route.calls.last.request.url.params
    assert q.get_list("scientific_name") == ["Berberis brevisepala", "Berberis alpicola", "Berberis densifolia"]
    assert q.get("county") == "南投縣"
    row = res["items"][0]
    assert row["display_text"] == "玉山, Hayata 12 (TAI:001)" and row["picked"] is False
    assert row["link"].endswith("/record/abc")

    client.put(f"/api/items/{it['id']}/specimens", headers=auth,
               json=[{"occurrence_id": "abc", "record": row}])
    res = client.get(f"/api/items/{it['id']}/specimen-candidates?q=Hayata", headers=auth).json()
    assert res["items"][0]["picked"] is True and res["names"] == []
    assert route.calls.last.request.url.params.get("q") == "Hayata"


@respx.mock
def test_tbia_down_is_502(client, auth, pub_id):
    respx.get(f"{settings.tbia_api}/api/occurrences").mock(side_effect=httpx.ConnectError("refused"))
    it = _brev(client, auth, pub_id)
    assert client.get(f"/api/items/{it['id']}/specimen-candidates", headers=auth).status_code == 502


@respx.mock
def test_inat_normalized(client, auth, pub_id):
    respx.get(f"{settings.inat_api}/observations").mock(return_value=httpx.Response(200, json={
        "total_results": 1, "results": [{"id": 42, "user": {"login": "moo"}, "observed_on": "2024-01-01",
            "photos": [{"id": 9, "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/9/square.jpg",
                        "attribution": "(c) moo, some rights reserved (CC BY)", "license_code": "cc-by"}]}]}))
    it = _brev(client, auth, pub_id)
    res = client.get(f"/api/items/{it['id']}/image-candidates?source=inat", headers=auth).json()
    p = res["items"][0]
    assert p["url"].endswith("/9/large.jpg") and p["thumb_url"].endswith("/9/medium.jpg")
    assert p["license"] == "cc-by" and p["link"] == "https://www.inaturalist.org/observations/42"


@respx.mock
def test_taieol_via_taicol_taxon(client, auth, pub_id):
    respx.get(f"{settings.taicol_public_api}/name").mock(return_value=httpx.Response(200, json={
        "status": {"code": 200}, "data": [{"taxon": [{"taxon_id": "t0040371", "taicol_name_status": "Accepted"}]}]}))
    tai = respx.get(f"{settings.taieol_api}/taieol_object/taxon_id/t0040371").mock(
        return_value=httpx.Response(200, json={"meta": {}, "data": [{
            "OID": "72ec", "datasetName": "林業及自然保育署", "permanentLink": "https://taieol.tw/muse/digi_object/72ec",
            "scientificName": "Berberis mingetsuensis",
            "associatedMedia": [{"url": "https://data.taieol.tw/files/w960/a.jpg?itok=x",
                                 "licence": "https://creativecommons.org/licenses/by-nc/3.0/tw/",
                                 "authors": "作者：呂勝由"}]}]}))
    it = _brev(client, auth, pub_id)
    res = client.get(f"/api/items/{it['id']}/image-candidates?source=taieol", headers=auth).json()
    assert res["taxon_id"] == "t0040371"
    p = res["items"][0]
    assert p["license"] == "cc-by-nc" and p["attribution"] == "呂勝由, 林業及自然保育署"
    assert p["source_id"] == "72ec:a.jpg"
    assert "Mozilla" in tai.calls.last.request.headers["user-agent"]


def test_image_pick_validation(client, auth, pub_id):
    it = _brev(client, auth, pub_id)
    bad = client.put(f"/api/items/{it['id']}/images", headers=auth,
                     json=[{"source": "inat", "source_id": "1", "url": "file:///etc/passwd"}])
    assert bad.status_code == 422
    ok = client.put(f"/api/items/{it['id']}/images", headers=auth, json=[
        {"source": "inat", "source_id": "1", "url": "https://static.inaturalist.org/a.jpg", "caption": "x"},
        {"source": "taieol", "source_id": "2", "url": "https://data.taieol.tw/b.jpg"},
        {"source": "inat", "source_id": "1", "url": "https://static.inaturalist.org/a.jpg"}])
    assert [i["source_id"] for i in ok.json()["images"]] == ["1", "2"]
