# 데이터 형식(자료형) 검증을 자동으로 해주는 도구
from pydantic import BaseModel, EmailStr

# 회원가입할 때 "유저가 보내야 하는 데이터 형식"을 정의
class SignupRequest(BaseModel):
    email: EmailStr     # EmailStr: 이메일 형식이 맞는지 자동으로 검사해줌
    password: str
    nickname: str

# 회원가입 성공했을 때 "서버가 돌려줄 응답 형식"을 정의
class SignupResponse(BaseModel):
    id: int
    email: str
    nickname: str
    # 주의: password는 절대 응답에 포함 안 시킴 (보안관리 차원)

# 로그인할 때 유저가 보내야 하는 데이터 형식
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 로그인 성공했을 때 서버가 돌려줄 응답 형식
class LoginResponse(BaseModel):
    access_token: str   # 발급된 JWT 토큰
    token_type: str     # 토큰 종류 표시, 보통 'bearer'라고 고정해서 씀