import json
import os
import pathlib

os.environ["DATABASE_URL"] = "sqlite:////tmp/biotaeditor-test.sqlite"
os.environ["TAICOL_SKIP_OWNERSHIP"] = "false"
os.environ["WEBHOOK_SECRET"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.sources import http as source_http  # noqa: E402

FIX = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def payload():
    return json.loads((FIX / "namespace_example.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    source_http.clear_cache()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth(client):
    r = client.post("/api/auth/signup", json={"email": "Author@Example.org", "password": "secret123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def taicol_ok(monkeypatch, payload):
    """TaiCOL says the user owns namespace 7 and serves the fixture for it."""
    from app.sources import taicol
    state = {"payload": payload}
    monkeypatch.setattr(taicol, "available_namespaces", lambda email: [7])
    monkeypatch.setattr(taicol, "fetch_namespace", lambda nid: state["payload"])
    return state


@pytest.fixture
def pub_id(client, auth, taicol_ok):
    r = client.post("/api/publications/import", json={"namespace_id": 7}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()["publication_id"]
