# 라우터를 만들기 위한 도구와 에러 발생 시 돌려줄 응답을 위한 도구
from fastapi import APIRouter, Depends, HTTPException

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# DB 세션 관리 함수 가져오기
from app.core.database import get_db

# 로그인한 유저인지 확인하는 함수 가져오기
from app.core.auth import get_current_user

# users, skin_profiles 테이블을 표현한 모델 가져오기
from app.models.user import User
from app.models.profile import SkinProfile

# 프로필 요청/응답 형식 가져오기
from app.schemas.profile import ProfileRequest, ProfileResponse

# 이 파일 안의 API들을 하나로 묶어주는 라우터 생성
router = APIRouter()


# 프로필 등록/수정 API
# current_user: 토큰 검증을 통과한 '로그인한 유저' 객체 (자동으로 주입됨)
@router.post("", response_model=ProfileResponse)
def create_or_update_profile(
        request: ProfileRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    # 1단계: 이 유저의 프로필이 이미 있는지 확인
    existing_profile = db.query(SkinProfile).filter(
        SkinProfile.user_id == current_user.id
    ).first()

    if existing_profile:
        # 2-1단계: 이미 있으면 기존 값들을 새 값으로 덮어쓰기
        existing_profile.skin_type = request.skin_type
        existing_profile.is_sensitive = request.is_sensitive
        existing_profile.concerns = request.concerns
        existing_profile.preferred_ingredients = request.preferred_ingredients
        existing_profile.avoided_ingredients = request.avoided_ingredients

        db.commit()
        db.refresh(existing_profile)
        return existing_profile

    else:
        # 2-2단계: 없으면 새로 생성
        new_profile = SkinProfile(
            user_id=current_user.id,        # 토큰에서 뽑은 유저 id를 그대로 사용
            skin_type = request.skin_type,
            is_sensitive = request.is_sensitive,
            concerns = request.concerns,
            preferred_ingredients = request.preferred_ingredients,
            avoided_ingredients = request.avoided_ingredients,
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile

# 프로필 조회 API
@router.get("", response_model=ProfileResponse)
def get_profile(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    # 로그인한 유저의 프로필을 DB에서 조회
    profile = db.query(SkinProfile).filter(
        SkinProfile.user_id == current_user.id
    ).first()

    # 아직 프로필을 등록 안한 유조라면 404 에러
    if profile is None:
        raise HTTPException(status_code=404, detail="등록된 프로필이 없습니다")

    return profile
