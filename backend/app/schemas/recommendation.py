# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel


# 게이트 탈락 사유 하나 (type: sensitive / banned / avoided)
class GateReason(BaseModel):
    type: str
    ingredient: str
    detail: str


# 성분 경고 하나 (kind: limit 배합 한도 성분 / trace_irritant 민감성에게 소량 들어 있는 자극 성분)
class LimitWarning(BaseModel):
    ingredient: str
    limit_cond: str = ""
    kind: str = "limit"


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
    # main: 주력 고민과 겹침 / contained: 주력은 아니지만 그 고민의 성분이 들어 있음 / none
    match_type: str = "none"
    contained_matched: list[str] = []
    # 주력 근거가 부족한 제품 (순위는 맨 뒤)
    main_basis_insufficient: bool = False
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
