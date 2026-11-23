# 챗봇 API 요청/응답 형식
from pydantic import BaseModel, Field

from app.schemas.recommendation import ExcludedProduct, RecommendedProduct


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    # 직전 응답의 understood를 클라이언트가 그대로 돌려보냄 (서버는 받은 값을 다시 검증함)
    previous_conditions: dict | None = None


class Explanation(BaseModel):
    product_id: int
    text: str


class EvidenceItem(BaseModel):
    ingredient: str
    concern: str


class ProductEvidence(BaseModel):
    product_id: int
    items: list[EvidenceItem] = []


class ChatResponse(BaseModel):
    understood: dict            # 검증된 조건 (다음 요청의 previous_conditions로 사용)
    confirmation: str           # "이렇게 이해했어요 — ..." (코드가 만든 확인 문구)
    reply: str | None = None    # 안내 문구 (범위 밖 질문, 고민을 더 물어볼 때, 결과 없음)
    needs_input: bool = False
    recommendations: list[RecommendedProduct] = []
    explanations: list[Explanation] = []
    evidence: list[ProductEvidence] = []   # 카드별 근거 성분 (성분 태그표에서 가져온 값)
    excluded: list[ExcludedProduct] = []
    notices: list[str] = []
