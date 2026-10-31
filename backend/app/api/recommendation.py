# 라우터를 만들기 위한 도구와 에러 발생 시 돌려줄 응답을 위한 도구
from fastapi import APIRouter, Depends, HTTPException

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# DB 세션 관리 함수, 로그인 유저 확인 함수 가져오기
from app.core.database import get_db
from app.core.auth import get_current_user

# 사용할 테이블 모델
from app.models.user import User
from app.models.profile import SkinProfile
from app.models.product import Product, Ingredient, ProductIngredient

# 응답 형식과 스코어링 엔진
from app.schemas.recommendation import RecommendationResponse
from app.services.recommender import recommend, load_irritants, load_regulated

# 이 파일 안의 API들을 하나로 묶어주는 라우터 생성
router = APIRouter()


def load_products_for_scoring(db: Session, category: str | None = None) -> list[dict]:
    """DB의 제품 + 성분(순번 포함)을 스코어링 엔진이 받는 dict 형태로 변환"""
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.order_by(Product.id).all()
    if not products:
        return []

    # 제품마다 성분을 따로 조회하지 않고, 한 번에 가져와서 제품별로 나눔
    links = (
        db.query(ProductIngredient.product_id, ProductIngredient.position, Ingredient.ingredient_name)
        .join(Ingredient, Ingredient.id == ProductIngredient.ingredient_id)
        .filter(ProductIngredient.product_id.in_([p.id for p in products]))
        .all()
    )
    ingredients_of: dict[int, list[dict]] = {}
    for product_id, position, name in links:
        ingredients_of.setdefault(product_id, []).append({"name": name, "position": position or 0})

    return [
        {
            "id": p.id,
            "product_name": p.product_name,
            "brand": p.brand,
            "category": p.category,
            "main_concerns": p.main_concerns.split(",") if p.main_concerns else [],
            "is_concerns_verified": p.is_concerns_verified,
            "ingredients": sorted(ingredients_of.get(p.id, []), key=lambda i: i["position"]),
        }
        for p in products
    ]


def profile_to_dict(profile: SkinProfile) -> dict:
    return {
        "skin_type": profile.skin_type,
        "is_sensitive": bool(profile.is_sensitive),
        "concerns": profile.concerns.split(",") if profile.concerns else [],
        "preferred_ingredients": profile.preferred_ingredients,
        "avoided_ingredients": profile.avoided_ingredients,
    }


def run_recommendation(
    db: Session, profile: dict, category: str | None = None, include_unverified: bool = False
) -> dict:
    """프로필 dict로 추천 실행 (API와 챗봇이 같이 쓰는 진입점)"""
    products = load_products_for_scoring(db, category)
    return recommend(profile, products, load_irritants(), load_regulated(), include_unverified)


# 추천 API
# 로그인한 유저의 피부 프로필로 스코어링 엔진을 실행
# category: 카테고리 한정 (선택), limit: 추천 목록 최대 개수
# include_unverified: 주력 고민 검수 전 제품도 포함 (개발·데모용, 결과에 검수 여부가 표시됨)
@router.get("", response_model=RecommendationResponse)
def get_recommendations(
        category: str | None = None,
        limit: int = 20,
        include_unverified: bool = False,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    profile = db.query(SkinProfile).filter(SkinProfile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="피부 프로필을 먼저 등록해 주세요")

    result = run_recommendation(db, profile_to_dict(profile), category, include_unverified)
    result["recommended"] = result["recommended"][:max(limit, 0)]
    return result
