from pathlib import Path

import pandas as pd

EVENT_WEIGHTS = {"view": 1.0, "click": 2.0, "add_to_cart": 3.0, "purchase": 5.0}


class DataRepository:
    def __init__(self, events_path: Path, products_path: Path, cold_start_window_days: int = 30):
        events = pd.read_csv(events_path, parse_dates=["timestamp"])
        products = pd.read_csv(products_path)

        self.products = self._build_products(products)
        self.all_product_ids: list[str] = list(self.products.keys())
        self.interaction_counts = self._build_interaction_counts(events)
        self.user_affinity = self._build_user_affinity(events, products)
        self.known_users: set[str] = set(events["user_id"].unique())
        self.trending_scores = self._build_trending_scores(events, cold_start_window_days)

    @staticmethod
    def _build_products(products: pd.DataFrame) -> dict[str, dict]:
        return products.set_index("product_id").to_dict("index")

    @staticmethod
    def _build_interaction_counts(events: pd.DataFrame) -> dict[tuple[str, str], int]:
        return events.groupby(["user_id", "product_id"]).size().to_dict()

    @staticmethod
    def _build_user_affinity(events: pd.DataFrame, products: pd.DataFrame) -> dict[str, str]:
        merged = events.merge(products[["product_id", "category"]], on="product_id", how="left")
        category_counts = merged.groupby(["user_id", "category"]).size().reset_index(name="count")
        top_category = category_counts.sort_values("count", ascending=False).drop_duplicates("user_id")
        return dict(zip(top_category["user_id"], top_category["category"]))

    @staticmethod
    def _build_trending_scores(events: pd.DataFrame, window_days: int) -> dict[str, float]:
        cutoff = events["timestamp"].max() - pd.Timedelta(days=window_days)
        recent = events[events["timestamp"] >= cutoff]
        weights = recent["event_type"].map(EVENT_WEIGHTS).fillna(0.0)
        return recent.assign(weight=weights).groupby("product_id")["weight"].sum().to_dict()

    def get_trending_score(self, product_id: str) -> float:
        return self.trending_scores.get(product_id, 0.0)

    def get_interaction_count(self, user_id: str, product_id: str) -> int:
        return self.interaction_counts.get((user_id, product_id), 0)

    def get_affinity_category(self, user_id: str) -> str | None:
        return self.user_affinity.get(user_id)

    def is_known_user(self, user_id: str) -> bool:
        return user_id in self.known_users
