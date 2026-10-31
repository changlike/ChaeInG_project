# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel


# 게이트 탈락 사유 하나 (type: sensitive / banned / avoided)
class GateReason(BaseModel):
    type: str
    ingredient: str
    detail: str


# 배합 한도 성분 경고 하나
class LimitWarning(BaseModel):
    ingredient: str
    limit_cond: str = ""


# 추천/탈락 제품 공통 정보
class RecommendedProductBase(BaseModel):
    id: int
    product_name: str
    brand: str | None = None
    category: str | None = None
    main_concerns: list[str] = []
    is_concerns_verified: bool


# 추천된 제품 (게이트 통과)
class RecommendedProduct(RecommendedProductBase):
    matched_concerns: list[str]
    match_count: int
    total_concerns: int
    preferred_hits: list[str] = []
    warnings: list[LimitWarning] = []


# 게이트에서 탈락한 제품 (왜 빠졌는지도 근거로 보여줌)
class ExcludedProduct(RecommendedProductBase):
    reasons: list[GateReason]


class RecommendationResponse(BaseModel):
    recommended: list[RecommendedProduct]
    excluded: list[ExcludedProduct]
    # 주력 고민 검수가 안 돼서 추천 대상에서 빠진 제품 수
    skipped_unverified: int
