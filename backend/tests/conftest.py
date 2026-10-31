# API 테스트용 공통 설정
# 실제 MySQL 대신 메모리 SQLite를 쓰므로 Docker/DB 없이도 API 흐름을 확인할 수 있음
import os

# config.py는 import 시점에 필수 환경변수를 검사하므로, 앱을 import하기 전에 테스트용 값을 넣어 둠
# (실제 .env 값이 있으면 그대로 쓰고, 없을 때만 채움. DB 접속은 아래에서 SQLite로 바꿔치기함)
for key, value in {
    "DB_USER": "test", "DB_PASSWORD": "", "DB_HOST": "localhost",
    "DB_NAME": "test", "SECRET_KEY": "test-secret-key",
}.items():
    os.environ.setdefault(key, value)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
# 테이블 등록을 위해 모델을 모두 import
from app.models import user, profile, product, favorite  # noqa: F401


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """회원가입 + 로그인 후 Authorization 헤더 반환"""
    client.post("/api/auth/signup", json={"email": "u@example.com", "password": "abcd1234", "nickname": "u"})
    res = client.post("/api/auth/login", json={"email": "u@example.com", "password": "abcd1234"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
