"""Endpoint tests for the RazorGuard FastAPI backend."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import database as database_package
from backend.database import database
from backend.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client


def transaction_payload() -> dict:
    return {
        "transaction_id": "DEMO-0001",
        "amount": 313.30,
        "hour": 3,
        "transaction_frequency": 6,
        "average_amount": 272.06,
        "recipient_is_new": 0,
        "device_changed": 1,
        "location_changed": 0,
        "transaction_type": "transfer",
        "account_age_days": 134,
        "previous_failed_transactions": 0,
    }


def test_health_and_cors(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": "loaded"}
    assert response.headers["access-control-allow-origin"] == "*"


def test_predict_transactions_and_analytics(client: TestClient) -> None:
    prediction = client.post("/predict", json=transaction_payload())

    assert prediction.status_code == 200
    result = prediction.json()
    assert result["transaction_id"] == "DEMO-0001"
    assert 0 <= result["fraud_probability"] <= 1
    assert result["risk_level"] in {"Safe", "Suspicious", "High Risk"}
    assert result["reasons"]
    assert result["recommended_action"]

    transactions = client.get("/transactions")
    assert transactions.status_code == 200
    assert len(transactions.json()) == 1
    assert transactions.json()[0]["transaction_id"] == "DEMO-0001"

    analytics = client.get("/analytics")
    assert analytics.status_code == 200
    assert analytics.json()["total_predictions"] == 1


def test_predict_rejects_unknown_feature(client: TestClient) -> None:
    payload = transaction_payload()
    payload["unexpected_feature"] = 1

    response = client.post("/predict", json=payload)

    assert response.status_code == 422