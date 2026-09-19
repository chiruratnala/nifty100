"""
API Test: Health & Diagnostic Suite
Module: tests/api/test_health.py
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_health_status_and_tables():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "version" in data
    assert "uptime_seconds" in data

    db_counts = data.get("db_row_counts", {})
    assert len(db_counts) >= 10

    for tbl in ["companies", "profitandloss", "balancesheet", "cashflow", "financial_ratios"]:
        assert tbl in db_counts
        assert db_counts[tbl] > 0
