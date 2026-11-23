# 피부 프로필 기반 제품 추천 (Rule-Based 엔진)
# 점수를 합산하지 않고 3단계를 분리함 (docs/prd.md 5번, docs/core-ingredient-rule.md 2-8)
#   1단계 게이트  : 통과/탈락만. 민감성 자극 성분, 금지 성분, 사용자가 적은 기피 성분 → 탈락
#                  알코올류(top_n 규칙)는 제품별 경계 앞이면 탈락, 경계 뒤(소량)면 탈락시키지 않고 경고만 함
#   2단계 정렬    : 게이트를 통과한 제품끼리 아래 순서로 정렬 (100점 환산 안 함)
#                  ① 주력 매칭 개수 → ② 매칭된 고민의 핵심(경계 앞) 계열 수 → ③ 함유(주력은 아님) 매칭 개수 → ④ 선호 성분
#                  주력 매칭 제품이 부족하면 함유 매칭 제품이 뒤를 채우고, 주력 근거가 없는 제품은 맨 뒤로 보냄
#   3단계 경고    : 배합 한도가 있는 성분, 민감성에게 소량 들어 있는 자극 성분은 표시만 함
#
# 이 파일의 함수들은 DB를 모름 (dict 목록을 받아 dict를 돌려줌) → DB 없이 테스트 가능
# LLM은 여기서 아무것도 판단하지 않음. 챗봇은 이 결과를 "설명"만 함
import csv
from pathlib import Path

from app.services.main_concerns import concern_profile, find_boundary, load_markers, load_tags

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_IRRITANT_PATH = DATA_DIR / "irritant_ingredients.csv"
DEFAULT_REGULATED_PATH = DATA_DIR / "regulated_ingredients.csv"

# 자극 성분 목록의 위치 규칙
RULE_TOP_N = "top_n"   # 제품별 경계 앞에 있을 때만 탈락 사유 (알코올류: 소량이면 경고만)
RULE_ANY = "any"       # 위치와 무관하게 탈락 사유 (향료, 알레르기 유발 성분, 에센셜 오일)

# 식약처 사용제한 원료정보의 REGULATE_TYPE 값
REGULATE_BANNED = "금지"
REGULATE_LIMITED = "한도"

# 탈락 사유 종류 (화면·챗봇에서 사유별로 문구를 다르게 보여주기 위함)
REASON_SENSITIVE = "sensitive"   # 민감성 피부 + 자극 유발 성분
REASON_BANNED = "banned"         # 사용 금지 성분
REASON_AVOIDED = "avoided"       # 사용자가 기피 성분으로 적은 성분

# 경고 종류
WARNING_LIMIT = "limit"                  # 배합 한도 성분
WARNING_TRACE_IRRITANT = "trace_irritant"  # 민감성에게 소량 들어 있는 자극 성분

# 고민 매칭 종류
MATCH_MAIN = "main"            # 제품의 주력 고민과 겹침
MATCH_CONTAINED = "contained"  # 주력은 아니지만 그 고민의 성분이 들어 있음
MATCH_NONE = "none"


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def load_irritants(path: Path = DEFAULT_IRRITANT_PATH) -> list[dict]:
    """자극 유발 성분 목록 [{ingredient_name, position_rule, reason, basis}]"""
    entries = _read_csv(path)
    for e in entries:
        if e["position_rule"] not in (RULE_TOP_N, RULE_ANY):
            raise ValueError(f"position_rule 값 오류: {e}")
    return entries


def load_regulated(path: Path = DEFAULT_REGULATED_PATH) -> list[dict]:
    """식약처 사용제한 원료 [{ingredient_name, regulate_type, limit_cond, source}] (파일이 없으면 빈 목록)"""
    return _read_csv(path)


def load_concern_tables() -> tuple[dict, list[str]]:
    """성분 태그표와 마커 목록. 파일이 없으면 빈 값 (정렬의 ②③ 기준 없이 주력 매칭 개수로만 정렬됨)"""
    try:
        return load_tags(), load_markers()
    except FileNotFoundError:
        return {}, []


