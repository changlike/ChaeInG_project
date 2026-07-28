# 컬럼 타입을 정의할 때 쓰는 도구들
# Boolean: 참/거짓 값 (is_sensitive용, MySQL의 tinyint(1)과 대응됨)
# ForeignKey: 다른 테이블(users)의 id를 참조하기 위한 도구
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

# database.py에서 만들어둔 기본 틀(Base)을 가져옴
from app.core.database import Base

# skin_profiles 테이블을 파이썬 클래스로 표현한 것
class SkinProfile(Base):
    __tablename__ = "skin_profiles"   # 실제 MySQL에 있는 테이블 이름과 정확히 일치해야 함

    # 컬럼 하나하나를 클래스 변수로 표현
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 이 프로필이 "누구의" 프로필인지 users 테이블의 id를 참조 (외래키)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    skin_type = Column(String(20), nullable=False)
    is_sensitive = Column(Boolean, default=False)

    # 콤마로 구분한 문자열로 저장 (ex: "홍조, 모공, 여드름")
    concerns = Column(String(255), nullable=True)
    preferred_ingredients = Column(String(255), nullable=True)
    avoided_ingredients = Column(String(255), nullable=True)
    