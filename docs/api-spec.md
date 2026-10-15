# API 명세 (현재 구현 기준)

> 기준: `backend/app/api/` (2026-10-15). 서버 실행 후 `http://localhost:8000/docs`(Swagger)에서도 확인 가능.

- Base URL: `http://localhost:8000`
- 인증이 필요한 API는 헤더에 `Authorization: Bearer <access_token>` 필요 → 토큰이 없거나 유효하지 않으면 `401`

## Auth — `/api/auth`

| Method | Path | 인증 | 설명 |
|---|---|---|---|
| POST | `/signup` | - | 회원가입 |
| POST | `/login` | - | 로그인, JWT 발급 |
| GET | `/me` | ✔ | 내 정보 확인 (토큰 검증용) |

**POST /signup**
```json
// Request
{ "email": "user@example.com", "password": "...", "nickname": "채인" }
// Response 200
{ "id": 1, "email": "user@example.com", "nickname": "채인" }
```
- `400` 이미 가입된 이메일
- `422` 비밀번호 정책 위반 (8자 이상, 72바이트 이하, 영문+숫자 각 1개 이상)

**POST /login**
```json
// Request
{ "email": "user@example.com", "password": "..." }
// Response 200
{ "access_token": "<JWT>", "token_type": "bearer" }
```
- `401` 이메일 또는 비밀번호 불일치
- 토큰 payload: `sub`(이메일), `exp`(기본 60분, `TOKEN_EXPIRE_MINUTES`)

## Profile — `/api/profile` (모두 인증 필요)

| Method | Path | 설명 |
|---|---|---|
| POST | `` | 프로필 등록 (이미 있으면 수정) |
| GET | `` | 내 프로필 조회, 없으면 `404` |
| DELETE | `` | 내 프로필 삭제, `204` / 없으면 `404` |

```json
// POST Request / GET Response
{
  "skin_type": "건성",            // 건성/지성/복합성/수부지/중성 (서버 검증 없음)
  "is_sensitive": false,
  "concerns": ["여드름/트러블", "건조/보습"],  // 허용: 여드름/트러블, 모공, 홍조, 건조/보습, 미백/톤, 주름/탄력
  "preferred_ingredients": "나이아신아마이드, 히알루론산",
  "avoided_ingredients": "알코올"
}
```
- `concerns`에 허용 목록 밖의 값이 있으면 `422`
- 응답에는 `id`, `user_id`가 추가로 포함됨

## Products — `/api/products` (인증 불필요)

| Method | Path | 설명 |
|---|---|---|
| GET | `` | 제품 목록. 쿼리: `category`(정확 일치), `skin_type`(정확 일치), `q`(제품명 부분 일치) |
| GET | `/{product_id}` | 제품 상세 (성분 목록 포함), 없으면 `404` |

목록 응답 항목: `id, product_name, brand, category, skin_type_target`
상세 응답: 위 + `source_url`, `ingredients[]` (`id, ingredient_name, efficacy, caution`)

## Ingredients — `/api/ingredients` (인증 불필요)

| Method | Path | 설명 |
|---|---|---|
| GET | `` | 성분 검색. 쿼리: `q`(성분명 부분 일치) |
| GET | `/{ingredient_id}` | 성분 상세 + 이 성분이 든 제품 목록, 없으면 `404` |

## Favorites — `/api/favorites` (모두 인증 필요)

| Method | Path | 설명 |
|---|---|---|
| POST | `` | 찜하기. Body: `{ "product_id": 1 }` |
| GET | `` | 내 찜 목록 (제품 정보 포함) |
| DELETE | `/{product_id}` | 찜 취소 |

- POST: `400` 존재하지 않는 제품 / 이미 찜한 제품
- DELETE: `404` 찜 기록 없음

## 미구현 / TBD

| 항목 | 상태 |
|---|---|
| 추천 API (스코어링 엔진 호출) | 설계 확정, 미구현 |
| 챗봇 API (성분 Q&A RAG / 추천 요청) | 설계 확정, 미구현 |
| 목록 페이지네이션 | 미적용 (데이터 확대 시 도입) |
| 에러 응답 형식 통일 | 현재 FastAPI 기본 `{"detail": ...}` |
