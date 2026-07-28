# 라우터를 만들기 위한 도구와 에러 발생 시 돌려줄 응답을 위한 도구
from fastapi import APIRouter, Depends, HTTPException

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# DB 세션 관리 함수 가져오기
from app.core.database import get_db

# products, ingredients 테이블을 표현한 모델 가져오기
from app.models.product import Product

# 제품 응답 형식 가져오기
from app.schemas.product import ProductListResponse, ProductDetailResponse

# 이 파일 안의 API들을 하나로 묶어주는 라우터 생성
router = APIRouter()

# 제품 목록 조회 API
# category, skin_type: URL 뒤에 ?category=토너 처럼 붙이는 선택적 검색 조건
# = None으로 기본값을 줘서, 조건 없이 호출하면 전체 목록을 반환하게 함
@router.get("", response_model=list[ProductListResponse])
def get_products(
        category: str | None = None,
        skin_type: str | None = None,
        db: Session = Depends(get_db)
):
    # 1단계: 기본 쿼리 준비 (아직 실행 안함, 조건만 쌓는 중)
    query = db.query(Product)

    # 2단계: category가 주어졌다면, 그 조건을 쿼리에 추가
    if category:
        query = query.filter(Product.category == category)

    # 3단계: skin_type이 주어졌다면, 그 조건도 추가
    if skin_type:
        query = query.filter(Product.skin_type_target == skin_type)

    # 4단계: 최종적으로 쌓인 조건대로 실제 DB 조회 실행
    products = query.all()

    return products

# 제품 상세 조회 API
# {products_id}: URL 경로에 실제 숫자가 들어오는 자리 (ex: /api/products/5)
@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    # product_id로 제품 하나를 조회
    product = db.query(Product).filter(Product.id == product_id).first()

    # 해당 id의 제품이 없다면 404 에러
    if product is None:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다")

    # product.ingredients는 relationship 덕분에 자동으로 연결된 성분 목록을 가져옴
    return product


