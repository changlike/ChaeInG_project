# .env 값을 읽는 곳을 이 파일 하나로 모음
# 다른 파일은 os.getenv를 직접 쓰지 않고 여기서 만든 settings를 가져다 씀
import os
from dotenv import load_dotenv

# .env 파일에 정의된 환경변수를 불러옴
load_dotenv()

# 없으면 서버가 제대로 동작할 수 없는 필수 값들
_REQUIRED = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME", "SECRET_KEY"]


def _validate():
    # DATABASE_URL을 직접 주면(예: 로컬 데모용 SQLite) DB_* 값은 필요 없음
    required = _REQUIRED if not os.getenv("DATABASE_URL") else ["SECRET_KEY"]
    # DB_PASSWORD는 비밀번호 없는 로컬 DB도 있을 수 있어 빈 값을 허용하고, 나머지는 빈 값도 없는 것으로 봄
    missing = [
        name for name in required
        if os.getenv(name) is None or (name != "DB_PASSWORD" and os.getenv(name) == "")
    ]
    if missing:
        # 서버 시작 시점에 바로 멈춰서, 로그인할 때 알아보기 힘든 에러가 나는 일을 막음
        raise RuntimeError(
            f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing)} "
            "(backend/.env.example 참고)"
        )


_validate()


class Settings:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    # 선택: 접속 URL 전체를 직접 지정 (없으면 위 DB_* 값으로 MySQL URL을 조립)
    DATABASE_URL = os.getenv("DATABASE_URL")

    # JWT 서명용 비밀 열쇠, 토큰 암호화 방식, 토큰 유효시간(분)
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

    # 프론트엔드 주소 목록 (콤마로 구분). 배포하면 실제 프론트 주소를 넣어야 함
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]


settings = Settings()
