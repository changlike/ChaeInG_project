# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel, field_validator

# 고민(concerns)으로 고를 수 있는 고정 목록
# 제품 쪽 "주력 고민" 태깅에도 동일한 값을 쓰게 될 공유 어휘라 자유 텍스트 대신 이 목록으로만 받음
ALLOWED_CONCERNS = ["여드름/트러블", "모공", "홍조", "건조/보습", "미백/톤", "주름/탄력"]

# 피부 프로필 등록/수정할 때 유저가 보내야 하는 데이터 형식
class ProfileRequest(BaseModel):
    skin_type: str      # ex: '건성', '지성', '복합성', '수부지', '중성'
    is_sensitive: bool  # 민감성 피부 여부 (True/False)

    # 고정 목록(ALLOWED_CONCERNS) 중에서 고른 항목들의 배열로 받음 (ex: ['여드름/트러블', '모공'])
    concerns: list[str] | None = None
    preferred_ingredients: str | None = None
    avoided_ingredients: str | None = None

    # concerns에 고정 목록에 없는 값이 들어오면 요청 자체를 막음 (오타/이상한 값 방지)
    @field_validator("concerns")
    @classmethod
    def validate_concerns(cls, value):
        if value is None:
            return value
        invalid = [v for v in value if v not in ALLOWED_CONCERNS]
        if invalid:
            raise ValueError(f"허용되지 않은 고민 항목입니다: {invalid}")
        return value

# 프로필 등록/조회 성공했을 때 서버가 돌려줄 응답 형식
class ProfileResponse(BaseModel):
    id: int
    user_id: int
    skin_type: str
    is_sensitive: bool
    concerns: list[str] | None = None
    preferred_ingredients: str | None = None
    avoided_ingredients: str | None = None

    # DB 모델(SQLAlchemy 객체)을 그대로 응답으로 반환할 수 있게 해주는 설정
    class Config:
        from_attributes = True
