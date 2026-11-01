import copy


def test_import_creates_items(client, auth, pub_id, payload):
    r = client.get(f"/api/publications/{pub_id}", headers=auth)
    pub = r.json()
    assert pub["title"] == payload["title"]
    assert pub["n_items"] == len(payload["group"]) == 14
    assert len(pub["literatures"]) == len(payload["literatures"])
    genus = pub["items"][0]
    assert genus["scientific_name"] == "Berberis" and genus["rank"] == ["Genus", "屬"]
    brev = next(i for i in pub["items"] if i["scientific_name"] == "Berberis brevisepala")
    assert brev["n_synonyms"] == 2


def test_import_twice_is_exist(client, auth, pub_id):
    r = client.post("/api/publications/import", json={"namespace_id": 7}, headers=auth)
    assert r.json()["status"] == "exist" and r.json()["publication_id"] == pub_id


def test_import_not_owned(client, auth, taicol_ok):
    r = client.post("/api/publications/import", json={"namespace_id": 99}, headers=auth)
    assert r.status_code == 403


def test_other_user_cannot_see(client, auth, pub_id):
    t = client.post("/api/auth/signup", json={"email": "x@y.org", "password": "secret123"}).json()["token"]
    assert client.get(f"/api/publications/{pub_id}", headers={"Authorization": f"Bearer {t}"}).status_code == 404


def test_search_names_include_synonyms(client, auth, pub_id):
    items = client.get(f"/api/publications/{pub_id}", headers=auth).json()["items"]
    brev = next(i for i in items if i["scientific_name"] == "Berberis brevisepala")
    full = client.get(f"/api/items/{brev['id']}", headers=auth).json()
    assert full["search_names"] == ["Berberis brevisepala", "Berberis alpicola", "Berberis densifolia"]


def test_sync_keeps_picks_and_edits(client, auth, pub_id, taicol_ok, payload):
    items = client.get(f"/api/publications/{pub_id}", headers=auth).json()["items"]
    sp = next(i for i in items if i["scientific_name"] == "Berberis brevisepala")
    gone = next(i for i in items if i["scientific_name"] == "Berberis aristatoserrulata")
    iid = sp["id"]

    client.put(f"/api/items/{iid}/specimens", headers=auth, json=[
        {"occurrence_id": "occ-1", "record": {"locality": "合歡山", "county": "南投縣",
                                              "recorded_by": "Lu", "record_number": "1",
                                              "institution_code": "TAI", "catalog_number": "9"}}])
    client.put(f"/api/items/{iid}/images", headers=auth, json=[
        {"source": "inat", "source_id": "5", "url": "https://static.inaturalist.org/photos/5/large.jpg"}])
    client.patch(f"/api/items/{iid}", headers=auth, json={"note": "my own note"})

    new = copy.deepcopy(payload)
    new["group"] = [g for g in new["group"] if g["name_id"] != gone["name_id"]]
    for g in new["group"]:
        if g["name_id"] == sp["name_id"]:
            g["note"] = "upstream note"
            g["description"] = "upstream description"
    new["group"].append({**new["group"][-1], "name_id": 999999, "name": "<i>Berberis nova</i>",
                         "synonyms": []})
    taicol_ok["payload"] = new

    counts = client.post(f"/api/publications/{pub_id}/sync", headers=auth).json()
    assert counts == {"created": 1, "updated": 13, "deleted": 1}

    full = client.get(f"/api/items/{iid}", headers=auth).json()
    assert full["note"] == "my own note"               # local edit wins
    assert full["description"] == "upstream description"  # untouched field follows TaiCOL
    assert [s["occurrence_id"] for s in full["specimens"]] == ["occ-1"]
    assert full["specimens"][0]["display_text"] == "合歡山, Lu 1 (TAI:9)"
    assert len(full["images"]) == 1

    reverted = client.post(f"/api/items/{iid}/revert", headers=auth, json={"fields": ["note"]}).json()
    assert reverted["note"] == "upstream note" and reverted["edited_fields"] == []


def test_reorder_and_literatures(client, auth, pub_id):
    items = client.get(f"/api/publications/{pub_id}", headers=auth).json()["items"]
    ids = [i["id"] for i in items][::-1]
    r = client.put(f"/api/publications/{pub_id}/items/order", headers=auth, json={"ids": ids})
    assert [i["id"] for i in r.json()["items"]] == ids
    assert client.put(f"/api/publications/{pub_id}/items/order", headers=auth,
                      json={"ids": ids[:-1]}).status_code == 422
    r = client.put(f"/api/publications/{pub_id}/literatures", headers=auth,
                   json=[{"citation": "B"}, {"citation": "A", "reference_id": 1}])
    assert [x["citation"] for x in r.json()] == ["B", "A"]
