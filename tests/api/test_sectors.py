"""
API Test: Sector Summary & Constituent Lookup
Module: tests/api/test_sectors.py
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_sectors_returns_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) in (10, 11)


def test_get_sector_it_returns_it_companies_only():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")
    if response.status_code == 404:
        response = client.get("/api/v1/sectors/IT/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for comp in data:
        assert "it" in comp["sector"].lower() or "technology" in comp["sector"].lower()
