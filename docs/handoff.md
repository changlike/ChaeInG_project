# 인수인계 문서 (Handoff)

> 작성: 2026-10-15 / 다른 로컬(집)에서 작업을 이어가기 위한 문서
> 이 문서만 읽고 환경을 복원하고, 바로 다음 작업을 시작할 수 있도록 작성함

---

## 0. 한 줄 요약

- **지금 위치**: 로드맵 2단계(데이터 파이프라인) 완료. 제품 99개가 DB에 적재됨.
- **사용자가 하던 일**: 적재에서 제외된 **5개 제품의 성분표를 CSV에서 직접 수정 중** (아래 4번).
- **다음 작업**: 수정 후 재적재 → 3단계(`main_concerns` 태깅) → 4단계(스코어링 엔진 + 테스트).

---

## 1. 새 로컬에서 환경 복원하기

> `.env`는 git에 올라가지 않음. 새 로컬에서는 **직접 만들어야 함**.

### 1-1. 준비물
| 항목 | 버전 / 비고 |
|---|---|
| Python | 3.11.x (이 프로젝트는 3.11.9에서 확인됨) |
| Node.js | 20 이상 (개발 PC는 24.x) |
| Docker Desktop | MySQL 컨테이너용. 실행 중이어야 함 |
| 로컬 MySQL | **설치돼 있다면 3306 포트 충돌**. 서비스 중지 또는 `docker-compose.yml`의 포트를 `3307:3306`으로 변경하고 `.env`의 `DB_HOST`를 맞춤 |

### 1-2. 순서

```bash
# 1) 저장소 받기
git clone https://github.com/changlike/ChaeInG_project.git
cd ChaeInG_project

# 2) 백엔드 가상환경 + 패키지
python -m venv .venv
.venv\Scripts\activate            # Windows (mac/linux: source .venv/bin/activate)
pip install -r backend/requirements.txt

# 3) backend/.env 만들기 (아래 1-3 참고)

# 4) DB 컨테이너 실행 (프로젝트 루트에서)
docker compose --env-file backend/.env up -d

# 5) 테이블 생성 + 데이터 적재 (backend 폴더에서)
cd backend
alembic upgrade head
python -m scripts.load_products --dry-run     # 먼저 파싱 결과 확인
python -m scripts.load_products               # 실제 적재

# 6) 서버 실행
python -m uvicorn app.main:app --reload       # http://localhost:8000/docs

# 7) 프론트 (다른 터미널)
cd frontend
npm install
npm run dev                                   # http://localhost:5173
```

### 1-3. `backend/.env` 만들기
`backend/.env.example`을 복사해서 채움. **값은 새로 정해서 쓰면 됨** (집 PC의 DB는 새 컨테이너이므로 기존 값과 같을 필요 없음).

| 키 | 설명 |
|---|---|
| `DB_USER` | **반드시 `root`** (`docker-compose.yml`이 root 계정만 생성함) |
| `DB_PASSWORD` | 컨테이너 root 비밀번호가 됨. 처음 컨테이너를 만들 때의 값으로 고정되므로, 나중에 바꾸려면 `docker compose down -v` 필요 |
| `DB_HOST` | `localhost` |
| `DB_NAME` | 예: `skincare_db` |
| `SECRET_KEY` | JWT 서명용 임의의 긴 문자열 |
| `ALGORITHM` | `HS256` |
| `TOKEN_EXPIRE_MINUTES` | `60` |
| `CORS_ORIGINS` | `http://localhost:5173` (생략 가능, 기본값 동일) |

필수 키(`DB_*`, `SECRET_KEY`)가 없으면 서버가 시작 시 에러 메시지와 함께 멈춤 → 정상 동작임.

### 1-4. 복원 확인 체크리스트
- [ ] `docker ps`에 `chaeing-mysql`이 `healthy`
- [ ] `alembic current` → `0002 (head)`
- [ ] `load_products` 결과: 제품 99개 (또는 CSV 수정 후 그 이상)
- [ ] `http://localhost:8000/api/products`에서 제품이 나옴
- [ ] 프론트에서 회원가입 → 로그인 → 프로필 저장 → 찜하기 동작

---

## 2. 작업 내역 (이번 세션: 2026-10-15)

