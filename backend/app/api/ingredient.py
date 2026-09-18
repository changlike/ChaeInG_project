# 라우터를 만들기 위한 도구와 에러 발생 시 돌려줄 응답을 위한 도구
from fastapi import APIRouter, Depends, HTTPException

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# DB 세션 관리 함수 가져오기
from app.core.database import get_db

# ingredients 테이블을 표현한 모델 가져오기
from app.models.product import Ingredient

# 성분 응답 형식 가져오기
from app.schemas.product import IngredientResponse, IngredientDetailResponse

# 이 파일 안의 API들을 하나로 묶어주는 라우터 생성
router = APIRouter()

# 성분 검색 API
# q: 성분명 검색어 (예: ?q=나이아신)
@router.get("", response_model=list[IngredientResponse])
def search_ingredients(q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Ingredient)

    if q:
        query = query.filter(Ingredient.ingredient_name.ilike(f"%{q}%"))

    return query.all()

# 성분 상세 조회 API
# {ingredient_id}: URL 경로에 실제 숫자가 들어오는 자리 (ex: /api/ingredients/5)
@router.get("/{ingredient_id}", response_model=IngredientDetailResponse)
def get_ingredient_detail(ingredient_id: int, db: Session = Depends(get_db)):
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()

    if ingredient is None:
        raise HTTPException(status_code=404, detail="성분을 찾을 수 없습니다")

    # ingredient.products는 relationship 덕분에 이 성분이 들어간 제품들을 자동으로 가져옴
    return ingredient
