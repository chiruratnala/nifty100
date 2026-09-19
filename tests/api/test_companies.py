"""
API Test: Companies Catalog & Profile
Module: tests/api/test_companies.py
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_list_companies_returns_92_records():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92


def test_get_company_profile_tcs_success():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert "company_profile" in data
    assert "latest_year_kpis" in data


def test_get_company_profile_invalid_returns_404():
    response = client.get("/api/v1/companies/INVALID_TICKER_XYZ")
    assert response.status_code == 404
    assert "detail" in response.json()
