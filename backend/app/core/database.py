# 환경변수 설정값 (.env를 읽는 곳은 config.py 하나)
from app.core.config import settings

# DB 연결 및 세션 관리를 위한 SQLALchemy 핵심 모듈
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLAlchemy가 요구하는 형식으로 DB 접속 URL 조립
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}/{settings.DB_NAME}"
)

# DB와의 연결 통로(engine) 생성
engine = create_engine(DATABASE_URL)

# DB 세션(요청 단위의 대화 창구)을 생성하는 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 이후 정의할 모든 테이블(모델)이 상속받는 기본 클래스
Base = declarative_base()

# API 요청마다 DB 세션(대화창)을 생성하고, 요청 처리가 끝나면 세션을 종료하는 의존성 함수
# FastAPI가 각 API 함수 실행 시 자동으로 호출함
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()