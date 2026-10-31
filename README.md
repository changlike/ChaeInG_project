# ChaeInG

> 사용자의 **피부 타입 · 피부 고민 · 선호/기피 성분**을 바탕으로 기초 스킨케어 제품을 추천하는 **성분 기반** 웹 서비스

리뷰·인기순이 아니라 **화장품 성분**을 기준으로 추천하고, 그 추천의 **판단 근거를 항상 명확히 보여주는 것**이 핵심 가치입니다.

- 개발 기간: 2026-07-13 ~ (진행 중)
- 개발 방식: 설계(요구사항 · 스코어링 로직 · DB)는 직접 확정하고, 구현은 AI(Claude Code)와 협업하여 리뷰하며 진행

---

## 프로젝트 범위

| 구분 | 내용 |
|---|---|
| 포함 | 토너, 에센스, 세럼, 앰플, 로션, 크림, 선크림, 클렌저 (기초 스킨케어) |
| 제외 | 색조 화장품, 향수, 헤어 제품, 바디 제품 |

## 주요 기능

| # | 기능 | 상태 |
|---|---|---|
| 1 | 회원가입 / 로그인 / 로그아웃 (JWT) | 완료 (공통 인증 가드) |
| 2 | 피부 프로필 등록 / 조회 / 수정 / 삭제 | 완료 |
| 3 | 즐겨찾기 (찜하기 / 목록 / 취소) | 완료 |
| 4 | 화장품 검색 (제품명 / 브랜드 / 카테고리) | 완료 |
| 5 | 성분 검색 (성분명 검색 + 해당 성분이 든 제품 역조회) | 완료 (성분 효능·주의사항 설명 데이터는 미확보) |
| 6 | 맞춤 추천 (Rule-Based 스코어링 엔진 + 추천 화면) | 완료 (주력 고민 태그 검수 진행 중) |
| 7 | 추천 챗봇 (RAG, 엔진 결과 설명) | 설계 확정, 구현 예정 |

### 피부 프로필 항목

- **피부 타입** (택1): 건성 / 지성 / 복합성 / 수부지 / 중성
- **민감성 여부**: 피부 타입과 별도 축(체크박스)
- **피부 고민** (다중 선택): 여드름/트러블, 모공, 홍조, 건조/보습, 미백/톤, 주름/탄력
- **선호 / 기피 성분**: 자유 텍스트 입력

## 추천 방식

**Rule-Based 스코어링**으로 판단하며, LLM은 그 결과를 자연어로 *설명*하는 역할만 합니다. (LLM이 직접 추천을 판단하지 않음)

1. **게이트 (통과/탈락)** — 민감성 사용자 + 자극 유발 성분, 규제 금지 성분, 사용자가 적은 기피 성분 포함 제품은 탈락. 탈락 제품도 버리지 않고 **사유와 함께** 보여줌
2. **가산점** — 사용자의 피부 고민과 제품의 "주력 고민" 태그가 겹치는 개수 표시 (예: "고민 3개 중 2개 매칭") 후 매칭 수 순 정렬. 선호 성분은 점수에 더하지 않고 동점일 때 순서만 정함
3. **경고 문구** — 배합 한도가 있는 성분 포함 시 참고용 경고만 표시 (점수 무관)

제품의 "주력 고민"은 **성분→고민 사전 + 규칙**(`concern_tagger.py`)으로 초안을 만들고 사람이 검수한 값만 추천에 씁니다. 같은 계열 성분(예: 히알루론산 변형 10종)은 점수에 1회만 반영합니다.

챗봇은 ① 성분 Q&A (FAISS 검색 기반 RAG), ② 추천 요청 (스코어링 엔진 호출) 두 갈래로 구성될 예정입니다.

## 설계 의사결정

| 결정 | 이유 |
|---|---|
| LLM이 아닌 Rule-Based 스코어링으로 추천 판단 | 추천 근거를 항상 설명할 수 있어야 한다는 핵심 가치를 지키기 위해. 챗봇은 결과를 설명만 함 |
| 게이트(통과/탈락)와 가산점을 분리 | "피부 타입이 안 맞는데 성분 점수가 높아 추천되는" 논리적 모순을 막기 위해. 안전 관련 항목은 감산이 아닌 하드 게이트로 처리 |
| v1에서 피부 타입 게이트 제외 | 수집한 제품 데이터의 타깃이 대부분 "모든 피부"라 변별력이 없음. 프로필의 피부 타입은 계속 수집하여 추후 적용 |
| 민감성을 피부 타입과 별도 축으로 분리 | 건성이면서 민감성인 경우 등 복합적인 상태를 표현하기 위해 |
| 피부 고민 어휘를 사용자·제품이 공유 | 사용자가 고른 고민과 제품 태그가 정확히 매칭되도록. 점수 환산 없이 매칭 개수를 그대로 표시 |
| 선호/기피 성분은 자유 텍스트 | 성분 종류가 너무 많아 고정 목록으로 만들기 어려움 |
| 한도 성분은 경고만 표시 | 제품 데이터에 실제 함량(%)이 없어 한도 초과 여부를 판정할 수 없음 |
| 제품 데이터는 수기 입력 | 자동 크롤링은 이용약관상 하지 않기로 결정 |

## 기술 스택

| 영역 | 기술 |
|---|---|
| Frontend | React 19, React Router 7, Vite |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | MySQL 8 (Docker, PyMySQL) |
| LLM / RAG (예정) | LangChain, FAISS, LLM API |
| 버전 관리 | Git, GitHub |

## 프로젝트 구조

