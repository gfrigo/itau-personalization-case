from itau_purchase_propensity.data.repository import DataRepository


def compute_features(repo: DataRepository, user_id: str, product_id: str) -> dict[str, float]:
    product = repo.products[product_id]
    affinity_category = repo.get_affinity_category(user_id)

    return {
        "interactions": repo.get_interaction_count(user_id, product_id),
        "price": product["price"],
        "avg_rating": product["avg_rating"],
        "popularity_score": product["popularity_score"],
        "user_affinity_match": int(affinity_category == product["category"]),
    }


def to_feature_row(features: dict[str, float], feature_cols: list[str]) -> list[float]:
    return [features[col] for col in feature_cols]
