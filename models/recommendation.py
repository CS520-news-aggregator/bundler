from typing import List
import uuid
from pydantic import BaseModel, Field


class RecommendationQuery(BaseModel):
    post_ids: List[str]


class PostRecommendation(BaseModel):
    post_id: str
    date: str


class Recommendation(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    user_id: str
    post_recommendations: List[PostRecommendation]
