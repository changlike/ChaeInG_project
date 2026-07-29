# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel

# 제품 정보 형식은 이미 만들어둔 걸 재사용
from app.schemas.product import ProductListResponse

# 찜하기 요청할 때 유저가 보내야 하는 데이터 형식
class FavoriteRequest(BaseModel):
    product_id: int

# 찜 목록 조회할 때 서버가 돌려줄 응답 형식
class FavoriteResponse(BaseModel):
    id: int
    product: ProductListResponse    # 찜한 제품의 정보를 통째로 포함

    class Config:
        from_attributes = True