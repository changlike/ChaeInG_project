# 환경변수(.env 파일)를 읽어오기 위한 모듈
import os
from dotenv import load_dotenv

# DB 연결 및 세션 관리를 위한 SQLALchemy 핵심 모듈
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env 파일에 정의된 환경변수를 불러옴
load_dotenv()

# 환경변수에서 DB 접속 정보를 가져옴 (민감정보는 코드에 직접 작성하지 않음)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# SQLAlchemy가 요구하는 형식으로 DB 접속 URL 조립
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

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