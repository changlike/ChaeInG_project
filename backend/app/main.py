# FastAPI 도구에서 서버를 만드는 도구(FastAPI 클래스)를 가져옴
from fastapi import FastAPI
from app.api import auth

# 본 프로젝트의 서버를 하나 만듦
# 앞으로 이 app이라는 이름으로 서버에 여러 기능(API)을 하나씩 추가할 예정
app = FastAPI()

# auth.py에 있는 API들을 "/api/auth"라는 주소 밑에 연결
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# @app.get("/"): "누군가 우리 서버의 기본 주소('/')로 GET 요청(조회 요청)을 보내면"의 의미
@app.get("/")
def read_root():
    # 위 요청이 들어오면 실행되는 함수 (응답은 JSON 딕셔너리 형태로 반환)
    return{"message": "Hello ChaeInG"}
