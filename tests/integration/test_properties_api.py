import json
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_properties_search_integration_header_and_body():
    # request that should match the "test" mock rows
    resp = client.get("/properties/search?q=test&page=1&limit=5")
    assert resp.status_code == 200
    # header present
    assert "x-total-count" in resp.headers
    assert int(resp.headers["x-total-count"]) == 2
    body = resp.json()
    assert body["status"] == 200
    assert body["page"] == 1
    assert body["limit"] == 5
    assert body["total"] == 2
    assert body["total_pages"] == 1
    ids = [r["id"] for r in body["results"]]
    assert "prop-006" in ids and "prop-007" in ids

def test_properties_search_pagination_integration():
    # page 2 with limit 2 should return the expected ids from the mock
    resp = client.get("/properties/search?page=2&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["limit"] == 2
    # total should match mock count (7)
    assert body["total"] == 7
    assert body["total_pages"] == 4
    ids = [r["id"] for r in body["results"]]
    # page 2 expected to include prop-003 and prop-004
    assert "prop-003" in ids and "prop-004" in ids