def split_ingredient_text(text: str | None) -> list[str]:
    """프로필의 자유 텍스트(콤마 구분) → 성분명 목록. 공백은 성분명 비교에 쓰지 않으므로 제거"""
    return [t.replace(" ", "") for t in (text or "").split(",") if t.strip()]


# 이름은 겹치지만 다른 물질이라 같은 단어로 거르면 안 되는 경우 (키워드 → 제외할 성분명 조각)
# 예: "에탄올"을 피하려는 사람에게 방부제 "페녹시에탄올"까지 탈락시키면 안 됨
KEYWORD_NOT_MATCH = {"에탄올": ["페녹시에탄올"]}


def _matches_keyword(ingredient_name: str, keyword: str) -> bool:
    # 사용자가 적은 단어가 성분명에 포함되면 일치로 봄 (예: "알코올" → "변성알코올")
    # 기피 성분은 놓치는 것보다 넓게 거르는 편이 안전하다고 판단. 대신 어떤 성분이 걸렸는지 항상 함께 보여줌
    name = ingredient_name.replace(" ", "")
    for other in KEYWORD_NOT_MATCH.get(keyword, []):
        name = name.replace(other, "")
    return keyword in name


def check_gates(
    product: dict,
    profile: dict,
    irritants: list[dict],
    regulated: list[dict],
    markers: list[str] | None = None,
) -> list[dict]:
    """1단계 게이트. 탈락 사유 목록을 반환 (빈 목록이면 통과)
    사유: [{type, ingredient, detail}]"""
    reasons = []
    position_of = {i["name"]: i["position"] for i in product["ingredients"]}
    boundary, _ = find_boundary(product["ingredients"], markers or [])

    if profile.get("is_sensitive"):
        for irr in irritants:
            pos = position_of.get(irr["ingredient_name"])
            if pos is None:
                continue
            if irr["position_rule"] == RULE_TOP_N and pos > boundary:
                continue  # 소량이 확실한 알코올류는 탈락시키지 않고 경고로만 알림 (find_trace_warnings)
            reasons.append({"type": REASON_SENSITIVE, "ingredient": irr["ingredient_name"], "detail": irr["reason"]})

    for reg in regulated:
        if reg["regulate_type"] == REGULATE_BANNED and reg["ingredient_name"] in position_of:
            reasons.append({"type": REASON_BANNED, "ingredient": reg["ingredient_name"], "detail": "사용 금지 원료"})

    for keyword in split_ingredient_text(profile.get("avoided_ingredients")):
        for name in position_of:
            if _matches_keyword(name, keyword):
                reasons.append({"type": REASON_AVOIDED, "ingredient": name, "detail": f"기피 성분 '{keyword}'"})

    return reasons


def find_warnings(product: dict, regulated: list[dict]) -> list[dict]:
    """3단계 경고. 배합 한도가 있는 성분 [{ingredient, limit_cond, kind}]"""
    names = {i["name"] for i in product["ingredients"]}
    return [
        {"ingredient": reg["ingredient_name"], "limit_cond": reg.get("limit_cond") or "", "kind": WARNING_LIMIT}
        for reg in regulated
        if reg["regulate_type"] == REGULATE_LIMITED and reg["ingredient_name"] in names
    ]


def find_trace_warnings(
    product: dict, profile: dict, irritants: list[dict], markers: list[str] | None = None
) -> list[dict]:
    """민감성 사용자에게 소량 들어 있는(경계 뒤) 알코올류 같은 자극 성분 경고 [{ingredient, limit_cond, kind}]"""
    if not profile.get("is_sensitive"):
        return []
    position_of = {i["name"]: i["position"] for i in product["ingredients"]}
    boundary, _ = find_boundary(product["ingredients"], markers or [])
    return [
        {
            "ingredient": irr["ingredient_name"],
            "limit_cond": f"소량 함유 (민감성 피부 주의: {irr['reason']})",
            "kind": WARNING_TRACE_IRRITANT,
        }
        for irr in irritants
        if irr["position_rule"] == RULE_TOP_N and position_of.get(irr["ingredient_name"], 0) > boundary
    ]


