# .env에 적어둔 값을 읽어오기 위한 도구
import os

# 라우터를 만들기 위한 도구와 에러 발생 시 돌려줄 응답을 위한 도구
from fastapi import APIRouter, Depends, HTTPException

# DB 세션 타입을 지정하기 위한 도구
from sqlalchemy.orm import Session

# 비밀번호 암호화를 위한 도구
from passlib.context import CryptContext

# 토큰 유효시간을 계산하기 위한 날짜/시간 도구
from datetime import datetime, timedelta

# JWT 토큰을 만들고 해석하기 위한 도구
from jose import jwt

# DB 세션 관리 함수 가져오기
from app.core.database import get_db

# users 테이블을 표현한 모델 가져오기
from app.models.user import User

# 회원가입/로그인 요청·응답 형식 가져오기
from app.schemas.user import SignupRequest, SignupResponse, LoginRequest, LoginResponse

# 비밀번호 암호화 방식 설정 (bycrypt 방식 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# .env 파일에서 비밀 열쇠 값을 꺼내옴
SECRET_KEY = os.getenv("SECRET_KEY")

# .env 파일에서 암호화 방식을 꺼내옴, 없으면 기본값 HS256 사용
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# .env 파일에서 토큰 유효시간을 꺼내옴, 문자열로 읽히므로 숫자로 변환
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", 60))

# 이 파일 안의 API들을 하나로 묶어주는 라우터 생성
router = APIRouter()

# 회원가입 API
# response_model: 이 함수가 반환하는 데이터를 SignupResponse 형식에 맞춰서 정리해줌
@router.post("/signup", response_model=SignupResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # 1단계: 이미 가입된 이메일인지 확인
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        # 이미 있으면 에러 응답 (400: 잘못된 요청)
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다")

    # 2단계: 비밀번호 암호화 (원본 비밀번호는 저장 안함)
    hashed_password = pwd_context.hash(request.password)

    # 3단계: User 모델 형태로 새 유저 객체 생성
    new_user = User(
        email = request.email,
        password = hashed_password,
        nickname = request.nickname
    )

    # 4단계: DB에 실제로 저장
    db.add(new_user)    # "DB 저장할" 준비하기"
    db.commit()     # "진짜로 저장하기"
    db.refresh(new_user)    # 저장 후 DB가 자동생성한 값(id 등)을 다시 받아옴

    return new_user


# 로그인 API
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # 1단계: 입력받은 이메일로 DB에서 유저를 찾아봄
    user = db.query(User).filter(User.email == request.email).first()

    # 2단계: 유저가 아예 없거나,비밀번호가 안 맞으면 로그인 실패 처리
    # pwd_context.verify(입력한 비밀번호, DB에 저장된 암호화 비밀번호) -> 서로 맞는 짝인지 확인하기
    if not user or not pwd_context.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다")

    # 3단계: 여기까지 통과했다면 진짜 본인이 맞다는 뜻으로 토큰을 만들어줌
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    # sub(subject): 이 토큰이 '누구의 것'인지 표시하는 값
    # exp(expire): 이 토큰이 언제 만료되는지 표시하는 값
    token_data = {"sub": user.email, "exp": expire}
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # 4단계: 만들어진 토큰을 응답으로 돌려줌
    return {"access_token": access_token, "token_type": "bearer"}
