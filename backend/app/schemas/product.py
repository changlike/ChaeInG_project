# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel

# 성분 정보를 표현하는 형식 (제품 상세 조회에서 함께 보여줄 용도)
class IngredientResponse(BaseModel):
    id: int
    ingredient: str
    efficacy: str | None = None
    caution: str | None = None

    class Config:
        from_attributes = True

# 제품 목록 조회에서 보여줄 간단한 형식 (성분 상세까지는 담지 않음)
class ProductListResponse(BaseModel):
    id: int
    product_name: str
    brand: str | None = None
    category: str | None = None
    skin_type_target: str | None = None

    class Config:
        from_attributes = True

# 제품 상세 조회에서 보여줄 형식 (포함된 성분 리스트까지 담음)
class ProductDetailResponse(BaseModel):
    id: int
    product_name: str
    branch: str | None = None
    category: str | None = None
    skin_type_target: str | None = None
    source_url: str | None = None
    ingredients: list[IngredientResponse] = []      # 이 제품에 포함된 성분들 목록

    class Config:
        from_attributes = True
        