```
ChaeInG_project/
├─ backend/
│  ├─ app/
│  │  ├─ api/        # 라우터 (auth, profile, product, favorite, ingredient, recommendation)
│  │  ├─ core/       # DB 연결, 인증 유틸
│  │  ├─ models/     # SQLAlchemy 모델
│  │  ├─ schemas/    # Pydantic 스키마
│  │  ├─ services/   # 성분 파서, 주력 고민 태거, 스코어링 엔진(recommender)
│  │  └─ main.py
│  ├─ scripts/     # CSV 적재, 고민 초안 생성, 검수값 반영
│  ├─ tests/      # pytest (엔진 단위 테스트 + SQLite API 테스트)
│  └─ requirements.txt
├─ frontend/
│  └─ src/
│     ├─ api/        # 백엔드 호출 함수
│     ├─ components/ # NavBar, RequireAuth(인증 가드), Input
│     └─ pages/      # Login, Signup, Profile, Recommend, Products, Favorites, Ingredients
├─ data/             # 제품/성분 CSV, 성분→고민 사전, 자극 성분 목록, 규제 성분
└─ docs/             # prd, api-spec, erd, user-flow, design-system, daily-log
```

## API 개요

| Prefix | 설명 |
|---|---|
| `/api/auth` | 회원가입, 로그인 |
| `/api/profile` | 피부 프로필 CRUD |
| `/api/products` | 제품 목록 / 검색 |
| `/api/favorites` | 즐겨찾기 |
| `/api/ingredients` | 성분 검색 / 성분별 제품 조회 |
| `/api/recommendations` | 내 프로필 기반 추천 (게이트 → 고민 매칭 → 경고) |

서버 실행 후 `http://localhost:8000/docs` (Swagger UI)에서 상세 명세를 확인할 수 있습니다. 설계 문서는 [`docs/api-spec.md`](docs/api-spec.md)를 참고하세요.

## 실행 방법

### Database (Docker)

```bash
# backend/.env 를 먼저 준비 (backend/.env.example 참고, DB_USER=root)
docker compose --env-file backend/.env up -d
```

### Backend

```bash
cd backend
pip install -r requirements.txt
# .env 에 DB 접속 정보 / JWT 시크릿 설정 필요 (.env.example 참고)

alembic upgrade head                      # 테이블 생성 (마이그레이션 적용)
python -m scripts.load_products --dry-run # CSV 파싱 결과만 확인
python -m scripts.load_products           # 제품/성분 데이터 DB 적재

python -m scripts.tag_concerns            # 주력 고민 초안 CSV 생성 (data/main_concerns_draft.csv)
python -m scripts.apply_concerns          # 검수 완료(reviewed 표시) 행만 DB 반영

python -m uvicorn app.main:app --reload
```

### 테스트

```bash
cd backend
python -m pytest -q    # DB 없이 실행 (API 테스트는 메모리 SQLite 사용)
```

### Docker 없이 데모 실행 (SQLite)

`DATABASE_URL`을 지정하면 MySQL 대신 해당 DB를 씁니다. 테이블은 모델 정의로 생성합니다.

```bash
cd backend
export DATABASE_URL=sqlite:///demo.db SECRET_KEY=dev-secret
python -c "from app.core.database import Base, engine; from app.models import user, profile, product, favorite; Base.metadata.create_all(engine)"
python -m scripts.load_products
python -m scripts.apply_concerns --with-drafts   # 검수 전 초안도 반영 (화면에서 '검수 전 태그'로 표시)
python -m uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 데이터 소스

- **제품 / 성분**: 올리브영 상품 페이지를 직접 확인하여 CSV로 수기 입력 (이용약관상 자동 크롤링은 하지 않음). 현재 5개 카테고리(에센스/세럼/앰플, 스킨/토너, 로션, 크림, 미스트/오일) 105개 제품 확보 (`data/ChaeInG_data - 통합.csv`). 104개 적재 완료(중복 1개 제외), 주력 고민은 규칙 초안 생성 후 검수 중.
- **금지 / 한도 성분**: 공공데이터포털 "식품의약품안전처_화장품 사용제한 원료정보" API → `data/regulated_ingredients.csv` (엔진 연동 완료, 데이터 수집 대기)
- **자극 유발 성분(민감성 게이트)**: `data/irritant_ingredients.csv` — 향료, 알레르기 유발 향료 성분, 앞쪽 함량 구간의 알코올, 에센셜 오일 (초안, 검수 필요)
- **고민-성분 효능 데이터**: 미확보 — 제품 단위 수동 태깅(`main_concerns`)으로 우회

## 진행 현황

- [x] 회원가입 / 로그인
- [x] 피부 프로필 CRUD
- [x] 즐겨찾기
- [x] 화장품 검색
- [x] 성분 검색
- [x] 제품 데이터 DB 적재
- [ ] 주력 고민 태깅 (규칙·초안 완료, 사람 검수 진행 중)
- [x] 스코어링 엔진 + 추천 API + 추천 화면
- [x] 로그아웃 · 공통 인증 가드 · 상단 네비게이션
- [ ] RAG 챗봇 (설계 완료)
- [x] 테스트 (pytest 50개: 파서, 태거, 엔진, 검수 반영, API 흐름)
- [ ] 배포 (토큰 저장을 `localStorage` → httpOnly 쿠키로 전환 검토)
- [ ] 문서화 (erd · api-spec · user-flow · daily-log 작성 완료, design-system은 TBD)

## 문서

- [인수인계(Handoff)](docs/handoff.md) · [데이터/LLM 원칙](docs/data-and-llm-policy.md)
- [PRD](docs/prd.md) · [API 명세](docs/api-spec.md) · [ERD](docs/erd.md) · [사용자 흐름](docs/user-flow.md) · [디자인 시스템](docs/design-system.md) · [작업 일지](docs/daily-log.md)
