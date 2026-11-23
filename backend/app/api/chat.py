# 챗봇 API: 문장 하나를 받아 해석 → 규칙 추천 → 카드용 정형 결과를 돌려줌
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.recommendation import profile_to_dict
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.profile import SkinProfile
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import run_chat

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(
        body: ChatRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    profile = db.query(SkinProfile).filter(SkinProfile.user_id == current_user.id).first()
    # 프로필이 없어도 대화로 고민을 말하면 추천할 수 있음
    return run_chat(db, body.message, body.previous_conditions, profile_to_dict(profile) if profile else None)
