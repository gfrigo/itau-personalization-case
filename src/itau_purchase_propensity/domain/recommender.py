from dataclasses import dataclass

from itau_purchase_propensity.data.repository import DataRepository
from itau_purchase_propensity.domain.features import compute_features, to_feature_row
from itau_purchase_propensity.ml.model import PropensityModel


@dataclass
class RankedProduct:
    product_id: str
    score: float | None


@dataclass
class RecommendationResult:
    items: list[RankedProduct]
    cold_start: bool


def _trending_key(repo: DataRepository, product_id: str) -> tuple[float, float]:
    return repo.get_trending_score(product_id), repo.products[product_id]["avg_rating"]


def cold_start_ranking(repo: DataRepository, top_n: int) -> list[str]:
    ranked = sorted(
        repo.all_product_ids, key=lambda pid: _trending_key(repo, pid), reverse=True
    )

    best_per_category: dict[str, str] = {}
    for product_id in ranked:
        best_per_category.setdefault(repo.products[product_id]["category"], product_id)

    quota = list(best_per_category.values())
    rest = [product_id for product_id in ranked if product_id not in set(quota)]
    selected = (quota + rest)[:top_n]

    return sorted(selected, key=lambda pid: _trending_key(repo, pid), reverse=True)


def recommend(
    user_id: str,
    repo: DataRepository,
    model: PropensityModel,
    top_n: int,
) -> RecommendationResult:
    cold_start = not repo.is_known_user(user_id)

    if cold_start:
        ranked = cold_start_ranking(repo, top_n)
        items = [
            RankedProduct(product_id=product_id, score=None) for product_id in ranked
        ]
        return RecommendationResult(items=items, cold_start=True)

    rows = [
        to_feature_row(compute_features(repo, user_id, product_id), model.feature_cols)
        for product_id in repo.all_product_ids
    ]
    scores = dict(zip(repo.all_product_ids, model.predict_proba(rows)))
    ranked = sorted(scores, key=lambda pid: scores[pid], reverse=True)[:top_n]
    items = [
        RankedProduct(product_id=product_id, score=scores[product_id])
        for product_id in ranked
    ]

    return RecommendationResult(items=items, cold_start=False)