def recommend(
    profile: dict,
    products: list[dict],
    irritants: list[dict],
    regulated: list[dict],
    include_unverified: bool = False,
    tags: dict | None = None,
    markers: list[str] | None = None,
) -> dict:
    """추천 실행
    profile : {is_sensitive, concerns:[...], avoided_ingredients:str, preferred_ingredients:str}
    products: [{id, product_name, brand, category, main_concerns:[...], is_concerns_verified,
                ingredients:[{name, position}]}]
    tags, markers: 성분 태그표와 마커 목록 (main_concerns.load_tags / load_markers). 없으면 주력 매칭 개수로만 정렬
    반환    : {"recommended": [...], "excluded": [...], "skipped_unverified": int}
      recommended: 위 정렬 순서대로. 주력 매칭 → 함유 매칭 → 매칭 없음 → 주력 근거 부족 순으로 자연스럽게 정렬됨
      excluded   : 게이트 탈락 제품과 사유 (탈락도 근거를 보여주기 위해 버리지 않음)
    """
    tags, markers = tags or {}, markers or []
    user_concerns = list(dict.fromkeys(profile.get("concerns") or []))
    preferred = split_ingredient_text(profile.get("preferred_ingredients"))

    recommended, excluded, skipped = [], [], 0
    for p in products:
        # 검수 전 주력 고민은 기본적으로 쓰지 않음 (검수 안 된 근거로 추천하지 않기 위함)
        if not p.get("is_concerns_verified") and not include_unverified:
            skipped += 1
            continue

        main_concerns = p.get("main_concerns") or []
        summary = {
            "id": p["id"],
            "product_name": p["product_name"],
            "brand": p.get("brand"),
            "category": p.get("category"),
            "main_concerns": main_concerns,
            "is_concerns_verified": bool(p.get("is_concerns_verified")),
        }

        reasons = check_gates(p, profile, irritants, regulated, markers)
        if reasons:
            excluded.append({**summary, "reasons": reasons})
            continue

        profile_info = concern_profile(p["ingredients"], tags, markers) if tags else {"core": {}, "contained": []}
        matched = [c for c in user_concerns if c in main_concerns]
        # 주력은 아니지만 그 고민의 성분이 들어 있는 경우 (주력 매칭 제품이 부족할 때 뒤를 채움)
        contained_matched = [c for c in user_concerns if c not in main_concerns and c in profile_info["contained"]]
        names = [i["name"] for i in p["ingredients"]]
        preferred_hits = sorted({n for n in names for k in preferred if _matches_keyword(n, k)})

        if matched:
            match_type = MATCH_MAIN
        elif contained_matched:
            match_type = MATCH_CONTAINED
        else:
            match_type = MATCH_NONE

        recommended.append({
            **summary,
            "matched_concerns": matched,
            "match_count": len(matched),
            "total_concerns": len(user_concerns),
            "match_type": match_type,
            "contained_matched": contained_matched,
            # 주력 근거가 없다고 검수된 제품 (카드에 "주력 근거 부족"으로 표시하고 순위는 맨 뒤)
            "main_basis_insufficient": bool(p.get("is_concerns_verified")) and not main_concerns,
            "preferred_hits": preferred_hits,
            "warnings": find_warnings(p, regulated) + find_trace_warnings(p, profile, irritants, markers),
            # 정렬 보조값 (개수일 뿐 점수 합산이 아님): 매칭된 고민의 경계 앞 계열(성분) 수
            "_core_count": sum(profile_info["core"].get(c, 0) for c in matched),
        })

    recommended.sort(key=lambda r: (
        r["main_basis_insufficient"],
        -r["match_count"],
        -r["_core_count"],
        -len(r["contained_matched"]),
        -len(r["preferred_hits"]),
        r["id"],
    ))
    for r in recommended:
        del r["_core_count"]
    return {"recommended": recommended, "excluded": excluded, "skipped_unverified": skipped}
