# ChaeInG

> 사용자의 **피부 타입 · 피부 고민 · 선호/기피 성분**을 바탕으로 기초 스킨케어 제품을 추천하는 **성분 기반** 웹 서비스

리뷰·인기순이 아니라 **화장품 성분**을 기준으로 추천하고, 그 추천의 **판단 근거를 항상 명확히 보여주는 것**이 핵심 가치입니다.

## 서비스 소개

**이름의 의미** — 개발자 이름의 `Chae`와, 채(彩, 채색 채)의 뜻을 합쳐 *change(변화)* 와 *색을 알아본다* 는 두 의미를 담았습니다. 지금은 스킨케어 서비스지만 색조 화장품으로 확장할 수 있고, 여기서 말하는 "색"은 퍼스널 컬러뿐 아니라 **자신의 피부 타입**도 포함합니다.

**만든 이유** — 올리브영에서 일하며, 인스타 인기템을 그대로 사거나 "홍조인데 뭐가 좋아요?"라고 묻는 고객이 많다는 것을 느꼈습니다. 사람마다 맞는 제품의 기준이 다르지만 짧은 응대 시간에 일일이 판단하기는 어렵습니다. 기존 플랫폼은 판매 중심이라 리뷰나 브랜드 설명에 의존할 뿐, *"잡티에 좋은 스킨 추천해줘, 근데 00 성분은 빼고"* 같은 직접적인 요구를 들어주는 서비스는 드뭅니다. ChaeInG는 이 부분을 겨냥합니다.

**AI 활용 방향** — 추천 *판단*은 규칙 기반 스코어링이 하고, LLM은 사용자 요청 해석과 추천 결과 설명 등 *응답 생성*을 맡습니다. 챗봇 또는 역할을 나눈 에이전트 오케스트레이션 구조로 확장하며, 사람이 검수한 정보만 제공합니다.

## 로드맵

| 단계 | 내용 |
|---|---|
| **v1 (진행 중)** | 올리브영 수기 수집 약 100개(5개 카테고리 × 20개)를 추천 범위로, 프로필 기반 추천 상위 3개와 근거 제시 |
| v1.5 | LLM 연동: 자연어 요청("잡티에 좋은데 00 빼고") 해석, 추천 결과 설명 생성. 웹 vs 채팅 UI 결정 |
| 이후 | 데이터 확대, 공공데이터 기반 성분 사전·RAG, 색조 등 카테고리 확장 |

- 개발 기간: 2026-07-13 ~ (진행 중)
- 개발 방식: 설계(요구사항 · 스코어링 로직 · DB)는 직접 확정하고, 구현은 AI(Claude Code)와 협업하여 리뷰하며 진행

---

## 프로젝트 범위

| 구분 | 내용 |
|---|---|
| v1 포함 | 토너, 에센스/세럼/앰플, 로션, 크림, 미스트/오일 (5개 카테고리, 올리브영 수기 수집) |
| 추후 | 선크림, 클렌저, 색조 화장품 |
| 제외 | 향수, 헤어 제품, 바디 제품 |

## 주요 기능

| # | 기능 | 상태 |
|---|---|---|
| 1 | 회원가입 / 로그인 / 로그아웃 (JWT) | 완료 (공통 인증 가드) |
| 2 | 피부 프로필 등록 / 조회 / 수정 / 삭제 | 완료 |
| 3 | 즐겨찾기 (찜하기 / 목록 / 취소) | 완료 |
| 4 | 화장품 검색 (제품명 / 브랜드 / 카테고리) | 완료 |
| 5 | 성분 검색 (성분명 검색 + 해당 성분이 든 제품 역조회) | 완료 (성분 효능·주의사항 설명 데이터는 미확보) |
| 6 | 맞춤 추천 (Rule-Based 스코어링 엔진 + 추천 화면) | 완료 (주력 고민 태그 검수 진행 중) |
| 7 | LLM 연동 (자연어 요청 해석, 추천 결과 설명, 챗봇/에이전트 구조) | 방향 확정, 구현 예정 |

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

최종적으로는 정렬된 결과 중 **상위 3개**를 근거와 함께 제시합니다. LLM 연동은 추천 요청(스코어링 엔진 호출 후 설명 생성)을 우선하고, 성분 Q&A(RAG)는 공공데이터 성분 사전을 갖춘 뒤로 미룹니다.

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
| LLM (예정) | LLM API (구성 방식은 구현 시 확정) |
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
- **금지 / 한도 성분**: 공공데이터포털 "식품의약품안전처_화장품 사용제한 원료정보" 연동은 v1 범위에서 제외(추후 확장). 엔진에는 `data/regulated_ingredients.csv`를 읽는 자리만 있고 현재 비어 있음
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
- [ ] 추천 상위 3개 제시
- [ ] LLM 연동 (자연어 요청 해석, 결과 설명)
- [x] 테스트 (pytest 50개: 파서, 태거, 엔진, 검수 반영, API 흐름)
- [ ] 배포 (토큰 저장을 `localStorage` → httpOnly 쿠키로 전환 검토)
- [ ] 문서화 (erd · api-spec · user-flow · daily-log 작성 완료, design-system은 TBD)

## 문서

- [인수인계(Handoff)](docs/handoff.md) · [데이터/LLM 원칙](docs/data-and-llm-policy.md)
- [PRD](docs/prd.md) · [API 명세](docs/api-spec.md) · [ERD](docs/erd.md) · [사용자 흐름](docs/user-flow.md) · [디자인 시스템](docs/design-system.md) · [작업 일지](docs/daily-log.md)