### 2-1. 점검과 의사결정
- 폴더 전체를 읽고 보완점을 도출 (보안, 데이터, 문서, 테스트, 프론트)
- 작업 방식이 산만하다는 피드백을 받아 **단계(0~6) 기준으로 재정리**하고 한 번에 한 단계만 진행

### 2-2. 커밋 이력 (origin/main 기준 6개 추가)
| 커밋 | 내용 |
|---|---|
| docs | erd / api-spec / user-flow / design-system / daily-log 작성, prd·README 갱신, 데이터·LLM 원칙 문서 |
| refactor | `core/config.py` 통합, CORS 환경변수화, `utcnow` 제거, 비밀번호 정책, LIKE 이스케이프, requirements 고정 |
| data | `통합.csv` 추가 (105개 제품) |
| chore | MySQL을 Docker Compose로 전환 |
| feat | Alembic 도입, 스키마 확장 (0001 기준선, 0002) |
| feat | 성분표 파서와 CSV 적재 스크립트 |

### 2-3. 코드 변경 상세
| 영역 | 파일 | 내용 |
|---|---|---|
| 설정 | `backend/app/core/config.py` (신규) | `.env` 로딩 단일화, 필수값 누락 시 시작 단계에서 `RuntimeError` |
| 설정 | `core/database.py`, `core/auth.py`, `api/auth.py`, `main.py` | `settings` 사용으로 변경 |
| 검색 | `backend/app/core/search.py` (신규) | `%`, `_`, `\`를 일반 글자로 처리하는 `escape_like` |
| 인증 | `schemas/user.py` | 비밀번호 정책: 8자 이상, 72바이트 이하, 영문+숫자 |
| 모델 | `models/product.py` | `main_concerns`, `is_concerns_verified`, `position`, `amount_note`, UNIQUE 제약 |
| 모델 | `models/favorite.py`, `models/profile.py` | UNIQUE 제약 |
| 마이그레이션 | `backend/migrations/` (신규) | Alembic. `env.py`는 앱의 engine과 `Base.metadata` 사용 |
| 파서 | `backend/app/services/ingredient_parser.py` (신규) | 성분표 분리, 함량 분리, URL 정리 |
| 적재 | `backend/scripts/load_products.py` (신규) | CSV → DB 멱등 적재 |
| 인프라 | `docker-compose.yml` (신규) | `mysql:8.0`, 볼륨, 헬스체크, `backend/.env` 값 사용 |

### 2-4. 확인된 동작
- uvicorn 기동, DB 연결, CORS 프리플라이트 정상
- `q=%` 검색이 전체 목록을 반환하지 않음
- 약한 비밀번호 가입 시 422
- 마이그레이션 0001 ↔ 0002 업/다운 왕복, `alembic check`에서 모델과 차이 없음
- 적재 2회 실행 시 중복 없이 갱신만 됨

---

## 3. 현재 DB 상태 (이 PC 기준)

| 항목 | 값 |
|---|---|
| 제품 | 99개 (에센스/세럼/앰플 18, 스킨/토너 20, 크림 19, 로션 21, 미스트/오일 21) |
| 성분 | 878개 고유 성분, 연결 3,457건 |
| 비어 있는 값 | `products.main_concerns` 전부, `ingredients.efficacy/caution` 전부 |
| 개발 데이터 | 이전 17개 제품과 계정 데이터는 덮어써서 **없음** (사용자 동의) |

> 집 PC의 DB는 새 컨테이너이므로 위 상태는 `load_products`로 재현해야 함. **회원/프로필/찜 데이터는 옮겨지지 않음.**

---

## 4. 진행 중인 작업: 제외된 제품 5개 CSV 수정

`load_products`는 자동 분리가 위험한 성분표를 **적재에서 제외**하고 경고를 출력함. 사용자가 아래 5개를 `data/ChaeInG_data - 통합.csv`에서 직접 수정 중.

| CSV 행 | 제품 | 문제 | 수정 방향 |
|---|---|---|---|
| 7 | 히알루 B5 수분탄력 세럼 | `[히알루 세럼] … [히알루 크림] …`처럼 세트 처방이 한 칸에 섞임 | 제품에 해당하는 처방 하나만 남기고 `[ ]` 표기 제거 |
| 25 | 어성초 77 히알루론산 수분 진정 토너 | `[크림]` 표기가 섞임 | 위와 같음 |
| 11 | 레티놀 시카 모공 흔적 앰플 | 성분 사이에 `*3X RETINOL COMPLEX 1% : …` 설명이 섞임 | 설명 문구 제거, 성분만 남김 |
| 15 | 피디알엔 히알루론산 캡슐 100 세럼 | `* 피디알엔: …` 주석이 섞임 | 주석 제거 |
| 50 | DMT 페이셜 크림 | 주석 섞임 (`:` 포함) | 주석 제거 |

- 제외 판정 규칙: 성분표에 `[` `]` 또는 `:`가 있으면 제외 (`review_reason` 함수)
- 이 외에 **63행은 49행과 같은 제품·같은 URL인 진짜 중복**이므로 CSV에서 삭제해도 됨
- 수정 후 확인:
  ```bash
  cd backend
  python -m scripts.load_products --dry-run   # 경고가 사라졌는지 확인
  python -m scripts.load_products
  ```
- 수정 완료 시 기대 결과: 제품 **104개** (105개 − 중복 1개)

> 주의: CSV를 두 PC에서 따로 수정하면 충돌함. 수정 후 **반드시 커밋·푸시**하고 집에서 `git pull` 할 것.

---

## 5. 다음 할 일 (로드맵)

| 단계 | 목표 | 완료 기준 | 상태 |
|---|---|---|---|
| 0 | 설계 확정 | 결정 사항이 `prd.md`에 정리됨 | 완료 |
| 1 | 기반 정리 | config 통합, 보안·정책 | 완료 |
| 2 | 데이터 파이프라인 | 빈 DB에서 스크립트로 적재 | 완료 (제외 5개 수정 대기) |
| **3** | **`main_concerns` 태깅** | **검수 완료된 값이 DB에 있음** | **다음** |
| 4 | 스코어링 엔진 + 테스트 | 게이트/가산점/경고 테스트 통과 | 대기 |
| 5 | 화면 | 로그아웃, 공통 인증 가드, 추천 화면 | 대기 |
| 6 | 챗봇 | RAG, 추천 결과 설명 | 대기 |

### 3단계 진행 현황 (2026-10-16)
- 결정: **성분→고민 사전 + 규칙 방식**, `TOP_N=20`, 판정 결과는 바로 DB에 넣지 않고 사람 검수 후 반영
- 완료: 사전 초안 `data/ingredient_concern_map.csv`(약 100행, 전부 미검수), 규칙 `app/services/concern_tagger.py`, 생성 스크립트 `scripts/tag_concerns.py`, 검수용 `data/main_concerns_draft.csv`
- 실행: `cd backend && python -m scripts.tag_concerns`
- 규칙: 후보 점수(strong 2 + weak 1) 상위 **2개만** 선택 (`MAX_CONCERNS=2`)
- 초안 결과(99개, 상위 2개 적용): 건조/보습 83, 주름/탄력 30, 미백/톤 22, 홍조 18, 여드름/트러블 9, 모공 1, 판정 없음 4 (1순위는 건조/보습 68)
- **문제**: 건조/보습이 여전히 지배적 (히알루론산 변형 여러 개가 각각 점수를 올림), 모공은 사전이 빈약 → 같은 계열 성분은 1회만 점수 반영하는 보정 필요
- 남은 일: 규칙 보완 → 사전 검수(사용자) → 검수 확정값을 DB `main_concerns`에 반영하는 스크립트 → 테스트

### 3단계 원래 계획 (참고)
원칙은 `docs/data-and-llm-policy.md` 참고. 요약:
1. 입력은 제품명+성분표만. 출력은 6개 고민 어휘로 제한 (여드름/트러블, 모공, 홍조, 건조/보습, 미백/톤, 주름/탄력)
2. 태깅 결과와 함께 **근거 성분**을 저장, 근거가 성분표에 실제 있는지 자동 검증
3. LLM 산출물은 초안 상태(`is_concerns_verified = False`)로 저장, 사람이 검수한 것만 `True`
4. 일회성 오프라인 배치. 모델명·프롬프트 버전·생성일 기록
5. 미결정: 초안 저장 위치(CSV 컬럼 vs DB 테이블), 모델·프롬프트, 미백/주름은 식약처 기능성 고시 성분으로 규칙 기반 가능한지

### 4단계 상세 (스코어링 + 테스트)
- 구조: **게이트(민감성 유발 성분, 금지 성분) → 가산점(고민 매칭 개수) → 경고(한도 성분)**
- 위치: `backend/app/services/` (현재 비어 있음), 테스트는 `backend/tests/`
- 선행 필요: 금지/한도 성분 테이블 + 식약처 공공데이터 연동, 자극 성분 목록
- 테스트에 포함할 것: `%` 검색이 전체를 반환하지 않는지, 비밀번호 정책, 즐겨찾기 중복, 성분 파서(`1,2-헥산다이올`, 괄호 쉼표, 공백 구분)
- 테스트 환경: pytest + 별도 테스트 DB (Docker 컨테이너의 다른 데이터베이스) 권장

---

## 6. 미결정 사항 / 알려진 이슈

| 항목 | 내용 |
|---|---|
| 피부 타입 적합도 | 결정: 마케팅 값(`skin_type_target`)과 자체 판단 값 분리, 가산점으로 사용. 구현·컬럼은 미정. 그때까지 필터 UI 제외 |
| 성분 순서 활용 | `position`은 저장함. 1% 이하는 순서가 함량이 아니므로 앞쪽 N개만 쓸지 미정 |
| 성분 효능/주의사항 | 공공 API에서 못 찾음. `docs/data-and-llm-policy.md`의 조사 결과 참고 |
| 금지/한도 성분 | 테이블·연동 없음 (식약처 사용제한 원료정보 API, 개발계정 필요) |
| `확인` 컬럼 | CSV의 `확인`(o/O)은 **데이터 확인 표시**로 해석해 사용하지 않음. 의미가 다르면 수정 필요 |
| 토큰 저장 | `localStorage`. 배포 전 httpOnly 쿠키 전환 검토 (후순위) |
| 페이지네이션 | 미적용. 문서로만 기록 |
| 프론트 | 로그아웃 버튼 없음, 인증 확인이 페이지마다 중복(공통화 예정), 회원가입 422 메시지가 일반 문구 |
| `concerns` 저장 | 콤마 문자열. 별도 테이블/JSON 전환은 추후 검토 |
| API 확인 | 새 스키마에서 `/api/products` 등 API를 아직 호출해 확인하지 않음 (4단계 테스트에서 확인) |
| 줄바꿈 경고 | git이 `LF will be replaced by CRLF` 경고를 냄. `.gitattributes`를 두면 정리 가능 (미적용) |

---

## 7. 작업 규칙 (CLAUDE.md 요약 + 합의된 방식)

- **`.env` / `.env.*` 파일은 읽거나 열지 않음** (내용이 필요하면 사용자에게 물어봄)
- AI 협업 원칙: 설계는 사용자가 확정하고, 코드는 AI가 초안 → 사용자가 리뷰하며 이해 ("모르는 구현이 하나도 없어야 한다")
- 한 번에 한 단계씩 진행하고, 단계마다 **완료 기준**을 먼저 말함
- 새로 발견한 문제는 현재 단계에 끼워 넣지 말고 `docs/daily-log.md`의 "다음 할 일"에 기록
- 커밋은 논리 단위로 분리 (docs / backend / data)

---

## 8. 참고 문서

| 문서 | 내용 |
|---|---|
| [prd.md](prd.md) | 요구사항, 스코어링 설계, 로드맵, 설계 재정비 이슈 |
| [erd.md](erd.md) | 현재 DB 구조와 한계 |
| [api-spec.md](api-spec.md) | 구현된 API 명세 |
| [user-flow.md](user-flow.md) | 화면 흐름, 챗봇 흐름(설계) |
| [data-and-llm-policy.md](data-and-llm-policy.md) | 데이터 소스 조사, LLM 채움 원칙 10개 |
| [daily-log.md](daily-log.md) | 날짜별 작업 일지와 다음 할 일 |
| [design-system.md](design-system.md) | TBD |
