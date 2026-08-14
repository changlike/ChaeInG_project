# FastAPI 도구에서 서버를 만드는 도구(FastAPI 클래스)를 가져옴
from fastapi import FastAPI
# CORS 정책을 관리해주는 도구를 가져옴
# 다른 출처(프론트엔드 주소)에서의 요청을 허용하기 위해 필요함
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, profile, product, favorite

# 본 프로젝트의 서버를 하나 만듦
# 앞으로 이 app이라는 이름으로 서버에 여러 기능(API)을 하나씩 추가할 예정
app = FastAPI()

# 프론트엔드(React) 개발 서버 주소에서 오는 요청을 허용하는 설정
# 이 목록에 없는 주소에서 오는 요청은 브라우저가 차단함
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 허용할 출처 목록
    allow_credentials=True,     # 쿠키, 인증 정보 등을 포함한 요청 허용
    allow_methods=["*"],        # GET, POST 등 모든 HTTP 메서트 허용
    allow_headers=["*"],        # 모든 요청 헤더 허용
)

# auth.py에 있는 API들을 "/api/auth"라는 주소 밑에 연결
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(product.router, prefix="/api/products", tags=["product"])

app.include_router(favorite.router, prefix="/api/favorites", tags=["favorite"])

# @app.get("/"): "누군가 우리 서버의 기본 주소('/')로 GET 요청(조회 요청)을 보내면"의 의미
@app.get("/")
def read_root():
    # 위 요청이 들어오면 실행되는 함수 (응답은 JSON 딕셔너리 형태로 반환)
    return{"message": "Hello ChaeInG"}
