"""
API Test: Screener Filter & Boundary Conditions
Module: tests/api/test_screener.py
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_screener_min_roe_filter():
    min_roe_val = 15.0
    response = client.get(f"/api/v1/screener?min_roe={min_roe_val}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert row["return_on_equity_pct"] >= min_roe_val


def test_screener_invalid_parameter_returns_400():
    response = client.get("/api/v1/screener?max_de=-0.5")
    assert response.status_code == 400
    assert "detail" in response.json()
