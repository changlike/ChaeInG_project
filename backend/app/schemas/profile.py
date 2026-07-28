# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel

# 피부 프로필 등록/수정할 때 유저가 보내야 하는 데이터 형식
class ProfileRequest(BaseModel):
    skin_type: str      # ex: '건성', '지성', '복합성', '수부지', '중성'
    is_sensitive: bool  # 민감성 피부 여부 (True/False)

    # 콤마로 구분한 문자열로 받음 (ex: '여드름, 모공, 홍조')
    concerns: str | None = None
    preferred_ingredients: str | None = None
    avoided_ingredients: str | None = None

# 프로필 등록/조회 성공했을 때 서버가 돌려줄 응답 형식
class ProfileResponse(BaseModel):
    id: int
    user_id: int
    skin_type: str
    is_sensitive: bool
    concerns: str | None = None
    preferred_ingredients: str | None = None
    avoided_ingredients: str | None = None

    # DB 모델(SQLAlchemy 객체)을 그대로 응답으로 반환할 수 있게 해주는 설정
    class Config:
        from_attributes = True
