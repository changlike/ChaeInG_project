# .env에 적어둔 값을 읽어오기 위한 도구
import os

# 라우터에서 이 함수를 의존성으로 쓰기 위한 도구 (Depends), 인증 실패 시 에러 응답을 위한 도구 (HTTPException)
from fastapi import Depends, HTTPException

# 요청 헤더의 "Authorization: Bearer 토큰값"에서 토큰 문자열만 자동으로 꺼내주는 도구
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# JWT 토큰을 해석(디코딩)하고, 위조/만료 여부를 검사하기 위한 도구
from jose import jwt, JWTError

# DB 세션 관리 함수 가져오기
from app.core.database import get_db

# users 테이블을 표현한 모델 가져오기
from app.models.user import User

# .env 파일에서 비밀 열쇠 값을 꺼내옴 (로그인 API에서 토큰 만들 때 쓴 것과 반드시 동일해야 함)
SECRET_KEY = os.getenv("SECRET_KEY")

# .env 파일에서 암호화 방식을 꺼내옴, 없으면 기본값 HS256 사용
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# HTTPBearer: 요청 헤더에서 "Bearer 토큰값" 형태의 토큰을 그대로 꺼내주는 단순한 인증 방식
# (username/password 로그인 폼이 아니라, 이미 발급된 토큰 문자열 하나만 받는 방식)
bearer_scheme = HTTPBearer()


# 로그인한 유저인지 확인하는 함수
# credentials: 요청 헤더에서 자동으로 꺼내진 토큰 정보 (bearer_scheme이 미리 꺼내줌)
# db: DB 세션 (get_db가 미리 만들어서 넣어줌)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    # credentials 객체 안에 들어있는 실제 토큰 문자열만 꺼냄
    token = credentials.credentials

    # 토큰이 유효하지 않을 때 공통으로 사용할 에러 (401: 인증 실패)
    credentials_exception = HTTPException(
        status_code=401,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1단계: 토큰 해석 시도
    try:
        # SECRET_KEY로 위조 여부를 확인하고, 만료 시간도 자동으로 검사함
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 토큰을 만들 때 넣었던 "sub" 값(이메일)을 꺼냄
        email = payload.get("sub")

        # sub 값이 없다면 잘못된 토큰이므로 에러 처리
        if email is None:
            raise credentials_exception

    # 토큰이 위조되었거나, 형식이 잘못되었거나, 만료된 경우 여기로 옴
    except JWTError:
        raise credentials_exception

    # 2단계: 이메일로 실제 DB에 있는 유저인지 확인
    user = db.query(User).filter(User.email == email).first()

    # DB에 해당 유저가 없다면 (예: 탈퇴한 유저) 에러 처리
    if user is None:
        raise credentials_exception

    # 3단계: 모든 검증 통과 → 실제 User 객체를 반환
    # 이 반환값은 이 함수를 사용하는 API 함수 안에서 그대로 사용 가능
    return user