def _hook(client, **data):
    return client.post("/api/hooks", json={"event": "namespace_published", "data": data})


def test_hook_imports_and_notifies(client, auth, taicol_ok):
    r = _hook(client, email="author@example.org", namespace_id=7, name="Berberidaceae")
    assert r.json() == {"message": "ok"}
    pubs = client.get("/api/publications", headers=auth).json()
    assert len(pubs) == 1 and pubs[0]["namespace_id"] == 7
    notes = client.get("/api/notifications", headers=auth).json()
    assert len(notes) == 1 and "imported" in notes[0]["content"]
    assert notes[0]["publication_id"] == pubs[0]["id"]
    # second publish re-syncs instead of duplicating
    _hook(client, email="author@example.org", namespace_id=7)
    assert len(client.get("/api/publications", headers=auth).json()) == 1
    assert "re-synced" in client.get("/api/notifications", headers=auth).json()[0]["content"]


def test_hook_rejections(client, auth, taicol_ok):
    assert _hook(client, email="nobody@example.org", namespace_id=7).json()["message"] == "no user"
    assert _hook(client, email="author@example.org", namespace_id=8).json()["message"] == "namespace not available"
    assert _hook(client, email="author@example.org").json()["message"] == "invalid data"
    assert client.post("/api/hooks", json={}).json()["message"] == "invalid data"


def test_hook_secret(client, auth, taicol_ok, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "webhook_secret", "s3")
    body = {"event": "e", "data": {"email": "author@example.org", "namespace_id": 7}}
    assert client.post("/api/hooks", json=body).status_code == 401
    assert client.post("/api/hooks?token=s3", json=body).json()["message"] == "ok"


def test_production_requires_strong_secret():
    import pytest
    from pydantic import ValidationError
    from app.config import Settings
    with pytest.raises(ValidationError):
        Settings(app_env="production", secret_key="change-me")
    with pytest.raises(ValidationError):
        Settings(app_env="production", secret_key="dev-secret-change-me")
    assert Settings(app_env="production", secret_key="x" * 40).secret_key == "x" * 40
    assert Settings(app_env="development", secret_key="change-me")  # dev stays easy
