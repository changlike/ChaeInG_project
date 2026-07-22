# 컬럼 타입을 정의할 때 쓰는 도구들
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func

# database.py에서 만들어둔 기본 틀(Base)을 가져옴
from app.core.database import Base

# users 테이블을 파이썬 클래스로 표현한 것
# 이 클래스 하나 = "테이블 하나"라고 생각
class User(Base):
    __tablename__ = "users" # 실제 MySQL에 있는 테이블 이름과 정확히 일치해야 함

    # 컬럼 하나하나를 클래스 변수로 표현
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
