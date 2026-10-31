# 피부 프로필 기반 제품 추천 (Rule-Based 스코어링 엔진)
# 점수를 합산하지 않고 3단계를 분리함 (docs/prd.md 5번)
#   1단계 게이트  : 통과/탈락만. 민감성 자극 성분, 금지 성분, 사용자가 적은 기피 성분 → 탈락
#   2단계 가산점  : 게이트를 통과한 제품끼리, 사용자 고민 ∩ 제품 주력 고민 "개수"로 정렬 (100점 환산 안 함)
#   3단계 경고    : 배합 한도가 있는 성분은 표시만 함 (함량 정보가 없어 초과 여부를 판정할 수 없으므로 게이트 아님)
#
# 이 파일의 함수들은 DB를 모름 (dict 목록을 받아 dict를 돌려줌) → DB 없이 테스트 가능
# LLM은 여기서 아무것도 판단하지 않음. 챗봇은 이 결과를 "설명"만 함
import csv
from pathlib import Path

from app.services.concern_tagger import TOP_N, RULE_TOP_N, RULE_ANY

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DEFAULT_IRRITANT_PATH = DATA_DIR / "irritant_ingredients.csv"
DEFAULT_REGULATED_PATH = DATA_DIR / "regulated_ingredients.csv"

# 식약처 사용제한 원료정보의 REGULATE_TYPE 값
REGULATE_BANNED = "금지"
REGULATE_LIMITED = "한도"

# 탈락 사유 종류 (화면·챗봇에서 사유별로 문구를 다르게 보여주기 위함)
REASON_SENSITIVE = "sensitive"   # 민감성 피부 + 자극 유발 성분
REASON_BANNED = "banned"         # 사용 금지 성분
REASON_AVOIDED = "avoided"       # 사용자가 기피 성분으로 적은 성분


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


def split_ingredient_text(text: str | None) -> list[str]:
    """프로필의 자유 텍스트(콤마 구분) → 성분명 목록. 공백은 성분명 비교에 쓰지 않으므로 제거"""
    return [t.replace(" ", "") for t in (text or "").split(",") if t.strip()]


def _matches_keyword(ingredient_name: str, keyword: str) -> bool:
    # 사용자가 적은 단어가 성분명에 포함되면 일치로 봄 (예: "알코올" → "변성알코올")
    # 기피 성분은 놓치는 것보다 넓게 거르는 편이 안전하다고 판단. 대신 어떤 성분이 걸렸는지 항상 함께 보여줌
    return keyword in ingredient_name.replace(" ", "")


def check_gates(
    product: dict,
    profile: dict,
    irritants: list[dict],
    regulated: list[dict],
    top_n: int = TOP_N,
) -> list[dict]:
    """1단계 게이트. 탈락 사유 목록을 반환 (빈 목록이면 통과)
    사유: [{type, ingredient, detail}]"""
    reasons = []
    position_of = {i["name"]: i["position"] for i in product["ingredients"]}

    if profile.get("is_sensitive"):
        for irr in irritants:
            pos = position_of.get(irr["ingredient_name"])
            if pos is None:
                continue
            if irr["position_rule"] == RULE_TOP_N and pos > top_n:
                continue
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
    """3단계 경고. 배합 한도가 있는 성분 [{ingredient, limit_cond}]"""
    names = {i["name"] for i in product["ingredients"]}
    return [
        {"ingredient": reg["ingredient_name"], "limit_cond": reg.get("limit_cond") or ""}
        for reg in regulated
        if reg["regulate_type"] == REGULATE_LIMITED and reg["ingredient_name"] in names
    ]


def recommend(
    profile: dict,
    products: list[dict],
    irritants: list[dict],
    regulated: list[dict],
    include_unverified: bool = False,
) -> dict:
    """추천 실행
    profile : {is_sensitive, concerns:[...], avoided_ingredients:str, preferred_ingredients:str}
    products: [{id, product_name, brand, category, main_concerns:[...], is_concerns_verified,
                ingredients:[{name, position}]}]
    반환    : {"recommended": [...], "excluded": [...], "skipped_unverified": int}
      recommended: 고민 매칭 개수 많은 순. 동점이면 선호 성분 포함 개수 → 제품 id 순
      excluded   : 게이트 탈락 제품과 사유 (탈락도 근거를 보여주기 위해 버리지 않음)
    """
    user_concerns = list(dict.fromkeys(profile.get("concerns") or []))
    preferred = split_ingredient_text(profile.get("preferred_ingredients"))

    recommended, excluded, skipped = [], [], 0
    for p in products:
        # 검수 전 주력 고민은 기본적으로 쓰지 않음 (검수 안 된 근거로 추천하지 않기 위함)
        if not p.get("is_concerns_verified") and not include_unverified:
            skipped += 1
            continue

        summary = {
            "id": p["id"],
            "product_name": p["product_name"],
            "brand": p.get("brand"),
            "category": p.get("category"),
            "main_concerns": p.get("main_concerns") or [],
            "is_concerns_verified": bool(p.get("is_concerns_verified")),
        }

        reasons = check_gates(p, profile, irritants, regulated)
        if reasons:
            excluded.append({**summary, "reasons": reasons})
            continue

        matched = [c for c in user_concerns if c in summary["main_concerns"]]
        names = [i["name"] for i in p["ingredients"]]
        preferred_hits = sorted({n for n in names for k in preferred if _matches_keyword(n, k)})

        recommended.append({
            **summary,
            "matched_concerns": matched,
            "match_count": len(matched),
            "total_concerns": len(user_concerns),
            "preferred_hits": preferred_hits,
            "warnings": find_warnings(p, regulated),
        })

    # 정렬은 "매칭 개수"가 먼저. 선호 성분은 매칭 개수가 같을 때 순서만 정함 (점수에 더하지 않음)
    recommended.sort(key=lambda r: (-r["match_count"], -len(r["preferred_hits"]), r["id"]))
    return {"recommended": recommended, "excluded": excluded, "skipped_unverified": skipped}
