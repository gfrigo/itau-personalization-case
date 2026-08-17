import logging

from fastapi import APIRouter, Request

from itau_purchase_propensity.api.schemas.recommendation import RecommendationItem, RecommendationResponse
from itau_purchase_propensity.core.config import config
from itau_purchase_propensity.domain.recommender import recommend

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
def get_recommendations(user_id: str, request: Request) -> RecommendationResponse:
    result = recommend(
        user_id=user_id,
        repo=request.app.state.repository,
        model=request.app.state.model,
        top_n=config.top_n_recommendations,
    )

    logger.info(
        "recommendation_served",
        extra={
            "extra_fields": {
                "user_id": user_id,
                "cold_start": result.cold_start,
            }
        },
    )

    return RecommendationResponse(
        user_id=user_id,
        cold_start=result.cold_start,
        items=[RecommendationItem(product_id=item.product_id, score=item.score) for item in result.items],
    )
