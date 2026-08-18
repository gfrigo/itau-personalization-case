from fastapi import FastAPI
from fastapi.testclient import TestClient

from itau_purchase_propensity.api.routes.recommendations import router


def make_client(repo, model) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.state.repository = repo
    app.state.model = model
    return TestClient(app)


def test_get_recommendations_known_user(repo, fake_model):
    client = make_client(repo, fake_model)

    response = client.get("/recommendations/u1")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "u1"
    assert body["cold_start"] is False
    assert [item["product_id"] for item in body["items"]] == [
        "p_a1",
        "p_b1",
        "p_a2",
        "p_a3",
        "p_b2",
    ]


def test_get_recommendations_unknown_user_is_cold_start(repo, fake_model):
    client = make_client(repo, fake_model)

    response = client.get("/recommendations/ghost")

    assert response.status_code == 200
    body = response.json()
    assert body["cold_start"] is True
    assert len(body["items"]) > 0
    for item in body["items"]:
        assert "product_id" in item
        assert "score" in item
