from pydantic import BaseModel


class RecommendationItem(BaseModel):
    product_id: str
    score: float


class RecommendationResponse(BaseModel):
    user_id: str
    cold_start: bool
    items: list[RecommendationItem]
