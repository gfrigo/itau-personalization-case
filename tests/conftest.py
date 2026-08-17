from pathlib import Path

import pytest

from itau_purchase_propensity.data.repository import DataRepository

# 5 produtos / 2 categorias, desenhados para que a cota por categoria do cold
# start divirja do ranking puro por trending (ver test_recommender.py).
PRODUCTS_CSV = """product_id,category,price,avg_rating,popularity_score
p_a1,eletronicos,100.0,4.5,0.8
p_a2,eletronicos,50.0,3.0,0.2
p_a3,eletronicos,80.0,4.0,0.5
p_b1,livros,20.0,4.0,0.6
p_b2,livros,15.0,2.5,0.1
"""

EVENTS_CSV = """user_id,product_id,event_type,timestamp
u1,p_a1,view,2026-01-01T00:00:00
u1,p_a1,purchase,2026-01-02T00:00:00
u1,p_b1,view,2026-01-01T00:00:00
u2,p_b1,click,2026-01-03T00:00:00
u2,p_b2,view,2026-01-03T00:00:00
u3,p_a3,purchase,2026-01-03T00:00:00
"""


@pytest.fixture
def repo(tmp_path: Path) -> DataRepository:
    products_path = tmp_path / "products.csv"
    events_path = tmp_path / "events.csv"
    products_path.write_text(PRODUCTS_CSV)
    events_path.write_text(EVENTS_CSV)
    return DataRepository(events_path, products_path, cold_start_window_days=30)


class FakeModel:
    """Score deterministico (interactions*10 + affinity_match) para ranking previsível em teste,
    sem acoplar a suite aos pesos do LogisticRegression treinado."""

    feature_cols = ["interactions", "price", "avg_rating", "popularity_score", "user_affinity_match"]

    def predict_proba(self, feature_rows: list[list[float]]) -> list[float]:
        i = self.feature_cols.index("interactions")
        m = self.feature_cols.index("user_affinity_match")
        return [row[i] * 10 + row[m] for row in feature_rows]


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()
