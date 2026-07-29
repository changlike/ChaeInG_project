# 라우터를 만들기 위한 도구와 에러 발생 시 돌려줄 응답을 위한 도구
from fastapi import APIRouter, Depends, HTTPException

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# DB 세션 관리 함수 가져오기
from app.core.database import get_db

# 로그인한 유저인지 확인하는 함수 가져오기
from app.core.auth import get_current_user

# users, products, favorites 테이블을 표현한 모델 가져오기
from app.models.user import User
from app.models.product import Product
from app.models.favorite import Favorite

# 찜하기 요청/응답 형식 가져오기
from app.schemas.favorite import FavoriteRequest, FavoriteResponse

# 이 파일 안의 API들을 하나로 묶어주는 라우터 생성
router = APIRouter()

# 찜하기 API
@router.post("", response_model=FavoriteResponse)
def add_favorite(
        request: FavoriteRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 1단계: 찜하려는 product_id가 실제로 존재하는 제품인지 확인
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if product is None:
        raise HTTPException(status_code=400, detail="제품을 찾을 수 없습니다")

    # 2단계: 이미 찜한 적 있는지 확인 (중복 방지)
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.product_id == request.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 찜한 제품입니다")

    # 3단계: 새 찜 기록 생성 및 저장
    new_favorite = Favorite(
        user_id=current_user.id,
        product_id=request.product_id
    )
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    return new_favorite

# 찜 목록 조회 API
@router.get("", response_model=list[FavoriteResponse])
def get_favorites(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 로그인한 유저가 찜한 목록을 전부 조회
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).all()

    return favorites

# 찜 취소 API
@router.delete("/{product_id}")
def remove_favorite(
        product_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 이 유저가 이 제품을 찜한 기록을 찾음
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.product_id == product_id
    ).first()

    # 찜한 기록이 없다면 404 에러
    if favorite is None:
        raise HTTPException(status_code=404, detail="찜한 기록이 없습니다")

    # 있으면 삭제
    db.delete(favorite)
    db.commit()

    return {"message": "찜이 취소되었습니다"}