import pytest
from fastapi.testclient import TestClient

from itau_purchase_propensity.main import app

KNOWN_USER_ID = "u_0078"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_end_to_end(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recommendations_known_user_end_to_end(client):
    response = client.get(f"/recommendations/{KNOWN_USER_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == KNOWN_USER_ID
    assert body["cold_start"] is False
    assert len(body["items"]) > 0

    scores = [item["score"] for item in body["items"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 for score in scores)


def test_recommendations_unknown_user_falls_back_to_cold_start_end_to_end(client):
    response = client.get("/recommendations/user-that-does-not-exist")

    assert response.status_code == 200
    body = response.json()
    assert body["cold_start"] is True
    assert len(body["items"]) > 0
